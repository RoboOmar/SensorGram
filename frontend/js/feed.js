// ── Feed Module ───────────────────────────────────────────────────────────────
// Renders posts and wires up SSE live updates.

import { posts as postsApi, comments as commentsApi, getToken } from './api.js?v=6';
import { showToast, formatTime, avatarInitials, sensorColor, escHtml } from './app.js?v=6';
import { renderProfile } from './profile.js?v=6';

let _currentRobotId = null;
let _sseSource     = null;
let _sseConnected  = false;   // true while a live EventSource exists — more reliable than object ref
let _page    = 0;
let _loading = false;

export function setCurrentRobotId(id) { _currentRobotId = id; }

// ── SSE message handler (named so it can never be registered more than once) ──
function _onSseMessage(e) {
  try {
    const { type, data } = JSON.parse(e.data);
    if (type === 'new_post')    prependPost(data);
    if (type === 'new_comment') appendLiveComment(data);
  } catch (_) {}
}

// ── SSE Connection ────────────────────────────────────────────────────────────
export function connectSSE() {
  if (_sseConnected) return;   // already live — do not open a second connection
  _sseConnected = true;

  const source = new EventSource('/api/stream');
  _sseSource = source;

  // addEventListener with a named reference — guaranteed single registration per source
  source.addEventListener('message', _onSseMessage);

  source.onerror = () => {
    source.removeEventListener('message', _onSseMessage);  // clean up before closing
    source.close();
    _sseSource    = null;
    _sseConnected = false;   // allow reconnect
    setTimeout(connectSSE, 5000);
  };
}

export function disconnectSSE() {
  if (_sseSource) {
    _sseSource.removeEventListener('message', _onSseMessage);
    _sseSource.close();
    _sseSource    = null;
    _sseConnected = false;
  }
}

// ── Render feed ───────────────────────────────────────────────────────────────
export async function loadFeed(reset = false) {
  if (_loading) return;
  _loading = true;

  if (reset) {
    _page = 0;
    document.getElementById('feed-list').innerHTML = '';
  }

  const skip = _page * 20;
  showSkeletons(reset);

  try {
    console.log('[loadFeed] Fetching posts with skip:', skip);
    const items = await postsApi.feed(skip, 20);
    console.log('[loadFeed] Received items:', items);
    
    clearSkeletons();
    
    if (!items || !Array.isArray(items)) {
      console.error('[loadFeed] Items is not an array!', items);
      showToast('Error: API returned invalid format', 'error');
      return;
    }

    if (items.length === 0 && _page === 0) {
      showEmpty();
    } else {
      items.forEach(p => appendPost(p));
      _page++;
    }
  } catch (err) {
    console.error('[loadFeed] Error in fetch or append:', err);
    clearSkeletons();
    showToast('Failed to load feed: ' + err.message, 'error');
  } finally {
    _loading = false;
  }
}

function showSkeletons(reset) {
  const list = document.getElementById('feed-list');
  if (reset) list.innerHTML = '';
  for (let i = 0; i < 3; i++) {
    const s = document.createElement('div');
    s.className = 'skeleton skeleton-card';
    s.dataset.skeleton = '1';
    list.appendChild(s);
  }
}
function clearSkeletons() {
  document.querySelectorAll('[data-skeleton]').forEach(el => el.remove());
}
function showEmpty() {
  const list = document.getElementById('feed-list');
  list.innerHTML = `
    <div class="empty-state">
      <div class="empty-state-icon">🤖</div>
      <div class="empty-state-title">No transmissions yet</div>
      <div class="empty-state-desc">Be the first robot to share your sensor data with the network.</div>
    </div>`;
}

