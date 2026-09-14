import time
import pytest

from browser.safe_operator import BrowserSafetyError, SafeBrowserOperator
from browser.targeting import TargetResolutionError, resolve_target


def element(target='t1', *, x=10, y=20, w=100, h=30, actionable=True, sensitive=False, label='Continue', role='button', tag='button', field_type=''):
    return {'target_id':target,'geometry_digest':f'g-{target}-{x}-{y}','path':f'#{target}','tag':tag,'role':role,'type':field_type,'name':'','label':label,'text':label,'placeholder':'','sensitive':sensitive,'actionable':actionable,'visible':actionable,'topmost':actionable,'disabled':False,'box':{'x':x,'y':y,'width':w,'height':h}}


def observation(*elements, origin='https://example.com', tab='tab-1', context='browser-1', tab_count=1, frame='frames-1'):
    return {'captured_at':time.time(),'browser_context_id':context,'tab_id':tab,'tab_index':0,'tab_count':tab_count,'origin':origin,'normalized_url':origin+'/page','domain':'example.com','visible_text':'safe text','accessibility':'- button "Continue"','accessibility_available':True,'frame_origins_digest':frame,'actionable_digest':'a','active_target_id':'','elements':list(elements),'sensitive_regions':[]}


def with_digest(obs):
    from browser.safe_operator import _digest
    from browser.observation import safe_browser_evidence
    row=dict(obs);row['observation_digest']=_digest(safe_browser_evidence(row));return row


def test_dom_target_resolves_exact_actionable_element():
    out=resolve_target(with_digest(observation(element())),{'target_id':'t1'});assert out.target_id=='t1' and out.method=='dom'

def test_dom_target_rejects_hidden_covered_or_disabled():
    with pytest.raises(TargetResolutionError):resolve_target(with_digest(observation(element(actionable=False))),{'target_id':'t1'})

def test_accessibility_fallback_requires_unique_element():
    out=resolve_target(with_digest(observation(element(label='Save',role='button'))),{'accessibility_target':{'role':'button','name':'Save'}});assert out.method=='accessibility'

def test_accessibility_fallback_rejects_same_label_replacement_ambiguity():
    obs=with_digest(observation(element('a',label='Save'),element('b',x=200,label='Save')))
    with pytest.raises(TargetResolutionError):resolve_target(obs,{'accessibility_target':{'name':'Save'}})

def test_visual_fallback_requires_sanitized_same_observation():
    obs=with_digest(observation(element()))
    with pytest.raises(TargetResolutionError):resolve_target(obs,{'visual_target':{'target_id':'t1','redaction_status':'raw','observation_digest':obs['observation_digest']}})
    out=resolve_target(obs,{'visual_target':{'target_id':'t1','redaction_status':'sanitized','observation_digest':obs['observation_digest'],'box':element()['box']}});assert out.method=='verified_visual'

def test_visual_fallback_rejects_changed_box():
    obs=with_digest(observation(element()))
    with pytest.raises(TargetResolutionError):resolve_target(obs,{'visual_target':{'target_id':'t1','redaction_status':'sanitized','observation_digest':obs['observation_digest'],'box':{'x':0,'y':0,'width':1,'height':1}}})

def test_coordinate_fallback_is_observation_bound_and_maps_to_one_element():
    obs=with_digest(observation(element()))
    with pytest.raises(TargetResolutionError):resolve_target(obs,{'coordinate_target':{'x':20,'y':25,'observation_digest':'stale'}})
    out=resolve_target(obs,{'coordinate_target':{'x':20,'y':25,'observation_digest':obs['observation_digest']}});assert out.method=='restricted_coordinate'

def test_coordinate_fallback_rejects_overlay_ambiguity():
    obs=with_digest(observation(element('a'),element('b',x=5,y=15,w=100,h=50)))
    with pytest.raises(TargetResolutionError):resolve_target(obs,{'coordinate_target':{'x':20,'y':25,'observation_digest':obs['observation_digest']}})


class PermitRegistry:
    def __init__(self):self.emergency_stop=False;self.events=[]
    def issue_tool_policy_permit(self,p):self.events.append('permit');return {'id':'p'}
    def consume_tool_policy_permit(self,p,permit):self.events.append('consume');return True

class Adapter:
    def __init__(self,obs):self.obs=dict(obs);self.clicked=0;self.filled=[];self.nav=[]
    def observe(self):self.events_append('observe');return dict(self.obs)
    def events_append(self,x):pass
    def application_identity(self):return {'canonical_path':'/browser','sha256':'a'*64,'publisher':'Test','version':'1'}
    def navigate(self,url,timeout_ms):self.nav.append(url);origin=url.split('/',3)[:3];self.obs['origin']='/'.join(origin);self.obs['normalized_url']=url;return {'url':url}
    def go_back(self,t):return {'url':self.obs['normalized_url']}
    def go_forward(self,t):return {'url':self.obs['normalized_url']}
    def refresh(self,t):return {'url':self.obs['normalized_url']}
    def create_tab(self,url=None,timeout_ms=1):self.obs['tab_id']='tab-2';self.obs['tab_count']=2;return {'url':url or 'about:blank'}
    def select_tab(self,tab):self.obs['tab_id']=tab;return {'url':self.obs['normalized_url']}
    def close_tab(self):self.obs['tab_id']='tab-0';self.obs['tab_count']=1;return {'url':self.obs['normalized_url']}
    def click(self,path):self.clicked+=1
    def fill(self,path,value):self.filled.append((path,value));self.obs['active_target_id']='t1'
    def select_option(self,path,value):return [value]
    def check(self,path,checked):return None
    def scroll(self,dx,dy):return None
    def wait_for(self,path,state,timeout):return None
    def set_input_files(self,path,file_path):return None


