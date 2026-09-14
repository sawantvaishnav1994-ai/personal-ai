from types import SimpleNamespace

from desktop.cross_operator import CrossOperatorCoordinator,RecoveryStep
from desktop.operator_recovery import OperatorRecoveryStore
from desktop.operator_transactions import OperatorBinding,OperatorTransactionStore


def setup(tmp_path,*,browser=None,desktop=None,verify=None,authority=None,stop=None):
    txs=OperatorTransactionStore(tmp_path/'tx.sqlite3');binding=OperatorBinding('owner','device','session',0)
    txs.propose('tx',binding,goal='cross operator',action_plan={'steps':[{'sequence':0,'kind':'cross'}]})
    store=OperatorRecoveryStore(tmp_path/'recovery.sqlite3',txs,emergency_stop=stop)
    op=CrossOperatorCoordinator(store,binding,browser_execute=browser,desktop_execute=desktop,verify=verify,authority=authority,emergency_stop=stop)
    return store,op


def step(operator='file',operation='copy',**kw):
    return RecoveryStep(0,operator,operation,'target','idem','postcondition',kw or {'path':'x'},consequential=kw.pop('consequential',False) if 'consequential' in kw else False,idempotent=kw.pop('idempotent',True) if 'idempotent' in kw else True)


def test_cross_operator_uses_existing_browser_surface(tmp_path):
    calls=[];store,op=setup(tmp_path,browser=lambda s:(calls.append(s),{'status':'verified'})[1])
    out=op.run_step('tx',step('browser','download'))
    assert out['status']=='verified_success' and len(calls)==1


def test_cross_operator_uses_existing_desktop_surface_for_file(tmp_path):
    calls=[];store,op=setup(tmp_path,desktop=lambda s:(calls.append(s),{'status':'verified'})[1])
    out=op.run_step('tx',step('file','copy'))
    assert out['status']=='verified_success' and calls[0].operator=='file'


def test_unapproved_operator_is_not_created_as_escape_hatch(tmp_path):
    store,op=setup(tmp_path)
    out=op.run_step('tx',step('shell','command'))
    assert out['status']=='recovery_review_required'


def test_policy_authority_blocks_before_dispatch(tmp_path):
    called=[];store,op=setup(tmp_path,desktop=lambda s:called.append(s),authority=lambda s,p:False)
    out=op.run_step('tx',step())
    assert out['status']=='blocked_before_dispatch' and called==[]


def test_handler_return_without_verification_becomes_unknown(tmp_path):
    store,op=setup(tmp_path,desktop=lambda s:{'status':'handler_returned'})
    out=op.run_step('tx',RecoveryStep(0,'file','copy','target','idem','checksum',{},consequential=True,idempotent=True))
    assert out['status']=='unknown_outcome' and store.snapshot('tx')['state']=='recovery_review_required'


def test_crash_after_dispatch_enters_recovery_review(tmp_path):
    def crash(step):raise RuntimeError('network lost')
    store,op=setup(tmp_path,browser=crash)
    out=op.run_step('tx',RecoveryStep(0,'browser','upload','origin','idem','resource exists',{},consequential=True))
    assert out['status']=='recovery_review_required' and store.snapshot('tx')['state']=='recovery_review_required'


def test_duplicate_run_does_not_duplicate_side_effect(tmp_path):
    calls=[];store,op=setup(tmp_path,desktop=lambda s:(calls.append(1),{'status':'verified'})[1])
    first=op.run_step('tx',step());second=op.run_step('tx',step())
    assert first['status']=='verified_success' and second['status']=='already_recorded' and len(calls)==1


def test_retry_requires_verified_no_effect(tmp_path):
    store,op=setup(tmp_path,desktop=lambda s:{'status':'verification_failed'})
    original=RecoveryStep(0,'file','copy','target','idem','post',{},consequential=True,idempotent=True)
    out=op.run_step('tx',original)
    retry=op.retry_step('tx',out['dispatch_id'],original)
    assert retry['status']=='retry_not_safe'


def test_external_send_never_auto_retries_even_if_no_effect(tmp_path):
    store,op=setup(tmp_path,browser=lambda s:{'status':'verified_no_effect'})
    s=RecoveryStep(0,'browser','message_send','origin','idem','message sent',{},consequential=True,idempotent=True)
    out=op.run_step('tx',s);retry=op.retry_step('tx',out['dispatch_id'],s)
    assert retry['status']=='retry_not_safe'


def test_emergency_stop_blocks_cross_operator_dispatch(tmp_path):
    flag={'on':True};calls=[];store,op=setup(tmp_path,desktop=lambda s:calls.append(1),stop=lambda:flag['on'])
    store.ensure_transaction('tx',op.binding)
    out=op.run_step('tx',step())
    assert out['status']=='emergency_stop_active' and not calls


def test_crash_recovery_collects_read_only_evidence_but_does_not_resume(tmp_path):
    def crash(step):raise RuntimeError('crash')
    store,op=setup(tmp_path,desktop=crash)
    out=op.run_step('tx',RecoveryStep(0,'file','move','target','idem','moved',{},consequential=True))
    recovered=op.recover_after_crash('tx',read_only_verify=lambda d:{'destination_exists':True,'source_exists':False})
    assert out['status']=='recovery_review_required' and recovered['status']=='recovery_review_required'


def test_compensation_requires_separate_authority(tmp_path):
    authority_calls=[]
    store,op=setup(tmp_path,desktop=lambda s:{'status':'verified'},authority=lambda s,p:(authority_calls.append(p),p!='compensation')[1])
    comp=store.plan_compensation('tx',original_action_id='tx:0',category='compensation_available',operation_class='delete',plan={'target_digest':'x'})
    out=op.compensation('tx',comp['compensation_id'],RecoveryStep(1,'file','delete','x','comp','removed',{},consequential=True))
    assert out['status']=='blocked_before_dispatch' and 'compensation' in authority_calls