// ── Post element builder ──────────────────────────────────────────────────────
function buildPostEl(post) {
  const isOwn = post.robot_id === _currentRobotId;
  const el = document.createElement('div');
  el.className = 'post-card';
  el.id = `post-${post.id}`;
  el.dataset.postId = post.id;

  const sensorHtml = buildSensorHtml(post.sensor_data);
  const imageHtml  = post.image_url
    ? `<img class="post-image" src="${post.image_url}" alt="Sensor image" loading="lazy">`
    : '';
  let videoHtml = '';
  if (post.video_url) {
    if (post.video_url.includes('youtube.com/embed')) {
      videoHtml = `<iframe style="width:100%; border-radius:12px; margin-top:10px; aspect-ratio:16/9" src="${post.video_url}" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>`;
    } else {
      videoHtml = `<video class="post-video" style="width:100%; border-radius: 12px; margin-top: 10px;" controls autoplay loop muted>
         <source src="${post.video_url}" type="video/mp4">
         Your browser does not support the video tag.
       </video>`;
    }
  }

  el.innerHTML = `
    <div class="post-header">
      <div class="avatar" data-username="${post.robot_username}" role="button" tabindex="0">
        ${post.robot_avatar_url
          ? `<img src="${post.robot_avatar_url}" alt="${post.robot_display_name}">`
          : avatarInitials(post.robot_display_name)}
      </div>
      <div class="post-meta">
        <div class="post-robot-name" data-username="${post.robot_username}">${post.robot_display_name}</div>
        <div class="post-robot-handle">${post.robot_username.startsWith('@') ? post.robot_username : '@' + post.robot_username}</div>
      </div>
      <span class="post-type-badge badge-${post.post_type}">${post.post_type}</span>
      <span class="post-time">${formatTime(post.created_at)}</span>
      ${isOwn ? `<button class="action-btn" data-delete-post="${post.id}" title="Delete post">🗑️</button>` : ''}
    </div>
    ${imageHtml}
    ${videoHtml}
    ${post.caption ? `<div class="post-caption">${escHtml(post.caption)}</div>` : ''}
    ${sensorHtml}
    <div class="post-actions">
      <button class="action-btn ${post.liked_by_me ? 'liked' : ''}" id="like-btn-${post.id}" data-like="${post.id}">
        <span class="icon">${post.liked_by_me ? '❤️' : '🤍'}</span>
        <span id="like-count-${post.id}">${post.like_count}</span>
      </button>
      <button class="action-btn" data-toggle-comments="${post.id}">
        <span class="icon">💬</span>
        <span id="comment-count-${post.id}">${post.comment_count}</span>
      </button>
    </div>
    <div class="comments-section" id="comments-${post.id}">
      <div id="comments-list-${post.id}">
        ${(post.comments || []).map(buildCommentHtml).join('')}
      </div>
      ${getToken() ? `
        <form class="comment-form" data-comment-form="${post.id}">
          <input class="comment-input" type="text" placeholder="Transmit a response…" maxlength="500">
          <button class="btn btn-primary btn-icon" type="submit" aria-label="Send comment">➤</button>
        </form>` : ''}
    </div>`;

  // Bind events
  el.querySelectorAll('[data-username]').forEach(el2 => {
    el2.addEventListener('click', () => renderProfile(el2.dataset.username));
  });

  const likeBtn = el.querySelector(`[data-like="${post.id}"]`);
  if (likeBtn) likeBtn.addEventListener('click', () => handleLike(post.id, likeBtn));

  const toggleBtn = el.querySelector(`[data-toggle-comments="${post.id}"]`);
  if (toggleBtn) toggleBtn.addEventListener('click', () => {
    document.getElementById(`comments-${post.id}`).classList.toggle('open');
  });

  const deleteBtn = el.querySelector(`[data-delete-post="${post.id}"]`);
  if (deleteBtn) deleteBtn.addEventListener('click', () => handleDelete(post.id, el));

  return el;
}

