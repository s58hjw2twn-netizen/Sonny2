'use strict';
const $ = id => document.getElementById(id);
let state = {goal:'', memories:[], messages:[]};
let editing = null;
let busy = false;
let pending = null;

function clearPrivateView() {
  state = {goal:'',memories:[],messages:[]}; stopEditing(); pending = null;
  $('chat').replaceChildren(); $('memories').replaceChildren(); $('goal').value = '';
  $('message').value = ''; $('memory-input').value = ''; $('memory-count').textContent = '0';
  $('error').textContent = ''; $('reply-status').textContent = '';
}
function showLogin(message='') {
  clearPrivateView();
  $('pilot-shell').classList.add('hidden'); $('login-panel').classList.remove('hidden');
  $('login-error').textContent = message; $('password').value = '';
}
async function api(path, options={}) {
  const response = await fetch(path, {credentials:'same-origin', ...options,
    headers:{'Content-Type':'application/json',...(options.headers || {})},signal:AbortSignal.timeout(15000)});
  if (response.status === 401) {showLogin('Your session ended. Sign in to continue.');throw new Error('Sign in required');}
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Check your input and retry.');
  return data;
}
function message(role, text) {
  const div = document.createElement('div'); div.className = 'message '+role;
  const label = document.createElement('strong'); label.textContent = role === 'user' ? 'YOU' : 'SONNY · DEMO';
  div.append(label,document.createTextNode(text));$('chat').append(div);
}
function stopEditing() {
  editing = null; $('memory-input').value = ''; $('save-fact').textContent = 'Save approved fact';
  $('cancel-edit').classList.add('hidden');
}
function render() {
  $('goal').value = state.goal; $('memory-count').textContent = state.memories.length;
  $('memories').replaceChildren();$('chat').replaceChildren();
  state.memories.forEach(fact => {
    const li = document.createElement('li');li.append(document.createTextNode(fact.statement));
    const meta = document.createElement('span');meta.className = 'fact-meta';
    meta.textContent = 'Explicitly approved · revision '+fact.revision;li.append(meta);
    const actions = document.createElement('div');actions.className = 'fact-actions';
    const correct = document.createElement('button');correct.type = 'button';correct.textContent = 'Correct';
    correct.setAttribute('aria-label','Correct '+fact.statement);
    correct.onclick = () => {editing = fact; $('memory-input').value = fact.statement; $('save-fact').textContent = 'Approve correction';$('cancel-edit').classList.remove('hidden');$('memory-input').focus();};
    const forget = document.createElement('button');forget.type = 'button';forget.textContent = 'Forget';
    forget.setAttribute('aria-label','Forget '+fact.statement);
    forget.onclick = () => action(async () => {state = await api('/api/memories/'+fact.id,{method:'DELETE'});stopEditing();render();});
    actions.append(correct,forget);li.append(actions);$('memories').append(li);
  });
  if (!state.messages.length) {
    const empty = document.createElement('p');empty.className = 'empty-chat';empty.textContent = 'Your local workspace is ready. Ask for a plan or review your approved memory.';$('chat').append(empty);
  }
  state.messages.forEach(turn => message(turn.role,turn.text));
}
function setBusy(value) {
  busy = value;
  $('pilot-shell').querySelectorAll('button').forEach(button => {button.disabled = value;});
  $('goal').disabled = value; $('memory-input').disabled = value;
}
async function action(work) {
  if (busy) return;
  setBusy(true);$('error').textContent = '';
  try {await work();}
  catch(error) { $('error').textContent = error.name === 'TimeoutError' ? 'Local server timed out. Retry when connected.' : error.message; }
  finally {setBusy(false);}
}
async function loadWorkspace() {
  state = await api('/api/workspace');render();
  $('login-panel').classList.add('hidden');$('pilot-shell').classList.remove('hidden');
  $('connection').textContent = 'Local workspace connected';
}
$('login-form').onsubmit = async event => {
  event.preventDefault();$('login-button').disabled = true;$('login-error').textContent = '';
  try {
    const response = await fetch('/auth/login',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:$('username').value,password:$('password').value}),signal:AbortSignal.timeout(15000)});
    const data = await response.json();
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Unable to sign in.');
    $('password').value = '';await loadWorkspace();
  } catch(error) {$('login-error').textContent = error.message;}
  finally {$('login-button').disabled = false;}
};
$('logout').onclick = () => action(async () => {await api('/auth/logout',{method:'POST'});showLogin();});
$('save-goal').onclick = () => action(async () => {state = await api('/api/workspace',{method:'PATCH',body:JSON.stringify({goal:$('goal').value})});render();});
$('new-chat').onclick = () => action(async () => {state = await api('/api/conversation',{method:'DELETE'});pending = null;render();});
$('erase').onclick = () => action(async () => {state = await api('/api/workspace',{method:'DELETE'});pending = null;stopEditing();$('message').value = '';render();});
$('cancel-edit').onclick = stopEditing;
$('memory-form').onsubmit = event => {
  event.preventDefault();const statement = $('memory-input').value.trim();if (!statement) return;
  action(async () => {
    const path = '/api/memories'+(editing ? '/'+editing.id : '');
    state = await api(path,{method:editing ? 'PATCH' : 'POST',body:JSON.stringify({statement,consent:true,...(editing ? {revision:editing.revision} : {})})});
    stopEditing();render();
  });
};
$('composer').onsubmit = event => {
  event.preventDefault();const text = $('message').value.trim();if (busy || !text) return;
  const draft = $('message').value;
  if (!pending || pending.message !== text) pending = {message:text,request_id:crypto.randomUUID()};
  action(async () => {
    $('reply-status').textContent = 'Preparing a demo reply…';$('chat').setAttribute('aria-busy','true');
    try {
      await api('/api/chat',{method:'POST',body:JSON.stringify(pending)});
      state = await api('/api/workspace');pending = null;render();
      if ($('message').value === draft) $('message').value = '';
      $('composer').scrollIntoView({block:'nearest'});
    } finally {$('reply-status').textContent = '';$('chat').setAttribute('aria-busy','false');}
  });
};
$('message').onkeydown = event => {if(event.key === 'Enter' && !event.shiftKey && !event.isComposing){event.preventDefault();$('composer').requestSubmit();}};
// An expired session or browser back/forward cache must not reveal a prior account.
window.addEventListener('pageshow', event => {if(event.persisted){showLogin();loadWorkspace().catch(() => showLogin());}});
loadWorkspace().catch(() => showLogin());
