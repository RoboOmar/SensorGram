// ── Profile Module ────────────────────────────────────────────────────────────
import { robots as robotsApi, posts as postsApi, getToken, getUserLocal } from './api.js?v=6';
import { showToast, avatarInitials, formatTime, escHtml } from './app.js?v=6';

export async function renderProfile(username) {
  const feedView    = document.getElementById('feed-view');
  const profileView = document.getElementById('profile-view');

  feedView.classList.add('hidden');
  document.getElementById('chat-view').classList.add('hidden');
  document.getElementById('ai-view').classList.add('hidden');
  profileView.classList.remove('hidden');
  profileView.innerHTML     = buildSkeleton();

  try {
    const [robot, robotPosts] = await Promise.all([
      robotsApi.get(username),
      postsApi.forRobot(username),
    ]);

    profileView.innerHTML = buildProfileHtml(robot, robotPosts);
    bindProfileEvents(robot);
  } catch (err) {
    showToast('Failed to load profile', 'error');
    goBackToFeed();
  }
}

export function goBackToFeed() {
  document.getElementById('feed-view').classList.remove('hidden');
  document.getElementById('profile-view').classList.add('hidden');
  document.getElementById('chat-view').classList.add('hidden');
  document.getElementById('ai-view').classList.add('hidden');
}

function buildProfileHtml(robot, robotPosts) {
  const postsHtml = robotPosts.length
    ? robotPosts.map(p => buildMiniPostHtml(p)).join('')
    : `<div class="empty-state"><div class="empty-state-icon">📡</div>
       <div class="empty-state-title">No transmissions yet</div></div>`;

  return `
    <button class="btn btn-ghost" id="back-to-feed" style="margin-bottom:20px">
      ← Back to Feed
    </button>
    <div class="profile-hero">
      <div class="avatar avatar-lg" style="margin:0 auto 16px">
        ${robot.avatar_url
          ? `<img src="${robot.avatar_url}" alt="${robot.display_name}">`
          : avatarInitials(robot.display_name)}
      </div>
      <div class="profile-header">
        <h1 class="profile-name">${escHtml(robot.display_name)}</h1>
        <p class="profile-handle" style="color:var(--text-muted);font-size:0.85rem;margin:4px 0">${escHtml(robot.username.startsWith('@') ? robot.username : '@' + robot.username)}</p>
        ${robot.model_type ? `<span class="post-type-badge badge-sensor" style="display:inline-block;margin:10px 0">${escHtml(robot.model_type)}</span>` : ''}
      ${robot.location   ? `<p style="color:var(--text-secondary);font-size:0.83rem">📍 ${escHtml(robot.location)}</p>` : ''}
      ${robot.bio        ? `<p style="margin-top:12px;font-size:0.9rem;color:var(--text-secondary);max-width:420px;margin-left:auto;margin-right:auto;line-height:1.5">${escHtml(robot.bio)}</p>` : ''}

      <div class="profile-stats">
        <div class="profile-stat">
          <div class="profile-stat-value">${robot.post_count}</div>
          <div class="profile-stat-label">Posts</div>
        </div>
        <div class="profile-stat">
          <div class="profile-stat-value">${robot.follower_count}</div>
          <div class="profile-stat-label">Followers</div>
        </div>
        <div class="profile-stat">
          <div class="profile-stat-value">${robot.following_count}</div>
          <div class="profile-stat-label">Following</div>
        </div>
      </div>

      ${getToken() ? 
        (getUserLocal()?.username === robot.username
          ? `<button id="edit-profile-btn" class="btn btn-primary" style="margin-top:20px">Edit Profile</button>`
          : `<div style="display:flex; gap:10px; margin-top:20px;">
               <button id="follow-btn" data-username="${robot.username}" data-following="${robot.is_followed_by_me ? 'true' : 'false'}" class="btn ${robot.is_followed_by_me ? 'btn-ghost' : 'btn-primary'}">
                 ${robot.is_followed_by_me ? 'Unfollow' : 'Follow'}
               </button>
               <button id="message-btn" data-id="${robot.id}" data-name="${escHtml(robot.display_name)}" class="btn btn-primary">
                 Message
               </button>
             </div>`
        ) : ''}
    </div>

    <h3 style="font-size:1rem;font-weight:700;margin-bottom:16px;letter-spacing:-0.01em">📡 Transmissions</h3>
    <div id="profile-posts">${postsHtml}</div>`;
}

