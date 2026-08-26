// ── API Client ────────────────────────────────────────────────────────────────
// Centralised fetch wrapper that injects auth headers and handles errors.

const BASE = '';

let _token = localStorage.getItem('sg_token') || null;

export function setToken(t) {
  _token = t;
  if (t) localStorage.setItem('sg_token', t);
  else localStorage.removeItem('sg_token');
}

export function getToken() { return _token; }

export function setUserLocal(user) {
  if (user) localStorage.setItem('sg_user', JSON.stringify(user));
  else localStorage.removeItem('sg_user');
}

export function getUserLocal() {
  try { return JSON.parse(localStorage.getItem('sg_user')); }
  catch(e) { return null; }
}

async function request(method, path, body, isForm = false) {
  const headers = {};
  const token = localStorage.getItem('sg_token');
  if (token && token !== 'null' && token !== 'undefined') {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const opts = { method, headers };
  if (body && !isForm) {
    headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  } else if (isForm) {
    // FormData — let browser set Content-Type with boundary
    opts.body = body;
  }

  let res;
  let data = {};
  try {
    res = await fetch(BASE + path, opts);
  } catch (err) {
    console.error(`[Fetch Error] on ${method} ${path}:`, err);
    throw err;
  }
  
  if (res.status === 204) return null;

  try {
    data = await res.json();
  } catch (err) {
    console.warn(`[JSON Parse Error] on ${path}:`, err);
  }
  if (!res.ok) {
    let errMsg;
    if (data.detail) {
      if (Array.isArray(data.detail)) {
        errMsg = data.detail.map(e => `${e.loc ? e.loc[e.loc.length - 1] : 'field'}: ${e.msg}`).join(', ');
      } else if (typeof data.detail === 'object') {
        errMsg = JSON.stringify(data.detail);
      } else {
        errMsg = data.detail;
      }
    } else if (Object.keys(data).length > 0) {
      errMsg = JSON.stringify(data);
    } else {
      errMsg = `HTTP ${res.status}`;
    }
    
    // Globally handle 401 Unauthorized
    if (res.status === 401) {
      setToken(null);
      setUserLocal(null);
      // Dispatch a custom event so app.js can handle the UI
      window.dispatchEvent(new Event('auth:unauthorized'));
    }
    
    // Include status in error for upstream catching
    const error = new Error(errMsg);
    error.status = res.status;
    throw error;
  }
  return data;
}

// ── Auth ──────────────────────────────────────────────────────────────────────
export const auth = {
  register:       (body) => request('POST', '/api/auth/register', body),
  login:          (body) => request('POST', '/api/auth/login', body),
  me:             ()     => request('GET',  '/api/auth/me'),
  updateMe:       (body) => request('PUT',  '/api/auth/me', body),
  uploadAvatar:   (formData) => request('POST', '/api/auth/me/avatar', formData, true),
  forgotPassword: (body) => request('POST', '/api/auth/forgot-password', body),
  resetPassword:  (body) => request('POST', '/api/auth/reset-password', body),
};

// ── Robots ────────────────────────────────────────────────────────────────────
export const robots = {
  list:      (skip = 0, limit = 30) => request('GET', `/api/robots?skip=${skip}&limit=${limit}`),
  search:    (query)                => request('GET', `/api/robots/search?q=${encodeURIComponent(query)}`),
  suggested: ()                     => request('GET', `/api/robots/suggested`),
  get:       (username)             => request('GET', `/api/robots/${username}`),
  follow:    (username)             => request('POST',   `/api/robots/${username}/follow`),
  unfollow:  (username)             => request('DELETE',  `/api/robots/${username}/follow`),
};

// ── Posts ─────────────────────────────────────────────────────────────────────
export const posts = {
  feed: (skip = 0, limit = 20) => request('GET', `/api/posts?skip=${skip}&limit=${limit}`),

  forRobot: (username, skip = 0, limit = 20) =>
    request('GET', `/api/posts/robot/${username}?skip=${skip}&limit=${limit}`),

  create: (formData) => request('POST', '/api/posts', formData, true),

  like:   (id) => request('POST',   `/api/posts/${id}/like`),
  delete: (id) => request('DELETE', `/api/posts/${id}`),
};

// ── Comments ──────────────────────────────────────────────────────────────────
export const comments = {
  add:    (postId, body) => request('POST',   `/api/comments/${postId}`, { body }),
  delete: (commentId)    => request('DELETE', `/api/comments/${commentId}`),
};

export const chat = {
  getConversations: () => request('GET', '/api/chat/conversations'),
  getHistory: (userId) => request('GET', `/api/chat/history/${userId}`)
};

export const ai = {
  ask: (message) => request('POST', '/api/ai_chat', { message })
};
