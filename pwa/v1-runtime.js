(()=>{
  'use strict';
  const PENDING_KEY='personal-ai:v1:pending-turn';
  const MAX_PENDING_AGE_MS=15*60*1000;
  let canonicalSequence=-1;
  let applyingCanonicalState=false;
  let nextInputModality='text';
  let currentUiRequestId=null;
  let currentPlaybackRequestId=null;
  let playbackGeneration=0;
  let lastApprovalRequestId=null;

  const uuid=()=>{
    const c=globalThis.crypto;
    if(c&&typeof c.randomUUID==='function')return c.randomUUID();
    if(!c||typeof c.getRandomValues!=='function')throw new Error('Secure request identity is unavailable in this browser context.');
    const b=new Uint8Array(16);c.getRandomValues(b);b[6]=(b[6]&15)|64;b[8]=(b[8]&63)|128;
    const h=[...b].map(x=>x.toString(16).padStart(2,'0')).join('');
    return `${h.slice(0,8)}-${h.slice(8,12)}-${h.slice(12,16)}-${h.slice(16,20)}-${h.slice(20)}`;
  };
  const rawPending=()=>{try{return JSON.parse(sessionStorage.getItem(PENDING_KEY)||'null')}catch{return null}};
  const loadPending=()=>{const p=rawPending();if(!p)return null;if(!p.created_at||Date.now()-Number(p.created_at)>MAX_PENDING_AGE_MS){try{sessionStorage.removeItem(PENDING_KEY)}catch{};return null}return p};
  const savePending=value=>{try{sessionStorage.setItem(PENDING_KEY,JSON.stringify(value))}catch{}};
  const clearPending=id=>{const p=rawPending();if(!p||p.request_id===id)try{sessionStorage.removeItem(PENDING_KEY)}catch{}};
  const terminalHttp=status=>status>=400&&status<500&&![408,409,425,429].includes(status);

  const renderVoiceControls=()=>{
    try{
      $('micButton').classList.toggle('active',handsFree&&!speaking);
      $('micButton').classList.toggle('speaking',speaking);
      $('micButton').setAttribute('aria-label',speaking?'Interrupt and listen':(handsFree?'Stop hands-free conversation':'Start hands-free conversation'));
    }catch{}
  };

  // Legacy UI code can still request presentation changes, but it is no longer
  // allowed to invent semantic AI state from timers/fetch/mic callbacks. Only an
  // authenticated RuntimeStateAuthority snapshot may update the semantic label.
  const semanticRenderer=globalThis.setState;
  if(typeof semanticRenderer==='function'){
    globalThis.setState=function stage3StateRenderer(name,detail){
      renderVoiceControls();
      if(!applyingCanonicalState)return;
      return semanticRenderer(name,detail);
    };
  }

  const applyCanonicalState=snapshot=>{
    const sequence=Number(snapshot&&snapshot.sequence);
    if(!Number.isInteger(sequence)||sequence<=canonicalSequence)return false;
    canonicalSequence=sequence;
    const state=String(snapshot.state||'').toLowerCase().replaceAll('_','-');
    if(state&&typeof setState==='function'){
      applyingCanonicalState=true;
      try{setState(state,String(snapshot.reason||''))}finally{applyingCanonicalState=false}
    }
    return true;
  };
  const refreshCanonicalState=async()=>{try{const snapshot=await api('/runtime-state');applyCanonicalState(snapshot)}catch{/* network status is not semantic AI state */}};
  globalThis.personalAiApplyCanonicalState=applyCanonicalState;
  refreshCanonicalState();
  setInterval(refreshCanonicalState,750);

  const voiceClientEvent=(event,requestId,detail='')=>api('/voice/client-event',{
    method:'POST',
    body:JSON.stringify({event,request_id:requestId||null,detail:String(detail||'').slice(0,160)})
  }).catch(()=>{});

  // Tag actual browser recognition starts as factual listening observations and
  // mark only FINAL speech results as voice input. Interim transcripts remain UI
  // presentation and never create canonical turns.
  const legacyCreateRecognition=globalThis.createRecognition;
  if(typeof legacyCreateRecognition==='function'){
    globalThis.createRecognition=function stage3CreateRecognition(){
      const instance=legacyCreateRecognition();
      if(!instance)return instance;
      const onstart=instance.onstart;
      instance.onstart=function(event){
        if(onstart)onstart.call(this,event);
        voiceClientEvent('listening_started',currentUiRequestId);
      };
      const onresult=instance.onresult;
      instance.onresult=function(event){
        for(let i=event.resultIndex;i<event.results.length;i++){
          if(event.results[i].isFinal){nextInputModality='voice';break}
        }
        if(onresult)return onresult.call(this,event);
      };
      return instance;
    };
  }

  const stopPlayback=(notify=true)=>{
    const interrupted=currentPlaybackRequestId;
    playbackGeneration++;
    try{if(globalThis.speechSynthesis)globalThis.speechSynthesis.cancel()}catch{}
    try{speaking=false;currentUtterance=null}catch{}
    renderVoiceControls();
    if(notify&&interrupted)voiceClientEvent('playback_interrupted',interrupted);
    return interrupted;
  };

  function canonicalSpeakReply(text,requestId){
    const rid=requestId||lastApprovalRequestId||currentPlaybackRequestId||currentUiRequestId;
    lastApprovalRequestId=null;
    stopPlayback(false);
    currentPlaybackRequestId=rid||null;
    const generation=++playbackGeneration;
    if(!globalThis.speechSynthesis){
      voiceClientEvent('tts_error',rid,'speech_synthesis_unavailable');
      $('voiceAlert').textContent='Spoken replies are unavailable in this browser. The answer is shown on screen.';
      if(handsFree)scheduleListening(400);
      return;
    }
    stopRecognition();
    let attempt=0,finished=false;
    const stale=()=>generation!==playbackGeneration||currentPlaybackRequestId!==rid;
    const finish=()=>{
      if(finished||stale())return;
      finished=true;voiceClientEvent('tts_completed',rid);speaking=false;currentUtterance=null;renderVoiceControls();$('voiceAlert').textContent='';
      if(!pendingApproval&&handsFree&&preference('continuous_voice',true))scheduleListening(350);
      else if(!pendingApproval){handsFree=false;renderVoiceControls()}
    };
    const fail=detail=>{
      if(finished||stale())return;
      finished=true;voiceClientEvent('tts_error',rid,detail||'speech_synthesis_blocked');speaking=false;currentUtterance=null;renderVoiceControls();
      $('voiceAlert').textContent='The spoken reply could not play. The canonical text answer is still available.';
      if(handsFree&&!pendingApproval)scheduleListening(450);
    };
    const play=()=>{
      if(stale()||finished)return;
      attempt++;
      let started=false;
      const utterance=makeUtterance(text,{
        start:()=>{if(stale())return;started=true;speaking=true;renderVoiceControls();voiceClientEvent('tts_started',rid)},
        end:finish,
        error:event=>{
          if(stale()||finished)return;
          if(event&&event.error==='interrupted'){finish();return}
          if(attempt<2)setTimeout(play,80);else fail(event&&event.error);
        }
      });
      currentUtterance=utterance;
      globalThis.speechSynthesis.cancel();
      globalThis.speechSynthesis.resume();
      globalThis.speechSynthesis.speak(utterance);
      globalThis.speechSynthesis.resume();
      setTimeout(()=>{if(!started&&!finished&&!stale()){if(attempt<2)play();else fail('start_timeout')}},1600);
    };
    play();
  }
  globalThis.speakReply=canonicalSpeakReply;

  const legacyShowApproval=globalThis.showApproval;
  if(typeof legacyShowApproval==='function'){
    globalThis.showApproval=function stage3ShowApproval(approval){
      lastApprovalRequestId=(approval&&approval.request_id)||currentUiRequestId||null;
      return legacyShowApproval(approval);
    };
  }

  // Playback barge-in is not canonical operation cancellation. It only stops the
  // current TTS generation. A new intentional R2 gets its own request ID; tapping
  // during THINKING uses the explicit canonical cancellation endpoint instead.
  globalThis.interruptAndListen=async function stage3InterruptAndListen(){
    const requestId=currentPlaybackRequestId;
    const wasSpeaking=Boolean(speaking||(globalThis.speechSynthesis&&globalThis.speechSynthesis.speaking));
    stopPlayback(false);handsFree=true;renderVoiceControls();
    try{await api('/voice/barge',{method:'POST',body:JSON.stringify({speaking:wasSpeaking,request_id:requestId})})}catch{}
    scheduleListening(100);
  };

  const mic=$('micButton');
  if(mic){
    mic.onclick=async()=>{
      if(speaking||(globalThis.speechSynthesis&&globalThis.speechSynthesis.speaking)){await globalThis.interruptAndListen();return}
      if(turnInFlight&&currentUiRequestId){
        try{
          await api('/voice/operation/cancel',{method:'POST',body:JSON.stringify({request_id:currentUiRequestId})});
          $('voiceAlert').textContent='Cancelling the current operation safely…';
          handsFree=true;renderVoiceControls();
        }catch(error){$('voiceAlert').textContent=error.message}
        return;
      }
      if(handsFree){handsFree=false;stopRecognition();renderVoiceControls();return}
      handsFree=true;renderVoiceControls();
      try{await primeVoice();startListening()}catch(error){handsFree=false;renderVoiceControls();$('voiceAlert').textContent=error.message}
    };
  }

  // Replace only the logical-turn transport. CanonicalTurnRuntime remains replay
  // authority; this adapter preserves one UUID across retry/reload, carries the
  // real modality, and never invents semantic UNDERSTANDING/THINKING/ERROR state.
  globalThis.sendTurn=async function v1SendTurn(text){
    const clean=String(text||'').trim();if(!clean||turnInFlight)return;
    const candidateModality=nextInputModality==='voice'?'voice':'text';nextInputModality='text';
    let pending=loadPending();
    const samePending=pending&&pending.text===clean&&String(pending.conversation_id||'')===String(currentConversationId||'');
    if(!samePending){pending={request_id:uuid(),text:clean,conversation_id:currentConversationId||null,input_modality:candidateModality,created_at:Date.now()};savePending(pending)}
    else if(!pending.input_modality){pending.input_modality=candidateModality;savePending(pending)}
    currentUiRequestId=pending.request_id;lastApprovalRequestId=null;
    if(currentPlaybackRequestId&&currentPlaybackRequestId!==pending.request_id)stopPlayback(true);
    stopRecognition();turnInFlight=true;$('voiceAlert').textContent='';$('transcript').textContent=clean;$('reply').textContent='';
    if(!samePending)appendMessage('user_message',clean);
    try{
      let result,lastError;
      for(let attempt=0;attempt<2;attempt++){
        try{
          result=await api('/voice/turn',{method:'POST',body:JSON.stringify({request_id:pending.request_id,transcript:clean,conversation_id:currentConversationId,input_modality:pending.input_modality||'text'})});
          lastError=null;break;
        }catch(error){lastError=error;if(terminalHttp(error.status))break;await new Promise(resolve=>setTimeout(resolve,180*(attempt+1)))}
      }
      if(lastError)throw lastError;
      clearPending(pending.request_id);
      if(currentUiRequestId!==pending.request_id)return;
      currentConversationId=result.conversation_id||currentConversationId;
      if(result.conversation_title){currentConversationTitle=result.conversation_title;$('conversationTitle').textContent=currentConversationTitle}
      $('reply').textContent=result.reply;turnInFlight=false;
      if(result.status==='approval_required')showApproval(result.approval);else appendMessage('assistant_message',result.reply);
      canonicalSpeakReply(result.reply,pending.request_id);refreshConversationList($('conversationSearch').value).catch(()=>{});refreshCanonicalState();
    }catch(error){
      if(currentUiRequestId!==pending.request_id)return;
      turnInFlight=false;
      if(terminalHttp(error.status))clearPending(pending.request_id);
      if(error.message!=='turn_cancelled'){$('voiceAlert').textContent=error.message;appendMessage('approval_rejected',error.message)}
      if(handsFree)scheduleListening(500);
      refreshCanonicalState();
    }
  };
})();