function buildMiniPostHtml(post) {
  const sensorSummary = post.sensor_data
    ? Object.entries(post.sensor_data).slice(0, 3)
        .map(([k, v]) => `<span style="color:var(--text-muted);font-size:0.75rem"><b style="color:var(--text-accent)">${escHtml(k)}</b> ${typeof v === 'number' ? v.toFixed(1) : v}</span>`)
        .join(' · ')
    : '';

  return `
    <div class="post-card" style="margin-bottom:14px">
      <div class="post-header">
        <span class="post-type-badge badge-${post.post_type}">${post.post_type}</span>
        <span class="post-time" style="margin-left:auto">${formatTime(post.created_at)}</span>
      </div>
      ${post.image_url ? `<img class="post-image" src="${post.image_url}" alt="Post" loading="lazy">` : ''}
      ${post.video_url ? (post.video_url.includes('youtube.com/embed') 
          ? `<iframe style="width:100%; border-radius:12px; margin-top:10px; aspect-ratio:16/9" src="${post.video_url}" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>`
          : `<video class="post-video" style="width:100%; border-radius: 12px; margin-top: 10px;" controls autoplay loop muted>
                             <source src="${post.video_url}" type="video/mp4">
                           </video>`) : ''}
      ${post.caption ? `<div class="post-caption">${escHtml(post.caption)}</div>` : ''}
      ${sensorSummary ? `<div style="padding:0 20px 14px;display:flex;flex-wrap:wrap;gap:10px">${sensorSummary}</div>` : ''}
      <div class="post-actions">
        <span class="action-btn">❤️ ${post.like_count}</span>
        <span class="action-btn">💬 ${post.comment_count}</span>
      </div>
    </div>`;
}

function bindProfileEvents(robot) {
  document.getElementById('back-to-feed')?.addEventListener('click', goBackToFeed);

  const followBtn = document.getElementById('follow-btn');
  const editBtn = document.getElementById('edit-profile-btn');

  if (editBtn) {
    editBtn.addEventListener('click', () => {
      document.getElementById('edit-profile-avatar').value = ''; // Reset file input
      document.getElementById('edit-profile-display-name').value = robot.display_name || '';
      document.getElementById('edit-profile-username').value = robot.username || '';
      document.getElementById('edit-profile-bio').value = robot.bio || '';
      document.getElementById('edit-profile-modal').classList.add('open');
    });
  }

  if (followBtn) {
    followBtn.addEventListener('click', async () => {
      const isFollowing = followBtn.dataset.following === 'true';
      try {
        if (isFollowing) {
          await robotsApi.unfollow(robot.username);
          followBtn.textContent = 'Follow';
          followBtn.dataset.following = 'false';
          followBtn.classList.add('btn-primary');
          followBtn.classList.remove('btn-ghost');
        } else {
          await robotsApi.follow(robot.username);
          followBtn.textContent = 'Unfollow';
          followBtn.dataset.following = 'true';
          followBtn.classList.add('btn-ghost');
          followBtn.classList.remove('btn-primary');
        }
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }

  const messageBtn = document.getElementById('message-btn');
  if (messageBtn) {
    messageBtn.addEventListener('click', () => {
      const navChat = document.getElementById('nav-chat');
      if (navChat) {
        navChat.click();
        // The navChat click event in app.js opens the chat view and calls initChat()
        // wait for DOM to update, then open specific chat
        setTimeout(() => {
          if (window.openChat) {
            window.openChat(robot.id, robot.display_name);
          }
        }, 300);
      }
    });
  }
}

function buildSkeleton() {
  return `
    <button class="btn btn-ghost" onclick="history.back()" style="margin-bottom:20px">← Back</button>
    <div class="skeleton" style="height:280px;border-radius:24px;margin-bottom:20px"></div>
    <div class="skeleton skeleton-card"></div>
    <div class="skeleton skeleton-card"></div>`;
}
