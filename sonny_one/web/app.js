'use strict';
const $ = id => document.getElementById(id);
const key = 'sonny-one-demo-v1';
const defaultGoal = 'Build a useful personal assistant';
let state = {goal: $('goal').value, memories: [], messages: []};
let busy = false;
function save() {
  try {
    if ($('persist').checked) localStorage.setItem(key, JSON.stringify(state));
    else localStorage.removeItem(key);
  } catch { $('error').textContent = 'Browser storage is unavailable. This session still works, but changes will not persist.'; }
}
function addMessage(role, text) {
  $('welcome')?.remove(); $('chat').querySelector('.empty-chat')?.remove();
  const item = document.createElement('div'); item.className = 'message ' + role;
  const label = document.createElement('strong'); label.textContent = role === 'user' ? 'YOU' : 'SONNY · DEMO';
  item.append(label, document.createTextNode(text)); $('chat').append(item);
}
function render() {
  $('goal').value = state.goal;
  $('memories').replaceChildren(); $('memory-count').textContent = state.memories.length;
  state.memories.forEach((text, i) => {
    const li = document.createElement('li'); li.append(document.createTextNode(text));
    const remove = document.createElement('button'); remove.textContent = 'Forget'; remove.type = 'button';
    remove.setAttribute('aria-label', 'Forget ' + text);
    remove.onclick = () => {state.memories.splice(i, 1); save(); render();};
    li.append(remove); $('memories').append(li);
  });
}
try {
  const saved = JSON.parse(localStorage.getItem(key));
  if (saved && typeof saved.goal === 'string' && saved.goal.length <= 500 && Array.isArray(saved.memories) && saved.memories.length <= 50 && saved.memories.every(x => typeof x === 'string' && x.trim() && x.length <= 500) && Array.isArray(saved.messages) && saved.messages.length <= 100 && saved.messages.every(x => x && ['user','assistant'].includes(x.role) && typeof x.text === 'string' && x.text.length <= 30000)) {
    state = saved; $('persist').checked = true;
    state.messages.forEach(m => addMessage(m.role, m.text));
  } else if (saved !== null) {
    $('error').textContent = 'Saved workspace was invalid. Erase workspace to remove it, or opt in to replace it.';
  }
} catch { $('error').textContent = 'Saved workspace could not be loaded. A fresh session is ready.'; }
render();
$('persist').onchange = save;
$('goal').oninput = () => {state.goal = $('goal').value; save();};
$('memory-form').onsubmit = event => {
  event.preventDefault(); const value = $('memory-input').value.trim();
  if (!value) return;
  if (state.memories.length >= 50) { $('error').textContent = 'Memory is full. Forget a fact before adding another.'; return; }
  state.memories.push(value); $('memory-input').value = ''; save(); render();
};
function clearConversation() {
  state.messages = []; $('chat').replaceChildren(); $('error').textContent = '';
  const empty = document.createElement('p'); empty.className = 'empty-chat';
  empty.textContent = 'A fresh conversation is ready. What would you like to work on?';
  $('chat').append(empty);
}
$('new-chat').onclick = () => {if (busy) return; clearConversation(); save();};
$('erase').onclick = () => {
  if (busy) return;
  state = {goal: defaultGoal, memories: [], messages: []};
  $('persist').checked = false; clearConversation(); $('memory-input').value = ''; $('message').value = ''; save(); render();
};
async function send(event) {
  event.preventDefault(); const message = $('message').value.trim();
  if (busy || !message) return;
  const draft = $('message').value;
  busy = true; $('send').disabled = true; $('new-chat').disabled = true; $('erase').disabled = true; $('error').textContent = '';
  $('chat').setAttribute('aria-busy', 'true'); $('reply-status').textContent = 'Preparing a demo reply…';
  try {
    const response = await fetch('/api/chat', {method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({message, goal: state.goal, memories: [...state.memories]}), signal: AbortSignal.timeout(15000)});
    if (!response.ok) throw new Error('Local server could not complete that request. Your message is ready to retry.');
    const data = await response.json();
    if (!data || typeof data.text !== 'string') throw new Error('Invalid demo response');
    addMessage('user', message); addMessage('assistant', data.text);
    state.messages.push({role:'user',text:message}, {role:'assistant',text:data.text});
    state.messages = state.messages.slice(-100);
    if ($('message').value === draft) $('message').value = '';
    save();
    $('composer').scrollIntoView({block:'nearest'});
  } catch (error) { $('error').textContent = error.name === 'TimeoutError' ? 'Local server timed out. Try again.' : 'Unable to reach the local demo. Check the server and retry.'; }
  finally { $('chat').setAttribute('aria-busy', 'false'); $('reply-status').textContent = ''; busy = false; $('send').disabled = false; $('new-chat').disabled = false; $('erase').disabled = false; $('message').focus(); }
}
$('composer').onsubmit = send;
$('message').onkeydown = event => {if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {event.preventDefault(); $('composer').requestSubmit();}};
document.querySelectorAll('[data-prompt]').forEach(button => button.onclick = () => {$('message').value = button.dataset.prompt; $('composer').requestSubmit();});
fetch('/api/status').then(r => {if (!r.ok) throw new Error(); return r.json();}).then(() => {$('connection').textContent = 'Local server connected';}).catch(() => {$('connection').textContent = 'Local server unavailable';});

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js').then(() => navigator.serviceWorker.ready).then(() => {
    $('install-status').textContent = 'Demo shell available for home-screen use. Sending messages needs the local server.';
  }).catch(() => {
    $('install-status').textContent = 'Home-screen offline support is unavailable in this browser.';
  });
}
