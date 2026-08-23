// ── App Bootstrap ─────────────────────────────────────────────────────────────
import { auth, robots as robotsApi, posts as postsApi, setToken, getToken, setUserLocal, getUserLocal } from './api.js?v=6';
import { loadFeed, connectSSE, disconnectSSE, setCurrentRobotId } from './feed.js?v=6';
import { renderProfile, goBackToFeed } from './profile.js?v=7';
import { initChat } from './chat.js?v=7';
import { initAiExpert } from './ai_expert.js?v=7';

// ── Exported helpers (used by other modules) ──────────────────────────────────
export function showToast(msg, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  const icons = { success: '✅', error: '❌', info: '📡' };
  toast.innerHTML = `<span>${icons[type] || '📡'}</span><span>${escHtml(msg)}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    toast.style.transition = '0.3s';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

export function formatTime(isoStr) {
  const d = new Date(isoStr + 'Z');
  const now = new Date();
  const diff = Math.floor((now - d) / 1000);
  if (diff < 60)   return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return d.toLocaleDateString();
}

export function avatarInitials(name = '') {
  return name.split(/\s+/).slice(0, 2).map(w => w[0]?.toUpperCase() || '').join('') || '🤖';
}

export function sensorColor(key, val) {
  if (typeof val !== 'number') return '';
  const k = key.toLowerCase();
  if (k.includes('temp') || k.includes('heat')) {
    if (val > 80) return 'warn';
    if (val > 50) return 'hot';
    return 'cool';
  }
  if (k.includes('battery') || k.includes('bat')) {
    if (val < 20) return 'warn';
    if (val < 50) return 'hot';
    return 'ok';
  }
  return '';
}

export function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── State ─────────────────────────────────────────────────────────────────────
let _currentUser = null;

function setUser(user, apiKey) {
  _currentUser = user;
  setUserLocal(user);
  setCurrentRobotId(user?.id ?? null);

  // Update UI
  document.getElementById('user-display-name').textContent = user?.display_name ?? '';
  document.getElementById('user-username').textContent = user ? (user.username.startsWith('@') ? user.username : `@${user.username}`) : '';

  const authBtns = document.getElementById('auth-buttons');
  const userInfo  = document.getElementById('user-info');
  if (user) {
    authBtns.classList.add('hidden');
    userInfo.classList.remove('hidden');
    if (apiKey) {
      document.getElementById('api-key-display').textContent = apiKey;
    }
    const keySection = document.getElementById('api-key-section');
    if (keySection) keySection.style.display = 'block';
  } else {
    authBtns.classList.remove('hidden');
    userInfo.classList.add('hidden');
    const keySection = document.getElementById('api-key-section');
    if (keySection) keySection.style.display = 'none';
  }

  // Post button visibility
  document.getElementById('new-post-btn').style.display = user ? 'flex' : 'none';
}

// ── Auth modal ────────────────────────────────────────────────────────────────
function openAuthModal(mode = 'login') {
  const overlay = document.getElementById('auth-modal');
  const title   = document.getElementById('auth-modal-title');
  const extra   = document.getElementById('register-extra-fields');
  const switchEl = document.getElementById('auth-switch-link');
  const forgotEl = document.getElementById('forgot-password-container');
  
  const userLabel = document.querySelector('label[for="auth-username"]');
  const userInput = document.getElementById('auth-username');

  title.textContent = mode === 'login' ? 'Log In' : 'Register Robot';
  extra.style.display = mode === 'register' ? 'block' : 'none';
  if (forgotEl) forgotEl.style.display = mode === 'login' ? 'block' : 'none';
  switchEl.dataset.mode = mode === 'login' ? 'register' : 'login';
  switchEl.textContent  = mode === 'login' ? 'Create an account' : 'Already have an account?';
  
  if (mode === 'login') {
    userLabel.textContent = 'Username or Email';
    userInput.placeholder = 'unit_alpha_7 or unit@sensorgram.local';
  } else {
    userLabel.textContent = 'Username';
    userInput.placeholder = 'unit_alpha_7';
  }

  overlay.classList.add('open');
}

function closeModal(id) {
  document.getElementById(id).classList.remove('open');
}

// ── Post modal ────────────────────────────────────────────────────────────────
function openPostModal() {
  if (!getToken()) { openAuthModal('login'); return; }
  document.getElementById('post-modal').classList.add('open');
}

// ── Suggested for You ─────────────────────────────────────────────────────────
async function loadSuggestedRobots() {
  try {
    const list = await robotsApi.suggested();
    const container = document.getElementById('suggested-robots-list');
    if (!container) return;
    if (list.length === 0) {
      container.innerHTML = '<div class="text-sm text-muted" style="padding: 10px;">No active robots yet</div>';
      return;
    }
    container.innerHTML = list.map(r => `
      <div class="robot-suggestion" data-profile="${r.username}">
        <div class="avatar" style="width:38px;height:38px;font-size:0.9rem">
          ${r.avatar_url ? `<img src="${r.avatar_url}" alt="">` : avatarInitials(r.display_name)}
        </div>
        <div class="robot-suggestion-info truncate">
          <div class="robot-suggestion-name truncate">${escHtml(r.display_name)}</div>
          <div class="robot-suggestion-model truncate">${escHtml(r.username.startsWith('@') ? r.username : '@' + r.username)}</div>
        </div>
        <button class="btn btn-ghost" style="padding: 4px 10px; font-size: 0.75rem;" data-follow="${r.username}">Follow</button>
      </div>`).join('');

    // Clicking profile goes to profile
    container.querySelectorAll('.robot-suggestion-info, .avatar').forEach(el => {
      el.addEventListener('click', (e) => {
        const row = e.target.closest('.robot-suggestion');
        if (row) renderProfile(row.dataset.profile);
      });
    });

    // Follow button
    container.querySelectorAll('[data-follow]').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        if (!getToken()) { openAuthModal('login'); return; }
        const username = btn.dataset.follow;
        btn.disabled = true;
        try {
          await robotsApi.follow(username);
          btn.textContent = 'Following';
          btn.style.color = 'var(--text-accent)';
          showToast(`Following ${username}`, 'success');
        } catch (err) {
          showToast(err.message, 'error');
          btn.disabled = false;
        }
      });
    });
  } catch (_) {}
}

function updateStats(robotCount, postCount) {
  const rc = document.getElementById('stat-robots');
  const pc = document.getElementById('stat-posts');
  if (rc) rc.textContent = robotCount;
  if (pc) pc.textContent = postCount;
}

// ── Nav helpers ───────────────────────────────────────────────────────────────
function setActive(el) {
  document.querySelectorAll('.sidebar-link').forEach(l => l.classList.remove('active'));
  el.classList.add('active');
}

// ── Boot ──────────────────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', async () => {
  try {
    // Restore session
  const savedToken = getToken();
  const savedUser = getUserLocal();
  
  if (savedToken && savedUser) {
    // Optimistic fast login
    setUser(savedUser, savedUser.api_key);
    // Background refresh
    auth.me().then(me => setUser(me, me.api_key)).catch((err) => {
      if (err.message && err.message.includes('401')) {
        setToken(null);
        setUser(null);
      }
    });
  } else if (savedToken) {
    try {
      const me = await auth.me();
      setUser(me, me.api_key);
    } catch (err) {
      if (err.message && err.message.includes('401')) {
        setToken(null);
        setUser(null);
      }
    }
  } else {
    setUser(null);
  }

  connectSSE();
  await loadFeed(true);
  loadSuggestedRobots();

  // ── Search ────────────────────────────────────────────────────────────────
  let searchTimeout;
  const searchInput = document.getElementById('search-input');
  const searchDropdown = document.getElementById('search-dropdown');

  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const q = e.target.value.trim();
      clearTimeout(searchTimeout);
      if (!q) {
        searchDropdown.classList.add('hidden');
        return;
      }
      searchTimeout = setTimeout(async () => {
        try {
          const results = await robotsApi.search(q);
          if (results.length === 0) {
            searchDropdown.innerHTML = '<div style="padding: 12px; color: var(--text-muted); font-size: 0.85rem;">No robots found.</div>';
          } else {
            searchDropdown.innerHTML = results.map(r => `
              <div class="search-result-item" data-profile="${r.username}">
                <div class="avatar" style="width:32px;height:32px;font-size:0.8rem">
                  ${r.avatar_url ? `<img src="${r.avatar_url}" alt="">` : avatarInitials(r.display_name)}
                </div>
                <div class="search-result-info truncate">
                  <div class="search-result-name truncate">${escHtml(r.display_name)}</div>
                  <div class="search-result-username truncate">${escHtml(r.username.startsWith('@') ? r.username : '@' + r.username)}</div>
                </div>
              </div>
            `).join('');
            
            searchDropdown.querySelectorAll('.search-result-item').forEach(item => {
              item.addEventListener('click', () => {
                searchDropdown.classList.add('hidden');
                searchInput.value = '';
                renderProfile(item.dataset.profile);
              });
            });
          }
          searchDropdown.classList.remove('hidden');
        } catch (err) {
          console.error(err);
        }
      }, 300);
    });

    document.addEventListener('click', (e) => {
      if (!e.target.closest('.search-container')) {
        searchDropdown?.classList.add('hidden');
      }
    });
  }

  // ── Navigation ────────────────────────────────────────────────────────────
  document.getElementById('nav-feed')?.addEventListener('click', (e) => {
    setActive(e.currentTarget);
    document.getElementById('chat-view').style.display = 'none';
    document.getElementById('ai-view').style.display = 'none';
    goBackToFeed();
    loadFeed(true);
  });

  document.getElementById('nav-profile')?.addEventListener('click', (e) => {
    if (!_currentUser) { openAuthModal('login'); return; }
    setActive(e.currentTarget);
    document.getElementById('chat-view').style.display = 'none';
    document.getElementById('ai-view').style.display = 'none';
    renderProfile(_currentUser.username);
  });
  
  document.getElementById('nav-chat')?.addEventListener('click', (e) => {
    if (!_currentUser) { openAuthModal('login'); return; }
    setActive(e.currentTarget);
    document.getElementById('feed-view').style.display = 'none';
    document.getElementById('profile-view').style.display = 'none';
    document.getElementById('ai-view').style.display = 'none';
    document.getElementById('chat-view').style.display = 'flex';
    initChat();
  });

  document.getElementById('nav-ai-expert')?.addEventListener('click', (e) => {
    if (!_currentUser) { openAuthModal('login'); return; }
    setActive(e.currentTarget);
    document.getElementById('feed-view').style.display = 'none';
    document.getElementById('profile-view').style.display = 'none';
    document.getElementById('chat-view').style.display = 'none';
    document.getElementById('ai-view').style.display = 'flex';
    initAiExpert();
  });

  // ── Auth buttons ──────────────────────────────────────────────────────────
  document.getElementById('login-btn')?.addEventListener('click', () => openAuthModal('login'));
  document.getElementById('register-btn')?.addEventListener('click', () => openAuthModal('register'));
  document.getElementById('logout-btn')?.addEventListener('click', () => {
    setToken(null);
    setUser(null);
    goBackToFeed();
    loadFeed(true);
    showToast('Logged out', 'info');
  });

  // ── Modal close ───────────────────────────────────────────────────────────
  document.querySelectorAll('[data-close-modal]').forEach(btn => {
    btn.addEventListener('click', () => closeModal(btn.dataset.closeModal));
  });
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) overlay.classList.remove('open');
    });
  });

  // ── Auth modal switch ─────────────────────────────────────────────────────
  document.getElementById('auth-switch-link')?.addEventListener('click', (e) => {
    openAuthModal(e.target.dataset.mode);
  });

  // ── Auth form submit ──────────────────────────────────────────────────────
  const authForm = document.getElementById('auth-form');
  if (authForm) {
    authForm.onsubmit = async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      const mode = document.getElementById('auth-modal-title').textContent.toLowerCase().includes('log')
        ? 'login' : 'register';

      const submitBtn = e.target.querySelector('[type=submit]');
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner"></span>';

      try {
        let resp;
        if (mode === 'login') {
          resp = await auth.login({ identifier: fd.get('username'), password: fd.get('password') });
        } else {
          resp = await auth.register({
            username:     fd.get('username'),
            email:        fd.get('email'),
            display_name: fd.get('display_name') || fd.get('username'),
            password:     fd.get('password'),
            location:     fd.get('location') || null,
            bio:          fd.get('bio') || null,
          });
        }
        setToken(resp.access_token);
        setUser(resp.robot, resp.api_key);
        closeModal('auth-modal');
        showToast(`Welcome, ${resp.robot.display_name}! 🤖`, 'success');
        e.target.reset();
        loadSuggestedRobots();
      } catch (err) {
        alert("Error: " + err.message);
        showToast(err.message, 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = mode === 'login' ? 'Log In' : 'Register';
      }
    };
  }

  // ── New post button ───────────────────────────────────────────────────────
  document.getElementById('new-post-btn')?.addEventListener('click', openPostModal);

  // ── Post form submit ──────────────────────────────────────────────────────
  const postForm = document.getElementById('post-form');
  if (postForm) {
    postForm.onsubmit = async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      const sensorRaw = fd.get('sensor_data');

      // Validate sensor JSON if provided
      if (sensorRaw) {
        try { JSON.parse(sensorRaw); } catch (_) {
          showToast('Sensor data must be valid JSON', 'error'); return;
        }
      }

      const submitBtn = e.target.querySelector('[type=submit]');
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner"></span> Transmitting…';

      try {
        await postsApi.create(fd);
        closeModal('post-modal');
        e.target.reset();
        showToast('Transmission sent! 📡', 'success');
        goBackToFeed();
      } catch (err) {
        showToast(err.message, 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Transmit';
      }
    };
  }

  // ── Infinite scroll ───────────────────────────────────────────────────────
  const mainContent = document.querySelector('.main-content');
  mainContent?.addEventListener('scroll', () => {
    const { scrollTop, scrollHeight, clientHeight } = mainContent;
    if (scrollHeight - scrollTop - clientHeight < 200) {
      loadFeed(false);
    }
  });

  // ── Forgot Password Logic ──────────────────────────────────────────────────
  document.getElementById('forgot-password-link')?.addEventListener('click', () => {
    closeModal('auth-modal');
    document.getElementById('forgot-password-modal').classList.add('open');
  });

  const forgotForm = document.getElementById('forgot-password-form');
  if (forgotForm) {
    forgotForm.onsubmit = async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      const submitBtn = e.target.querySelector('[type=submit]');
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner"></span>';
      try {
        await auth.forgotPassword({ email: fd.get('email') });
        closeModal('forgot-password-modal');
        showToast('Reset link sent to your email', 'success');
        e.target.reset();
      } catch (err) {
        showToast(err.message, 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Send Reset Link';
      }
    };
  }

  // ── Edit Profile Logic ─────────────────────────────────────────────────────
  const editProfileForm = document.getElementById('edit-profile-form');
  if (editProfileForm) {
    editProfileForm.onsubmit = async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      let newDisplayName = fd.get('display_name') || '';
      let newUsername = fd.get('username') || '';
      
      if (newUsername && !newUsername.startsWith('@')) {
        newUsername = '@' + newUsername;
      }

      const updates = {
        display_name: newDisplayName || null,
        username: newUsername || null,
        bio: fd.get('bio') || null
      };
      
      const file = fd.get('avatar_file');
      
      const submitBtn = e.target.querySelector('[type=submit]');
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner"></span> Saving...';

      try {
        let updatedUser = await auth.updateMe(updates);
        
        if (file && file.size > 0) {
          const avatarFd = new FormData();
          avatarFd.append('avatar_file', file);
          updatedUser = await auth.uploadAvatar(avatarFd);
        }

        if (updatedUser.access_token) {
          setToken(updatedUser.access_token);
        }

        // --- HARD UI UPDATE DIRECTLY FROM FORM ---
        if (typeof _currentUser !== 'undefined' && _currentUser) {
          _currentUser.display_name = newDisplayName;
          _currentUser.username = newUsername;
          setUser(_currentUser, _currentUser.api_key);
        } else {
          setUser(updatedUser, updatedUser.api_key);
        }

        // Directly update DOM profile elements if they exist
        const pName = document.querySelector('.profile-name');
        const pHandle = document.querySelector('.profile-handle');
        if (pName) pName.textContent = newDisplayName;
        if (pHandle) pHandle.textContent = newUsername;

        closeModal('edit-profile-modal');
        showToast('Profile updated forcefully!', 'success');
        
        // Also update URL to match the new username
        if (window.location.hash.startsWith('#profile')) {
          window.location.hash = '#profile/' + encodeURIComponent(newUsername);
        }
      } catch (err) {
        showToast(err.message, 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Save Changes';
      }
    };
  }
  } catch (err) {
    console.error("Critical Boot Error:", err);
    document.querySelectorAll('.modal-overlay').forEach(el => {
      el.classList.remove('open');
      el.style.pointerEvents = 'none';
    });
  }
});