def configured_operator(obs):
    reg=PermitRegistry();adapter=Adapter(obs);op=SafeBrowserOperator(reg,adapter)
    original=op._fresh_target
    def issue_first(p):p['_permit']=reg.issue_tool_policy_permit(p);return original(p)
    def consume(p):return reg.consume_tool_policy_permit(p,p.pop('_permit'))
    op._fresh_target=issue_first;op._consume_permit=consume
    return op,adapter,reg


def prepared(op,action='click',params=None):
    row=op.prepare(action,params or {'target_id':'t1'});row['_policy_tool_name']='x';return row


def test_permit_is_issued_before_second_fresh_verification_and_consumed_before_click():
    obs=with_digest(observation(element()));op,adapter,reg=configured_operator(obs);row=prepared(op)
    op.execute('click',row);assert reg.events==['permit','consume'] and adapter.clicked==1

def test_changed_element_geometry_is_rejected_before_dispatch():
    obs=with_digest(observation(element()));op,adapter,reg=configured_operator(obs);row=prepared(op)
    adapter.obs=with_digest(observation(element(x=80)))
    with pytest.raises(BrowserSafetyError,match='changed'):op.execute('click',row)
    assert adapter.clicked==0 and reg.events==['permit']

def test_detached_element_is_rejected_before_dispatch():
    obs=with_digest(observation(element()));op,adapter,reg=configured_operator(obs);row=prepared(op)
    adapter.obs=with_digest(observation())
    with pytest.raises(BrowserSafetyError):op.execute('click',row)
    assert adapter.clicked==0

def test_tab_substitution_is_rejected_before_dispatch():
    obs=with_digest(observation(element()));op,adapter,reg=configured_operator(obs);row=prepared(op)
    adapter.obs=with_digest(observation(element(),tab='attacker-tab'))
    with pytest.raises(BrowserSafetyError,match='tab'):op.execute('click',row)

def test_origin_change_is_rejected_before_element_dispatch():
    obs=with_digest(observation(element()));op,adapter,reg=configured_operator(obs);row=prepared(op)
    adapter.obs=with_digest(observation(element(),origin='https://evil.test'))
    with pytest.raises(BrowserSafetyError,match='origin'):op.execute('click',row)

def test_emergency_stop_blocks_dispatch():
    obs=with_digest(observation(element()));op,adapter,reg=configured_operator(obs);row=prepared(op);reg.emergency_stop=True
    with pytest.raises(BrowserSafetyError):op.execute('click',row)
    assert adapter.clicked==0

def test_credential_bearing_url_is_rejected_in_prepare():
    op,_,_=configured_operator(with_digest(observation()))
    with pytest.raises(Exception):op.prepare('navigate',{'url':'https://user:pass@example.com/path'})

def test_private_ip_and_localhost_are_default_denied():
    op,_,_=configured_operator(with_digest(observation()))
    for url in ('http://127.0.0.1/','http://192.168.1.10/'):
        with pytest.raises(Exception):op.prepare('navigate',{'url':url})

def test_https_downgrade_is_rejected():
    obs=with_digest(observation(origin='https://example.com'));op,adapter,reg=configured_operator(obs);row=op.prepare('navigate',{'url':'http://example.com'});row['_policy_tool_name']='x'
    with pytest.raises(BrowserSafetyError,match='downgrade'):op.execute('navigate',row)

def test_cross_origin_redirect_is_rejected_after_navigation():
    class Redirect(Adapter):
        def navigate(self,url,timeout_ms):self.obs['origin']='https://evil.test';self.obs['normalized_url']='https://evil.test/landing';return {'url':self.obs['normalized_url']}
    obs=with_digest(observation());reg=PermitRegistry();adapter=Redirect(obs);op=SafeBrowserOperator(reg,adapter);orig=op._fresh_target;op._fresh_target=lambda p:(p.__setitem__('_permit',reg.issue_tool_policy_permit(p)) or orig(p));op._consume_permit=lambda p:reg.consume_tool_policy_permit(p,p.pop('_permit'))
    row=op.prepare('navigate',{'url':'https://example.com'});row['_policy_tool_name']='x'
    with pytest.raises(BrowserSafetyError,match='unapproved'):op.execute('navigate',row)

def test_password_otp_and_payment_fields_are_never_actionable():
    for kind in ('password','one-time-code','cc-number'):
        obs=with_digest(observation(element(tag='input',field_type=kind,sensitive=True,actionable=False)))
        op,_,_=configured_operator(obs)
        with pytest.raises(BrowserSafetyError):op.prepare('type',{'target_id':'t1','text':'secret'})
