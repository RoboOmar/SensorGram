// ΓöÇΓöÇ Feed Module ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
// Renders posts and wires up SSE live updates.

import { posts as postsApi, comments as commentsApi, getToken } from './api.js?v=6';
import { showToast, formatTime, avatarInitials, sensorColor, escHtml } from './app.js?v=6';
import { renderProfile } from './profile.js?v=6';

let _currentRobotId = null;
let _sseSource     = null;
let _sseConnected  = false;   // true while a live EventSource exists ΓÇö more reliable than object ref
let _page    = 0;
let _loading = false;

export function setCurrentRobotId(id) { _currentRobotId = id; }

// ΓöÇΓöÇ SSE message handler (named so it can never be registered more than once) ΓöÇΓöÇ
function _onSseMessage(e) {
  try {
    const { type, data } = JSON.parse(e.data);
    if (type === 'new_post')    prependPost(data);
    if (type === 'new_comment') appendLiveComment(data);
  } catch (_) {}
}

// ΓöÇΓöÇ SSE Connection ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
export function connectSSE() {
  if (_sseConnected) return;   // already live ΓÇö do not open a second connection
  _sseConnected = true;

  const source = new EventSource('/api/stream');
  _sseSource = source;

  // addEventListener with a named reference ΓÇö guaranteed single registration per source
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

// ΓöÇΓöÇ Render feed ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
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

// ΓöÇΓöÇ Post element builder ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
function buildPostEl(post) {
  const isOwn = post.robot_id === _currentRobotId;
  const deleteBtnHtml = isOwn 
    ? `<button class="action-btn" data-delete-post="${post.id}" title="Delete Post"><span class="icon">🗑️</span></button>` 
    : '';
  const likedClass = post.liked_by_me ? 'liked' : '';
  
  const el = document.createElement('div');
  el.className = 'post-card';
  el.id = `post-${post.id}`;
  el.dataset.postId = post.id;
  el.dataset.postAuthorId = post.robot_id;

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
      <div class="avatar avatar-sm" style="cursor: pointer;" onclick="window.openProfile('${post.robot_username}')">
        ${post.robot_avatar_url
          ? `<img src="${post.robot_avatar_url}" alt="${post.robot_display_name}">`
          : avatarInitials(post.robot_display_name)}
      </div>
      <div class="post-meta">
        <div class="author-name" style="cursor: pointer;" onclick="window.openProfile('${post.robot_username}')">${escHtml(post.robot_display_name)}</div>
        <div class="post-time">${formatTime(post.created_at)}</div>
      </div>
      ${deleteBtnHtml}
    </div>
    <div class="post-content">
      ${post.caption ? `<p>${escHtml(post.caption)}</p>` : ''}
      ${sensorHtml}
      ${post.image_url ? `<img src="${post.image_url}" class="post-media" loading="lazy">` : ''}
      ${videoHtml}
    </div>
    <div class="post-actions">
      <button class="action-btn ${likedClass}" data-like="${post.id}">
        <span class="icon">${post.liked_by_me ? '❤️' : '🤍'}</span>
        <span class="like-count">${post.like_count}</span>
      </button>
      <button class="action-btn" data-toggle-comments="${post.id}">
        <span class="icon">💬</span>
        <span id="comment-count-${post.id}">${post.comment_count}</span>
      </button>
    </div>
    <div class="comments-section" id="comments-${post.id}">
      <div id="comments-list-${post.id}">
        ${buildCommentTreeHtml(post.comments || [], post.robot_id)}
      </div>
      ${getToken() ? `
        <form class="comment-form" data-comment-form="${post.id}">
          <input class="comment-input" type="text" placeholder="Transmit a responseΓÇª" maxlength="500">
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

function buildCommentTreeHtml(comments, postAuthorId) {
  if (!comments || !comments.length) return '';
  const rootComments = comments.filter(c => !c.parent_comment_id);
  return rootComments.map(c => buildCommentHtml(c, postAuthorId, comments)).join('');
}

function buildCommentHtml(c, postAuthorId, allComments = [], isNested = false) {
  const isCreator = String(c.robot_id) === String(postAuthorId);
  const badgeHtml = isCreator ? `<span class="creator-badge" title="Creator" style="color: #ffd700; font-size: 0.8em; margin-left: 4px;">👑</span>` : '';
  const likedClass = c.liked_by_me ? 'liked' : '';
  const likeColor = c.liked_by_me ? '#e0245e' : 'inherit';
  
  const replies = allComments.filter(reply => reply.parent_comment_id === c.id);
  const repliesHtml = replies.map(reply => buildCommentHtml(reply, postAuthorId, allComments, true)).join('');

  return `
    <div class="comment-item ${isNested ? 'nested-reply' : ''}" data-comment-id="${c.id}" style="${isNested ? 'margin-left: 32px; border-left: 2px solid var(--surface-light); padding-left: 12px; margin-top: 8px;' : 'margin-bottom: 12px;'}">
      <div style="display: flex; gap: 10px;">
        <div class="avatar avatar-sm">
          ${c.robot_avatar_url
            ? `<img src="${c.robot_avatar_url}" alt="${escHtml(c.robot_display_name)}">`
            : avatarInitials(c.robot_display_name)}
        </div>
        <div class="comment-body" style="flex: 1; min-width: 0;">
          <div class="comment-author" style="display: flex; align-items: center;">
            ${escHtml(c.robot_display_name)} ${badgeHtml}
          </div>
          <div class="comment-text" style="word-wrap: break-word;">${escHtml(c.body)}</div>
          <div class="comment-actions" style="display: flex; gap: 15px; margin-top: 6px; font-size: 0.85em; color: var(--text-muted);">
            <button class="comment-like-btn ${likedClass}" data-comment-like="${c.id}" style="background: none; border: none; color: inherit; cursor: pointer; padding: 0; display: flex; align-items: center; gap: 4px;">
              <span class="icon" id="comment-heart-${c.id}" style="font-size: 1.1em; color: ${likeColor}; transition: color 0.2s;">♥</span> 
              <span id="comment-like-count-${c.id}">${c.like_count || 0}</span>
            </button>
            <button class="comment-reply-btn" data-comment-reply="${c.id}" data-comment-author="${escHtml(c.robot_display_name)}" style="background: none; border: none; color: inherit; cursor: pointer; padding: 0;">Reply</button>
          </div>
        </div>
      </div>
      <div class="replies-container" id="replies-${c.id}" style="margin-top: 4px;">
        ${repliesHtml}
      </div>
    </div>`;
}

// ΓöÇΓöÇ Actions ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
async function handleLike(postId, btn) {
  if (!getToken()) { showToast('Log in to like posts', 'info'); return; }
  try {
    await postsApi.like(postId);
    const isLiked = btn.classList.toggle('liked');
    btn.querySelector('.icon').textContent = isLiked ? '❤️' : '🤍';
    const countEl = btn.querySelector('.like-count');
    if (countEl) {
      countEl.textContent = parseInt(countEl.textContent) + (isLiked ? 1 : -1);
    }
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
    const parentId = form.dataset.replyTo || null;
    await commentsApi.add(postId, body, parentId ? parseInt(parentId) : null);
    input.value = '';
    form.dataset.replyTo = '';
    input.placeholder = 'Transmit a response.';
    // DOM update is handled solely by the SSE appendLiveComment listener
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    if (btn) btn.disabled = false;
  }
}

// ΓöÇΓöÇ Event Delegation ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
// Single event listener for all comment forms to prevent duplication
document.addEventListener('submit', (e) => {
  const form = e.target.closest('[data-comment-form]');
  if (form) {
    const postId = form.dataset.commentForm;
    handleComment(e, postId);
  }
});

// ΓöÇΓöÇ DOM helpers ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
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
  showToast(`≡ƒôí ${post.robot_display_name} just transmitted!`, 'info');
}

function appendLiveComment(data) {
  const list = document.getElementById(`comments-list-${data.post_id}`);
  if (!list) return;

  // Dedup guard: the backend always sends a unique comment id in the SSE payload.
  if (data.id && document.querySelector(`[data-comment-id="${data.id}"]`)) return;

  const postCard = document.getElementById(`post-${data.post_id}`);
  const postAuthorId = postCard ? postCard.dataset.postAuthorId : null;
  const html = buildCommentHtml(data, postAuthorId, [], !!data.parent_comment_id);

  if (data.parent_comment_id) {
    const parentRepliesContainer = document.getElementById(`replies-${data.parent_comment_id}`);
    if (parentRepliesContainer) {
      parentRepliesContainer.insertAdjacentHTML('beforeend', html);
    }
  } else {
    list.insertAdjacentHTML('beforeend', html);
  }

  const countEl = document.getElementById(`comment-count-${data.post_id}`);
  if (countEl) countEl.textContent = parseInt(countEl.textContent) + 1;
}


document.addEventListener('click', async (e) => {
  // Reply to Comment
  const replyBtn = e.target.closest('[data-comment-reply]');
  if (replyBtn) {
    const commentId = replyBtn.dataset.commentReply;
    const authorName = replyBtn.dataset.commentAuthor;
    const postCard = replyBtn.closest('.post-card');
    if (postCard) {
      const form = postCard.querySelector('.comment-form');
      if (form) {
        form.dataset.replyTo = commentId;
        const input = form.querySelector('.comment-input');
        if (input) {
          input.placeholder = `Replying to ` + authorName;
          input.focus();
        }
      }
    }
  }

  // Like Comment
  const likeBtn = e.target.closest('[data-comment-like]');
  if (likeBtn) {
    if (!getToken()) { showToast('Log in to like comments', 'info'); return; }
    const commentId = likeBtn.dataset.commentLike;
    try {
      await commentsApi.like(commentId);
      const isLiked = likeBtn.classList.toggle('liked');
      const countEl = document.getElementById(`comment-like-count-${commentId}`);
      const iconEl = document.getElementById(`comment-heart-${commentId}`);
      if (countEl) {
        let count = parseInt(countEl.textContent) || 0;
        countEl.textContent = isLiked ? count + 1 : Math.max(0, count - 1);
      }
      if (iconEl) {
        iconEl.style.color = isLiked ? '#e0245e' : 'inherit';
      }
    } catch (err) {
      showToast(err.message, 'error');
    }
  }
});

