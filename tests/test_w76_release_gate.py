from pathlib import Path
import re


def test_tmp_should_not_create_absent_from_worktree():
    assert not Path('tmp_should_not_create').exists()


def test_w76_does_not_add_unrestricted_execution_capabilities():
    files=['desktop/verification.py','desktop/operator_recovery.py','desktop/cross_operator.py','server/recovery_api.py']
    text='\n'.join(Path(p).read_text(encoding='utf-8') for p in files).lower()
    forbidden=('shell=true','cmd.exe','powershell','subprocess.popen','os.system(','reg.exe','sc.exe','netsh','shutdown.exe','keyboard.hook','keylog','create_remote_thread')
    assert not any(token in text for token in forbidden)


def test_w76_changed_surface_has_no_secret_patterns():
    files=['desktop/verification.py','desktop/operator_recovery.py','desktop/cross_operator.py','server/recovery_api.py']
    text='\n'.join(Path(p).read_text(encoding='utf-8') for p in files)
    patterns=(r'\bsk-[A-Za-z0-9_-]{16,}\b',r'\bAKIA[0-9A-Z]{16}\b',r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',r'(?i)(?:api[_-]?key|access[_-]?token|client[_-]?secret)\s*=\s*["\'][^"\']{12,}["\']')
    assert not any(re.search(p,text) for p in patterns)


def test_w76_uses_w71_transaction_authority_not_parallel_transaction_creation():
    source=Path('desktop/operator_recovery.py').read_text(encoding='utf-8')
    assert 'OperatorTransactionStore' in source and '.transactions.assert_binding' in source
    assert 'CREATE TABLE IF NOT EXISTS operator_transactions' not in source


def test_recovery_api_uses_safe_http_states_not_raw_500_contract():
    source=Path('server/recovery_api.py').read_text(encoding='utf-8')
    for token in ('authentication_required','reauthentication_required','recovery_not_found','recovery_binding_mismatch','verification_pending'):
        assert token in source
    assert 'status_code=500' not in source


def test_w76_does_not_modify_home_or_ai_core_by_design():
    # Release diff review verifies this again at exact-head; this guard catches accidental imports/coupling.
    text=(Path('desktop/operator_recovery.py').read_text()+Path('desktop/cross_operator.py').read_text()+Path('server/recovery_api.py').read_text()).lower()
    assert 'home v1' not in text and 'ai core' not in text
