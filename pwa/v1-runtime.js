(()=>{
  'use strict';
  const PENDING_KEY='personal-ai:v1:pending-turn';
  const uuid=()=>{
    if(globalThis.crypto&&typeof crypto.randomUUID==='function')return crypto.randomUUID();
    const b=new Uint8Array(16);crypto.getRandomValues(b);b[6]=(b[6]&15)|64;b[8]=(b[8]&63)|128;
    const h=[...b].map(x=>x.toString(16).padStart(2,'0')).join('');
    return `${h.slice(0,8)}-${h.slice(8,12)}-${h.slice(12,16)}-${h.slice(16,20)}-${h.slice(20)}`;
  };
  const loadPending=()=>{try{return JSON.parse(sessionStorage.getItem(PENDING_KEY)||'null')}catch{return null}};
  const savePending=value=>{try{sessionStorage.setItem(PENDING_KEY,JSON.stringify(value))}catch{}};
  const clearPending=id=>{const p=loadPending();if(!p||p.request_id===id)try{sessionStorage.removeItem(PENDING_KEY)}catch{}};
  const terminalHttp=status=>status>=400&&status<500&&![408,409,425,429].includes(status);

  // Replace only the transport function. CanonicalTurnRuntime remains replay
  // authority; this adapter merely preserves the same client UUID across retry.
  globalThis.sendTurn=async function v1SendTurn(text){
    const clean=String(text||'').trim();if(!clean||turnInFlight)return;
    let pending=loadPending();
    const samePending=pending&&pending.text===clean&&String(pending.conversation_id||'')===String(currentConversationId||'');
    if(!samePending){pending={request_id:uuid(),text:clean,conversation_id:currentConversationId||null,created_at:Date.now()};savePending(pending)}
    stopRecognition();turnInFlight=true;$('voiceAlert').textContent='';$('transcript').textContent=clean;$('reply').textContent='';
    if(!samePending)appendMessage('user_message',clean);
    setState('understanding');
    try{
      setState('thinking');
      let result,lastError;
      for(let attempt=0;attempt<2;attempt++){
        try{
          result=await api('/voice/turn',{method:'POST',body:JSON.stringify({request_id:pending.request_id,transcript:clean,conversation_id:currentConversationId})});
          lastError=null;break;
        }catch(error){lastError=error;if(terminalHttp(error.status))break;await new Promise(resolve=>setTimeout(resolve,180*(attempt+1)))}
      }
      if(lastError)throw lastError;
      clearPending(pending.request_id);
      currentConversationId=result.conversation_id||currentConversationId;
      if(result.conversation_title){currentConversationTitle=result.conversation_title;$('conversationTitle').textContent=currentConversationTitle}
      $('reply').textContent=result.reply;turnInFlight=false;
      if(result.status==='approval_required')showApproval(result.approval);else appendMessage('assistant_message',result.reply);
      speakReply(result.reply);refreshConversationList($('conversationSearch').value).catch(()=>{});
    }catch(error){
      turnInFlight=false;
      if(terminalHttp(error.status))clearPending(pending.request_id);
      if(error.message!=='turn_cancelled'){$('voiceAlert').textContent=error.message;appendMessage('approval_rejected',error.message);setState('error',error.message)}
      if(handsFree)scheduleListening(500);
    }
  };
})();
