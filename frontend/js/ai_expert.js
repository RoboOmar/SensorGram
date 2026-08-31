import { ai } from './api.js?v=7';
import { escHtml } from './app.js?v=7';

export function initAiExpert() {
  const sendBtn = document.getElementById('ai-send-btn');
  const input = document.getElementById('ai-input');
  
  if (!sendBtn || !input) return;

  sendBtn.addEventListener('click', sendMessage);
  input.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
  });
}

async function sendMessage() {
  const input = document.getElementById('ai-input');
  const text = input.value.trim();
  if (!text) return;

  // Append user message
  appendMessage(text, true);
  input.value = '';

  // Append typing indicator
  const typingId = 'typing-' + Date.now();
  appendTypingIndicator(typingId);

  try {
    const res = await ai.ask(text);
    removeMessage(typingId);
    appendMessage(res.response, false);
  } catch (err) {
    removeMessage(typingId);
    appendMessage("Error communicating with AI Expert. Please check your connection.", false);
  }
}

function appendMessage(text, isUser) {
  const container = document.getElementById('ai-messages');
  const div = document.createElement('div');
  div.className = `chat-bubble ${isUser ? 'mine' : 'theirs'}`;
  div.innerHTML = `<div class="text">${escHtml(text)}</div>`;
  container.appendChild(div);
  div.scrollIntoView({ behavior: "smooth", block: "end" });
}

function appendTypingIndicator(id) {
  const container = document.getElementById('ai-messages');
  const div = document.createElement('div');
  div.id = id;
  div.className = 'chat-bubble theirs';
  div.innerHTML = `<div class="text"><span style="color:var(--text-muted)">Thinking...</span></div>`;
  container.appendChild(div);
  div.scrollIntoView({ behavior: "smooth", block: "end" });
}

function removeMessage(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}