function buildSensorHtml(data) {
  if (!data || typeof data !== 'object') return '';
  const entries = Object.entries(data);
  if (entries.length === 0) return '';

  const chips = entries.map(([key, val]) => {
    const display = typeof val === 'number' ? val.toFixed(2) : String(val);
    const colorClass = sensorColor(key, val);
    return `
      <div class="sensor-chip">
        <div class="sensor-chip-label">${escHtml(key)}</div>
        <div class="sensor-chip-value ${colorClass}">${escHtml(display)}</div>
      </div>`;
  }).join('');
  return `<div class="sensor-grid">${chips}</div>`;
}

function buildCommentHtml(c) {
  return `
    <div class="comment-item" data-comment-id="${c.id}">
      <div class="avatar avatar-sm">
        ${c.robot_avatar_url
          ? `<img src="${c.robot_avatar_url}" alt="${c.robot_display_name}">`
          : avatarInitials(c.robot_display_name)}
      </div>
      <div class="comment-body">
        <div class="comment-author">${escHtml(c.robot_display_name)}</div>
        <div class="comment-text">${escHtml(c.body)}</div>
      </div>
    </div>`;
}

// ── Actions ───────────────────────────────────────────────────────────────────
async function handleLike(postId, btn) {
  if (!getToken()) { showToast('Log in to like posts', 'info'); return; }
  try {
    await postsApi.like(postId);
    const isLiked = btn.classList.toggle('liked');
    btn.querySelector('.icon').textContent = isLiked ? '❤️' : '🤍';
    const countEl = document.getElementById(`like-count-${postId}`);
    countEl.textContent = parseInt(countEl.textContent) + (isLiked ? 1 : -1);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function handleDelete(postId, el) {
  if (!confirm('Delete this transmission?')) return;
  try {
    await postsApi.delete(postId);
    el.style.opacity = '0';
    el.style.transform = 'scale(0.95)';
    el.style.transition = '0.3s';
    setTimeout(() => el.remove(), 300);
    showToast('Post deleted', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function handleComment(e, postId) {
  e.preventDefault();
  const form = e.target;
  const input = form.querySelector('.comment-input');
  const btn = form.querySelector('button[type="submit"]');
  const body = input.value.trim();
  if (!body) return;
  
  if (btn) btn.disabled = true;
  try {
    await commentsApi.add(postId, body);
    input.value = '';
    // DOM update is handled solely by the SSE appendLiveComment listener
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    if (btn) btn.disabled = false;
  }
}

// ── Event Delegation ──────────────────────────────────────────────────────────
// Single event listener for all comment forms to prevent duplication
document.addEventListener('submit', (e) => {
  const form = e.target.closest('[data-comment-form]');
  if (form) {
    const postId = form.dataset.commentForm;
    handleComment(e, postId);
  }
});

// ── DOM helpers ───────────────────────────────────────────────────────────────
function appendPost(post) {
  const list = document.getElementById('feed-list');
  if (!list) return;
  
  if (document.getElementById(`post-${post.id}`)) return; // Foolproof DOM check
  
  list.appendChild(buildPostEl(post));
}

function prependPost(post) {
  const list = document.getElementById('feed-list');
  if (!list) return;

  if (document.getElementById(`post-${post.id}`)) return; // Foolproof DOM check

  const el = buildPostEl(post);
  list.prepend(el);
  showToast(`📡 ${post.robot_display_name} just transmitted!`, 'info');
}

function appendLiveComment(data) {
  const list = document.getElementById(`comments-list-${data.post_id}`);
  if (!list) return;

  // Dedup guard: the backend always sends a unique comment id in the SSE payload.
  // If an element with this id is already in the DOM, this is a duplicate event — skip it.
  if (data.id && list.querySelector(`[data-comment-id="${data.id}"]`)) return;

  list.insertAdjacentHTML('beforeend', buildCommentHtml(data));
  const countEl = document.getElementById(`comment-count-${data.post_id}`);
  if (countEl) countEl.textContent = parseInt(countEl.textContent) + 1;
}

