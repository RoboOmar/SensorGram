import { auth, chat as chatApi, getUserLocal } from './api.js?v=6';
import { formatTime, escHtml, avatarInitials, showToast } from './app.js?v=6';

let chatWs = null;
let currentChatUserId = null;

export async function initChat() {
  const token = localStorage.getItem('sg_token');
  if (!token) return;

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/api/chat/ws?token=${encodeURIComponent(token)}`;
  
  if (chatWs) chatWs.close();
  
  chatWs = new WebSocket(wsUrl);
  
  chatWs.onopen = () => {
    console.log('[Chat] WebSocket connected');
  };
  
  chatWs.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    const currentUser = getUserLocal();
    
    // If we are currently chatting with the sender (or it's a message we just sent), render it
    if (msg.sender_id === currentChatUserId || msg.receiver_id === currentChatUserId) {
        appendMessage(msg, currentUser.id);
    } else {
        // Show a toast if someone else messaged us
        if (msg.sender_id !== currentUser.id) {
            showToast('New message received!', 'success');
            loadConversations(); // Update sidebar
        }
    }
  };
  
  chatWs.onclose = () => {
    console.log('[Chat] WebSocket disconnected');
    // Reconnect after 3 seconds if we didn't deliberately close it
    setTimeout(() => {
      if (!chatWs || chatWs.readyState === WebSocket.CLOSED) {
        initChat();
      }
    }, 3000);
  };
  
  await loadConversations();
  
  document.getElementById('chat-send-btn').onclick = sendMessage;
  document.getElementById('chat-input').addEventListener('keypress', (e) => {
      if (e.key === 'Enter') sendMessage();
  });
}

// Handle mobile browser backgrounding/resuming
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') {
    // If WebSocket died while backgrounded, restart it
    if (!chatWs || chatWs.readyState !== WebSocket.OPEN) {
      initChat();
    }
    // If we have an open chat, reload history to catch missed messages
    if (currentChatUserId) {
      window.openChat(currentChatUserId, document.getElementById('chat-header-title').textContent);
    }
  }
});

async function loadConversations() {
  const usersList = document.getElementById('chat-users-list');
  if (!usersList) return;
  
  try {
    const users = await chatApi.getConversations();
    usersList.innerHTML = users.map(u => `
      <div class="chat-user-item" data-id="${u.id}" onclick="window.openChat(${u.id}, '${escHtml(u.display_name)}')">
        <div class="avatar" style="width:40px;height:40px;font-size:1rem;">
          ${u.avatar_url ? `<img src="${u.avatar_url}">` : avatarInitials(u.display_name)}
        </div>
        <div style="font-weight:600;">${escHtml(u.display_name)}</div>
      </div>
    `).join('');
  } catch (err) {
    console.error(err);
  }
}

window.openChat = async function(userId, displayName) {
  currentChatUserId = userId;
  document.getElementById('chat-header-title').textContent = displayName;
  document.getElementById('chat-messages').innerHTML = '<div class="spinner" style="margin:auto;"></div>';
  
  // Highlight active user
  document.querySelectorAll('.chat-user-item').forEach(el => el.classList.remove('active'));
  const activeEl = document.querySelector(`.chat-user-item[data-id="${userId}"]`);
  if (activeEl) activeEl.classList.add('active');
  
  try {
    const history = await chatApi.getHistory(userId);
    const currentUser = getUserLocal();
    
    document.getElementById('chat-messages').innerHTML = '';
    history.forEach(msg => appendMessage(msg, currentUser.id));
    scrollToBottom();
  } catch (err) {
    document.getElementById('chat-messages').innerHTML = '<div style="color:red;padding:20px;">Failed to load history.</div>';
  }
};

function appendMessage(msg, currentUserId) {
  const isMine = msg.sender_id === currentUserId;
  const div = document.createElement('div');
  div.className = `chat-bubble ${isMine ? 'mine' : 'theirs'}`;
  div.innerHTML = `
    <div class="text">${escHtml(msg.text_content)}</div>
    <div class="time">${new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
  `;
  document.getElementById('chat-messages').appendChild(div);
  scrollToBottom();
}

function scrollToBottom() {
  const container = document.getElementById('chat-messages');
  container.scrollTop = container.scrollHeight;
}

function sendMessage() {
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if (!text || !currentChatUserId || !chatWs || chatWs.readyState !== WebSocket.OPEN) return;
  
  const payload = {
    receiver_id: currentChatUserId,
    text_content: text
  };
  
  chatWs.send(JSON.stringify(payload));
  input.value = '';
}
