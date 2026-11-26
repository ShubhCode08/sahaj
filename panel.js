'use strict';
const BASE = 'http://127.0.0.1:8000';
const WS = 'ws://127.0.0.1:8000/ws';
const $ = id => document.getElementById(id);
let socket = null, running = false, generation = 0, demoTab = null, intent = null, expectedIndex = 0, simpleText = '', recognition = null;
// Independent browser-side allowlist. Do not trust selectors/URLs from a remote agent.
const RULES = {
  bus: [['navigate','/demo/bus',null],['fill','from','Bengaluru'],['fill','to','Mysuru'],['click','search-buses',null],['handoff','checkout',null]],
  bill: [['navigate','/demo/bill',null],['fill','consumer-id','DEMO-1042'],['click','lookup-bill',null],['handoff','payment',null]],
  scheme: [['navigate','/demo/scheme',null],['fill','district','Bengaluru'],['click','check-scheme',null],['handoff','application',null]],
  compare: [['compare','bus-offers',null],['handoff','checkout',null]]
};
const PATHS = {bus:'/demo/bus',bill:'/demo/bill',scheme:'/demo/scheme'};
function allowed(kind, i, step) {
  const rule = Object.hasOwn(RULES,kind) && RULES[kind][i];
  return Boolean(rule && step && rule[0] === step.action && rule[1] === step.target && rule[2] === (step.value ?? null));
}
function speak(text) {
  if (!('speechSynthesis' in window)) return;
  const u = new SpeechSynthesisUtterance(text); u.lang = 'en-IN'; u.rate = 0.9;
  speechSynthesis.speak(u);
}
function addLog(text, state='done') {
  $('empty').hidden = true;
  const li = document.createElement('li'); li.textContent = text; li.dataset.state = state; $('activity').append(li);
  if ($('narrate').checked) speak(text);
  return li;
}
function setRunning(value, status) {
  running = value; $('status').textContent = status; $('run').disabled = value; $('stop').disabled = !value;
  $('goal').disabled = value; $('mic').disabled = value;
  document.querySelectorAll('[data-intent]').forEach(b => b.disabled = value);
}
function cancel(reason='Stopped') {
  ++generation; if (socket) socket.close(); socket = null;
  if (reason !== 'Complete' && 'speechSynthesis' in window) speechSynthesis.cancel();
  setRunning(false, reason);
}
function assertLive(run) { if (!running || run !== generation) throw new Error('Task cancelled.'); }
async function waitForTab(id, url, run) {
  for (let i=0;i<80;i++) {
    assertLive(run);
    const t = await chrome.tabs.get(id);
    if (t.status === 'complete' && t.url === url) return;
    await new Promise(r=>setTimeout(r,125));
  }
  throw new Error('Demo page did not load. Is the local server running?');
}
// Runs inside the demo page. Checks the actual origin and path again at execution time.
function pageAction(path, action, target, value) {
  if (location.origin !== 'http://127.0.0.1:8000' || location.pathname !== path) throw Error('Unexpected page.');
  const el = document.getElementById(target);
  if (!el || el.disabled || el.hidden || !el.getClientRects().length) throw Error('Target unavailable.');
  if (action === 'fill' && el instanceof HTMLInputElement && el.type === 'text') {
    el.focus(); el.value = value; el.dispatchEvent(new Event('input',{bubbles:true})); el.dispatchEvent(new Event('change',{bubbles:true}));
  } else if (action === 'click' && el instanceof HTMLButtonElement && el.type === 'button') {
    el.click();
    if (document.getElementById('result')?.hidden !== false) throw Error('Expected result did not appear.');
  } else throw Error('Unsupported or sensitive target.');
  return true;
}
async function readOffer(key) {
  const url = BASE + '/demo/provider/' + key;
  const response = await fetch(url,{redirect:'error',credentials:'omit',signal:AbortSignal.timeout(5000)});
  if (!response.ok) throw Error('Provider unavailable.');
  const doc = new DOMParser().parseFromString(await response.text(),'text/html');
  const offer = doc.getElementById('offer');
  const price = Number(offer?.dataset.price);
  if (!offer || !offer.dataset.provider || !Number.isFinite(price) || price < 0 || !offer.dataset.duration || !offer.dataset.departure) throw Error('Invalid provider data.');
  return {provider:offer.dataset.provider,price,duration:offer.dataset.duration,departure:offer.dataset.departure,url};
}
function renderOffers(offers) {
  const table = document.createElement('table'); const header = table.createTHead().insertRow();
  for(const text of ['Provider','Price','Departs','Duration']) {const th=document.createElement('th');th.scope='col';th.textContent=text;header.append(th);}
  const body = table.createTBody();
  for (const o of offers.sort((a,b)=>a.price-b.price)) {
    const row = body.insertRow(); const a = document.createElement('a'); a.href=o.url;a.target='_blank';a.rel='noopener noreferrer';a.textContent=o.provider;row.insertCell().append(a);
    for(const text of ['₹'+o.price,o.departure,o.duration]) row.insertCell().textContent=text;
  }
  $('comparison').replaceChildren(table); $('compare-section').hidden=false;
}
async function execute(step, run) {
  assertLive(run);
  if (step.action === 'navigate') {
    const url = BASE + step.target; const tab = await chrome.tabs.create({url,active:true});
    demoTab = tab.id; await waitForTab(tab.id,url,run);
  } else if (step.action === 'fill' || step.action === 'click') {
    assertLive(run); if (demoTab === null) throw Error('No demo tab.');
    const [result] = await chrome.scripting.executeScript({target:{tabId:demoTab},func:pageAction,args:[PATHS[intent],step.action,step.target,step.value]});
    if (result?.result !== true) throw Error('Browser action failed.');
  } else if (step.action === 'compare') {
    const offers = await Promise.all([readOffer('a'),readOffer('b')]); assertLive(run); renderOffers(offers);
  } else if (step.action === 'handoff') {
    if (demoTab !== null) {try {await simplify(demoTab,run);} catch(e) {assertLive(run); addLog('Simple View unavailable; review the demo page directly.','error');}}
  } else throw Error('Unknown action.');
}
async function start(explicitIntent=null) {
  if (running) return;
  const goal = $('goal').value.trim(); if (!goal) { $('status').textContent='Enter a goal first'; $('goal').focus(); return; }
  if (recognition) {recognition.abort();recognition=null;}
  const run = ++generation; demoTab=null; intent=null; expectedIndex=0;
  $('activity').replaceChildren(); $('empty').hidden=true; $('compare-section').hidden=true;
  $('simple').replaceChildren(); simpleText=''; $('read').disabled=true;
  setRunning(true,'Connecting…');
  let pending = false, planLength = 0;
  const ws = new WebSocket(WS); socket=ws;
  ws.onopen=()=>{if(run!==generation)return; ws.send(JSON.stringify({goal,intent:explicitIntent})); $('status').textContent='Planning…';};
  ws.onmessage=async event=>{
    if(run!==generation || !running)return;
    try {
      const msg=JSON.parse(event.data);
      if(msg.type==='plan') {
        if(intent!==null || !Object.hasOwn(RULES,msg.intent) || (explicitIntent && msg.intent!==explicitIntent) || !Array.isArray(msg.steps) || msg.steps.length!==RULES[msg.intent].length || !msg.steps.every((s,i)=>allowed(msg.intent,i,s))) throw Error('Plan blocked by browser guard.');
        intent=msg.intent;planLength=msg.steps.length; addLog('Plan approved: '+intent+' (fictional data only).'); $('status').textContent='Running';
      } else if(msg.type==='step') {
        if(pending || msg.intent!==intent || msg.index!==expectedIndex || !allowed(intent,expectedIndex,msg.step)) throw Error('Action blocked by browser guard.');
        pending=true; const line=addLog(msg.step.narration,'running');
        await execute(msg.step,run);assertLive(run); line.dataset.state='done';expectedIndex++;pending=false;
        ws.send(JSON.stringify({index:msg.index,ok:true}));
      } else if(msg.type==='done') {
        if(pending || expectedIndex!==planLength || !intent) throw Error('Unexpected completion.');
        addLog(msg.message);cancel('Complete');
      } else if(msg.type==='error') {addLog(msg.message,'error');cancel('Stopped');}
      else throw Error('Unknown agent message.');
    } catch(err) {
      if(run!==generation)return;
      addLog(err.message || 'Task failed.','error');cancel('Blocked');
    }
  };
  ws.onerror=()=>{if(run===generation){addLog('Cannot reach local backend. Start it on port 8000.','error');cancel('Offline');}};
  ws.onclose=()=>{if(run===generation && running){addLog('Connection closed before completion.','error');cancel('Disconnected');}};
}
// Read-only extraction, on the active tab with Chrome-granted permission or the demo tab.
// No form values, passwords, hidden text, or page contents are sent to the backend.
function extractVisible() {
  const visible = el => !el.closest('[hidden],[aria-hidden="true"],form,nav,header,footer') && el.getClientRects().length && getComputedStyle(el).visibility==='visible';
  const cards=[]; let current=null; const root=document.querySelector('main') || document.body;
  for(const el of root.querySelectorAll('h1,h2,h3,p,li')) {
    if(!visible(el))continue;
    const text=(el.innerText || '').replace(/\s+/g,' ').trim().slice(0,250);if(!text)continue;
    if(/^H[123]$/.test(el.tagName)) {if(cards.length>=8)break;current={heading:text,lines:[]};cards.push(current);}
    else {if(!current){current={heading:'Page overview',lines:[]};cards.push(current);}if(current.lines.length<4)current.lines.push(text);}
  }
  return cards;
}
async function simplify(tabId=null, run=null) {
  if(tabId===null){const [tab]=await chrome.tabs.query({active:true,currentWindow:true});if(!tab?.id)throw Error('No active tab.');tabId=tab.id;}
  const [result]=await chrome.scripting.executeScript({target:{tabId},func:extractVisible});
  if(run!==null)assertLive(run);
  const cards=result?.result || []; $('simple').replaceChildren(); simpleText='';
  for(const card of cards){const box=document.createElement('article');box.className='simple-card';const h=document.createElement('h3');h.textContent=card.heading;box.append(h);simpleText+=card.heading+'. ';
    for(const line of card.lines){const p=document.createElement('p');p.textContent=line;box.append(p);simpleText+=line+'. ';} $('simple').append(box);}
  if(!cards.length)$('simple').textContent='No readable headings or paragraphs were found.';
  $('read').disabled=!simpleText;
}
$('run').onclick=()=>start(); $('stop').onclick=()=>{addLog('Stopped by user. Already completed actions are not undone.');cancel();};
document.querySelectorAll('[data-intent]').forEach(b=>b.onclick=()=>{$('goal').value=b.dataset.goal;start(b.dataset.intent);});
$('simplify').onclick=async()=>{try{await simplify();}catch(e){$('simple').textContent='Cannot read this page. Open a normal website or demo page, click the Sahaj toolbar icon, then try again.';simpleText='';$('read').disabled=true;}};
$('read').onclick=()=>{if('speechSynthesis' in window)speechSynthesis.cancel();speak(simpleText);};
$('mic').onclick=()=>{
  const Speech=window.SpeechRecognition || window.webkitSpeechRecognition;
  if(!Speech){$('status').textContent='Speech unavailable; type your goal';return;}
  if(recognition){recognition.abort();recognition=null;return;}
  try {const rec=new Speech();recognition=rec;rec.lang=$('language').value;rec.interimResults=false;rec.maxAlternatives=1;
    rec.onresult=e=>{if(!running)$('goal').value=e.results[0][0].transcript.slice(0,300);};
    rec.onerror=()=>{$('status').textContent='Voice unavailable; try typing';};
    rec.onend=()=>{if(recognition===rec)recognition=null;$('mic').textContent='🎙 Speak';if(!running && $('status').textContent==='Listening…')$('status').textContent='Ready';};
    rec.start();$('mic').textContent='Stop listening';$('status').textContent='Listening…';
  }catch(e){recognition=null;$('status').textContent='Voice unavailable; try typing';}
};
window.addEventListener('pagehide',()=>{if(socket)socket.close();if(recognition)recognition.abort();});
