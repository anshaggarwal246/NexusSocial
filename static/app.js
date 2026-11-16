/**
 * NexusSocial - Full Stack Frontend Application Logic
 */

// Application State
const state = {
  activeTab: 'feed',
  feedFilter: 'all',
  searchQuery: '',
  activeTag: '',
  currentUser: null,
  users: [],
  queries: [],
  currentQuery: null,
  posts: [],
  expandedComments: new Set()
};

// Initial App Boot
document.addEventListener('DOMContentLoaded', async () => {
  initTheme();
  await loadStats();
  await loadUsers();
  await loadCurrentUser();
  await loadFeed();
  await loadHashtags();
  await loadDbTables();
  await loadQueries();
  setupKeyboardShortcuts();
});

// --- Theme Management ---
function initTheme() {
  const saved = localStorage.getItem('nexus_theme');
  if (saved === 'light') {
    document.body.classList.remove('dark-theme');
    document.body.classList.add('light-theme');
  }
}

function toggleTheme() {
  const isLight = document.body.classList.toggle('light-theme');
  document.body.classList.toggle('dark-theme', !isLight);
  localStorage.setItem('nexus_theme', isLight ? 'light' : 'dark');
}

// --- Navigation & Tabs ---
function switchTab(tabId) {
  state.activeTab = tabId;
  document.querySelectorAll('.sidebar-nav .nav-item').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabId);
  });
  document.querySelectorAll('.tab-pane').forEach(pane => {
    pane.classList.toggle('active', pane.id === `tab-${tabId}`);
  });

  if (tabId === 'users' && state.users.length === 0) loadUsers();
  if (tabId === 'hashtags') loadHashtags();
  if (tabId === 'tables') loadDbTables();
  if (tabId === 'analytics' && state.queries.length === 0) loadQueries();
}

// --- Toast Notifications ---
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// --- Helpers: Avatars & Media ---
function getInitials(name) {
  if (!name) return 'U';
  return name.trim().split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
}

function renderAvatar(photoUrl, name, size = 44) {
  const initials = getInitials(name);
  const isValidUrl = photoUrl && (photoUrl.startsWith('http://') || photoUrl.startsWith('https://'));
  if (isValidUrl) {
    return `
      <div class="avatar" style="width: ${size}px; height: ${size}px;">
        <img src="${photoUrl}" alt="${name}" onerror="this.onerror=null; this.parentElement.innerHTML='${initials}'">
      </div>
    `;
  }
  return `
    <div class="avatar" style="width: ${size}px; height: ${size}px;">
      ${initials}
    </div>
  `;
}

function formatYoutubeEmbed(url) {
  if (!url) return null;
  const match = url.match(/(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([\w-]{11})/);
  if (match && match[1]) {
    return `https://www.youtube-nocookie.com/embed/${match[1]}`;
  }
  return null;
}

// --- Data Fetching ---

async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    if (data.success && data.stats) {
      document.getElementById('stat-users').innerText = (data.stats.users || 0).toLocaleString();
      document.getElementById('stat-posts').innerText = (data.stats.post || 0).toLocaleString();
      document.getElementById('stat-comments').innerText = (data.stats.comments || 0).toLocaleString();
      document.getElementById('stat-likes').innerText = (data.stats.post_likes || 0).toLocaleString();
    }
  } catch (err) {
    console.error('Failed to load stats', err);
  }
}

async function loadUsers() {
  try {
    const res = await fetch('/api/users?limit=60');
    const data = await res.json();
    if (data.success) {
      state.users = data.users;
      renderUsersSwitcher(data.users);
      renderUsersGrid(data.users);
    }
  } catch (err) {
    console.error('Failed to load users', err);
  }
}

async function loadCurrentUser() {
  try {
    const res = await fetch('/api/current-user');
    const data = await res.json();
    if (data.success && data.user) {
      state.currentUser = data.user;
      const select = document.getElementById('current-user-select');
      if (select) select.value = data.user.user_id;
      const avatarBox = document.getElementById('active-avatar-preview');
      if (avatarBox) {
        avatarBox.innerHTML = renderAvatar(data.user.profile_photo_url, data.user.username, 30);
      }
    }
  } catch (err) {
    console.error('Failed to load active user', err);
  }
}

async function switchCurrentUser(userId) {
  try {
    const res = await fetch('/api/current-user', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: parseInt(userId) })
    });
    const data = await res.json();
    if (data.success) {
      state.currentUser = data.user;
      showToast(`Switched active user to @${data.user.username}`, 'success');
      const avatarBox = document.getElementById('active-avatar-preview');
      if (avatarBox) {
        avatarBox.innerHTML = renderAvatar(data.user.profile_photo_url, data.user.username, 30);
      }
      loadFeed();
      loadUsers();
    }
  } catch (err) {
    showToast('Failed to switch user', 'error');
  }
}

function renderUsersSwitcher(users) {
  const select = document.getElementById('current-user-select');
  if (!select) return;
  select.innerHTML = users.map(u => `
    <option value="${u.user_id}">${u.username}</option>
  `).join('');
  if (state.currentUser) {
    select.value = state.currentUser.user_id;
  }
}

// --- Feed & Posts ---

async function loadFeed() {
  const container = document.getElementById('feed-posts-container');
  container.innerHTML = `
    <div class="loading-state">
      <div class="spinner"></div>
      <p>Fetching social media database feed...</p>
    </div>
  `;

  try {
    const params = new URLSearchParams({
      filter: state.feedFilter,
      search: state.searchQuery,
      tag: state.activeTag,
      limit: 30
    });
    const res = await fetch(`/api/feed?${params.toString()}`);
    const data = await res.json();

    if (data.success) {
      state.posts = data.posts;
      renderFeed(data.posts);
    } else {
      container.innerHTML = `<div class="loading-state"><p>Error loading feed: ${data.error}</p></div>`;
    }
  } catch (err) {
    container.innerHTML = `<div class="loading-state"><p>Connection error loading feed.</p></div>`;
  }
}

function setFeedFilter(filter) {
  state.feedFilter = filter;
  state.activeTag = '';
  document.querySelectorAll('.filter-chips .chip').forEach(c => {
    c.classList.toggle('active', c.dataset.filter === filter);
  });
  updateFilterIndicator();
  loadFeed();
}

function handleSearch(val) {
  state.searchQuery = val.trim();
  const clearBtn = document.getElementById('search-clear');
  if (clearBtn) clearBtn.style.display = state.searchQuery ? 'block' : 'none';
  clearTimeout(window._searchTimer);
  window._searchTimer = setTimeout(() => {
    loadFeed();
  }, 350);
}

function clearSearch() {
  document.getElementById('global-search').value = '';
  state.searchQuery = '';
  document.getElementById('search-clear').style.display = 'none';
  loadFeed();
}

function filterByTag(tagName) {
  state.activeTag = tagName.replace('#', '').trim();
  switchTab('feed');
  updateFilterIndicator();
  loadFeed();
}

function updateFilterIndicator() {
  const ind = document.getElementById('filter-indicator-text');
  if (state.activeTag) {
    ind.innerHTML = `Filtering by tag: <strong>#${state.activeTag}</strong> <a href="#" onclick="clearTagFilter(event)" style="color:var(--danger); margin-left:6px;">&times; Clear</a>`;
  } else if (state.searchQuery) {
    ind.innerHTML = `Search: "${state.searchQuery}"`;
  } else {
    ind.innerHTML = '';
  }
}

function clearTagFilter(e) {
  e.preventDefault();
  state.activeTag = '';
  updateFilterIndicator();
  loadFeed();
}

function renderFeed(posts) {
  const container = document.getElementById('feed-posts-container');
  if (!posts || posts.length === 0) {
    container.innerHTML = `
      <div class="loading-state">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="8" y1="12" x2="16" y2="12"></line>
        </svg>
        <p>No posts match the current filter or search criteria.</p>
        <button class="secondary-btn btn-sm" onclick="setFeedFilter('all')">Reset to All Posts</button>
      </div>
    `;
    return;
  }

  container.innerHTML = posts.map(post => {
    const isLiked = post.has_liked === 1;
    const isBookmarked = post.has_bookmarked === 1;
    const ytEmbed = formatYoutubeEmbed(post.video_url);

    // Media rendering
    let mediaHtml = '';
    if (ytEmbed) {
      mediaHtml = `
        <div class="video-container">
          <iframe src="${ytEmbed}" title="Post video" allowfullscreen loading="lazy"></iframe>
        </div>
      `;
    } else if (post.photo_url) {
      mediaHtml = `
        <div class="post-media-wrap" ondblclick="handleDoubleTapLike(${post.post_id})">
          <img class="post-img" src="${post.photo_url}" alt="Post image" loading="lazy" onerror="this.onerror=null; this.src='https://picsum.photos/seed/${post.post_id}/600/400';">
        </div>
      `;
    }

    // Hashtags
    const tagsHtml = (post.tags || []).map(t => `
      <span class="tag-pill" onclick="filterByTag('${t.hashtag_name}')">${t.hashtag_name}</span>
    `).join('');

    return `
      <article class="post-card" id="post-${post.post_id}">
        <div class="post-header">
          <div class="post-user-info" onclick="openUserProfileModal(${post.user_id})">
            ${renderAvatar(post.profile_photo_url, post.username)}
            <div class="user-meta">
              <span class="post-username">${escapeHtml(post.username)}</span>
              <span class="post-location">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                ${escapeHtml(post.location || 'Everywhere')}
              </span>
            </div>
          </div>
          <span class="post-time">${formatDate(post.created_at)}</span>
        </div>

        ${mediaHtml}

        <div class="post-body">
          <div class="post-actions-bar">
            <div class="actions-left">
              <button class="action-btn ${isLiked ? 'liked' : ''}" id="like-btn-${post.post_id}" onclick="toggleLikePost(${post.post_id})">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
                <span id="likes-count-${post.post_id}">${post.likes_count}</span>
              </button>
              <button class="action-btn" onclick="toggleComments(${post.post_id})">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
                <span id="comments-count-${post.post_id}">${post.comments_count}</span>
              </button>
              <button class="action-btn" onclick="copyPostLink(${post.post_id})" title="Share Post">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>
              </button>
            </div>
            <button class="action-btn ${isBookmarked ? 'bookmarked' : ''}" id="bookmark-btn-${post.post_id}" onclick="toggleBookmarkPost(${post.post_id})">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path></svg>
            </button>
          </div>

          <div class="post-caption">${highlightHashtags(escapeHtml(post.caption || ''))}</div>

          ${tagsHtml ? `<div class="post-tags-row">${tagsHtml}</div>` : ''}
        </div>

        <div class="comments-section" id="comments-section-${post.post_id}" style="display: none;">
          <div class="comments-list" id="comments-list-${post.post_id}">
            <div class="loading-state" style="padding:1rem 0;"><div class="spinner" style="width:20px;height:20px;"></div></div>
          </div>
          <form class="comment-input-box" onsubmit="handleAddCommentSubmit(event, ${post.post_id})">
            <input type="text" id="comment-input-${post.post_id}" placeholder="Write a comment..." required>
            <button type="submit" class="comment-send-btn" title="Post Comment">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
            </button>
          </form>
        </div>
      </article>
    `;
  }).join('');
}

// --- Like / Bookmark Interactivity ---

async function toggleLikePost(postId) {
  const btn = document.getElementById(`like-btn-${postId}`);
  const countSpan = document.getElementById(`likes-count-${postId}`);
  const isCurrentlyLiked = btn.classList.contains('liked');

  // Optimistic UI
  btn.classList.toggle('liked', !isCurrentlyLiked);
  let currentCount = parseInt(countSpan.innerText) || 0;
  countSpan.innerText = isCurrentlyLiked ? Math.max(0, currentCount - 1) : currentCount + 1;

  try {
    const res = await fetch(`/api/posts/${postId}/like`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      btn.classList.toggle('liked', data.liked);
      countSpan.innerText = data.likes_count;
      loadStats();
    }
  } catch (err) {
    // Revert on error
    btn.classList.toggle('liked', isCurrentlyLiked);
    countSpan.innerText = currentCount;
    showToast('Failed to update like status', 'error');
  }
}

function handleDoubleTapLike(postId) {
  const card = document.getElementById(`post-${postId}`);
  const mediaWrap = card.querySelector('.post-media-wrap');
  if (mediaWrap) {
    const heart = document.createElement('div');
    heart.className = 'floating-heart';
    heart.innerHTML = '❤️';
    mediaWrap.appendChild(heart);
    setTimeout(() => heart.remove(), 800);
  }
  const btn = document.getElementById(`like-btn-${postId}`);
  if (!btn.classList.contains('liked')) {
    toggleLikePost(postId);
  }
}

async function toggleBookmarkPost(postId) {
  const btn = document.getElementById(`bookmark-btn-${postId}`);
  const isBookmarked = btn.classList.contains('bookmarked');

  btn.classList.toggle('bookmarked', !isBookmarked);

  try {
    const res = await fetch(`/api/posts/${postId}/bookmark`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      btn.classList.toggle('bookmarked', data.bookmarked);
      showToast(data.bookmarked ? 'Saved to bookmarks' : 'Removed from bookmarks', 'success');
      loadStats();
    }
  } catch (err) {
    btn.classList.toggle('bookmarked', isBookmarked);
    showToast('Failed to update bookmark', 'error');
  }
}

function copyPostLink(postId) {
  const url = `${window.location.origin}/#post-${postId}`;
  navigator.clipboard.writeText(url).then(() => {
    showToast('Post link copied to clipboard!', 'success');
  }).catch(() => {
    showToast('Link copied: ' + url, 'info');
  });
}

// --- Comments Drawer ---

async function toggleComments(postId) {
  const section = document.getElementById(`comments-section-${postId}`);
  const isHidden = section.style.display === 'none';

  if (isHidden) {
    section.style.display = 'block';
    state.expandedComments.add(postId);
    await loadComments(postId);
  } else {
    section.style.display = 'none';
    state.expandedComments.delete(postId);
  }
}

async function loadComments(postId) {
  const list = document.getElementById(`comments-list-${postId}`);
  try {
    const res = await fetch(`/api/posts/${postId}/comments`);
    const data = await res.json();
    if (data.success) {
      if (data.comments.length === 0) {
        list.innerHTML = `<div style="color:var(--text-muted);font-size:0.8rem;text-align:center;padding:0.5rem;">No comments yet. Be the first to comment!</div>`;
        return;
      }
      list.innerHTML = data.comments.map(c => `
        <div class="comment-item" id="comment-${c.comment_id}">
          <div class="comment-main">
            ${renderAvatar(c.profile_photo_url, c.username, 26)}
            <div class="comment-text-wrap">
              <span class="comment-author">${escapeHtml(c.username)}</span>
              <span class="comment-body">${escapeHtml(c.comment_text)}</span>
            </div>
          </div>
          <button class="comment-like-btn ${c.has_liked ? 'liked' : ''}" onclick="toggleLikeComment(${c.comment_id})">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="${c.has_liked ? '#f43f5e' : 'none'}" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
            <span>${c.likes_count || 0}</span>
          </button>
        </div>
      `).join('');
    }
  } catch (err) {
    list.innerHTML = `<div style="color:var(--danger);font-size:0.8rem;">Failed to load comments</div>`;
  }
}

async function handleAddCommentSubmit(e, postId) {
  e.preventDefault();
  const input = document.getElementById(`comment-input-${postId}`);
  const text = input.value.trim();
  if (!text) return;

  try {
    const res = await fetch(`/api/posts/${postId}/comments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ comment_text: text })
    });
    const data = await res.json();
    if (data.success) {
      input.value = '';
      const countSpan = document.getElementById(`comments-count-${postId}`);
      if (countSpan) countSpan.innerText = (parseInt(countSpan.innerText) || 0) + 1;
      await loadComments(postId);
      loadStats();
      showToast('Comment published!', 'success');
    } else {
      showToast(data.error || 'Failed to add comment', 'error');
    }
  } catch (err) {
    showToast('Failed to send comment', 'error');
  }
}

async function toggleLikeComment(commentId) {
  try {
    const res = await fetch(`/api/comments/${commentId}/like`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      const item = document.getElementById(`comment-${commentId}`);
      if (item) {
        const btn = item.querySelector('.comment-like-btn');
        btn.classList.toggle('liked', data.liked);
        btn.querySelector('span').innerText = data.likes_count;
        const svg = btn.querySelector('svg');
        svg.setAttribute('fill', data.liked ? '#f43f5e' : 'none');
      }
    }
  } catch (err) {
    showToast('Failed to like comment', 'error');
  }
}

// --- Creators Grid ---

function renderUsersGrid(users) {
  const grid = document.getElementById('users-grid');
  if (!grid) return;
  grid.innerHTML = users.map(u => `
    <div class="user-card">
      <div class="user-card-avatar" onclick="openUserProfileModal(${u.user_id})" style="cursor:pointer;">
        ${renderAvatar(u.profile_photo_url, u.username, 72)}
      </div>
      <h3 class="user-card-name">${escapeHtml(u.username)}</h3>
      <span class="user-card-email">${escapeHtml(u.email || '')}</span>
      <p class="user-card-bio">${escapeHtml(u.bio || 'Social media enthusiast & digital creator')}</p>
      <div class="user-card-stats">
        <div class="user-stat">
          <span class="user-stat-val">${u.post_count || 0}</span>
          <span class="user-stat-lbl">Posts</span>
        </div>
        <div class="user-stat">
          <span class="user-stat-val" id="user-followers-${u.user_id}">${u.follower_count || 0}</span>
          <span class="user-stat-lbl">Followers</span>
        </div>
        <div class="user-stat">
          <span class="user-stat-val">${u.following_count || 0}</span>
          <span class="user-stat-lbl">Following</span>
        </div>
      </div>
      <div class="user-card-actions">
        <button class="secondary-btn btn-sm" onclick="openUserProfileModal(${u.user_id})">View Profile</button>
        <button class="primary-btn btn-sm" id="follow-btn-${u.user_id}" onclick="toggleFollowUser(${u.user_id})">Follow</button>
      </div>
    </div>
  `).join('');
}

async function toggleFollowUser(targetUserId) {
  const btn = document.getElementById(`follow-btn-${targetUserId}`);
  try {
    const res = await fetch(`/api/users/${targetUserId}/follow`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      if (btn) btn.innerText = data.following ? 'Unfollow' : 'Follow';
      const followerSpan = document.getElementById(`user-followers-${targetUserId}`);
      if (followerSpan) followerSpan.innerText = data.follower_count;
      showToast(data.following ? 'Followed creator!' : 'Unfollowed', 'success');
      loadStats();
    } else {
      showToast(data.error || 'Follow action failed', 'error');
    }
  } catch (err) {
    showToast('Failed to update follow status', 'error');
  }
}

async function openUserProfileModal(userId) {
  const modal = document.getElementById('user-profile-modal');
  const body = document.getElementById('user-profile-body');
  body.innerHTML = `<div class="loading-state"><div class="spinner"></div><p>Loading creator profile...</p></div>`;
  modal.style.display = 'flex';

  try {
    const res = await fetch(`/api/users/${userId}`);
    const data = await res.json();
    if (data.success) {
      const u = data.user;
      const posts = data.posts || [];
      body.innerHTML = `
        <div style="display:flex; gap:1.5rem; align-items:center; margin-bottom:1.5rem;">
          ${renderAvatar(u.profile_photo_url, u.username, 80)}
          <div>
            <h2 style="font-size:1.4rem; font-weight:800;">${escapeHtml(u.username)}</h2>
            <p style="color:var(--text-muted); font-size:0.85rem;">${escapeHtml(u.email)} • Joined ${formatDate(u.created_at)}</p>
            <p style="color:var(--text-secondary); margin-top:0.4rem; font-size:0.95rem;">${escapeHtml(u.bio || 'No bio provided.')}</p>
            <div style="display:flex; gap:1.5rem; margin-top:0.75rem;">
              <span><strong>${u.post_count || 0}</strong> <small style="color:var(--text-muted)">Posts</small></span>
              <span><strong>${u.follower_count || 0}</strong> <small style="color:var(--text-muted)">Followers</small></span>
              <span><strong>${u.following_count || 0}</strong> <small style="color:var(--text-muted)">Following</small></span>
            </div>
          </div>
        </div>
        <h3 style="font-size:1.1rem; font-weight:700; margin-bottom:0.75rem; border-top:1px solid var(--card-border); padding-top:1rem;">Posts by @${escapeHtml(u.username)} (${posts.length})</h3>
        <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(180px, 1fr)); gap:0.75rem; max-height:350px; overflow-y:auto;">
          ${posts.length ? posts.map(p => `
            <div style="background:var(--bg-primary); border:1px solid var(--card-border); border-radius:var(--radius-md); padding:0.75rem;">
              ${p.photo_url ? `<img src="${p.photo_url}" style="width:100%; height:100px; object-fit:cover; border-radius:6px; margin-bottom:0.4rem;" onerror="this.src='https://picsum.photos/seed/${p.post_id}/200/150'">` : ''}
              <p style="font-size:0.8rem; line-height:1.3; margin-bottom:0.4rem;">${escapeHtml(p.caption || '')}</p>
              <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:var(--text-muted);">
                <span>❤️ ${p.likes_count}</span>
                <span>💬 ${p.comments_count}</span>
              </div>
            </div>
          `).join('') : '<p style="color:var(--text-muted); font-size:0.85rem;">No posts published yet.</p>'}
        </div>
      `;
    }
  } catch (err) {
    body.innerHTML = `<p style="color:var(--danger)">Failed to load profile.</p>`;
  }
}

// --- Trending Hashtags ---

async function loadHashtags() {
  const grid = document.getElementById('hashtags-grid');
  if (!grid) return;
  grid.innerHTML = `<div class="loading-state"><div class="spinner"></div><p>Loading hashtags...</p></div>`;

  try {
    const res = await fetch('/api/hashtags');
    const data = await res.json();
    if (data.success) {
      grid.innerHTML = data.hashtags.map(h => `
        <div class="hashtag-card">
          <div class="hashtag-info" onclick="filterByTag('${h.hashtag_name}')">
            <span class="hashtag-name">${escapeHtml(h.hashtag_name)}</span>
            <span class="hashtag-meta">${h.post_count} posts • ${h.follow_count} followers</span>
          </div>
          <button class="secondary-btn btn-sm" onclick="toggleFollowHashtag(${h.hashtag_id})">Follow</button>
        </div>
      `).join('');
    }
  } catch (err) {
    grid.innerHTML = `<p style="color:var(--danger)">Failed to load hashtags</p>`;
  }
}

async function toggleFollowHashtag(tagId) {
  try {
    const res = await fetch(`/api/hashtags/${tagId}/follow`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      showToast(data.following ? 'Hashtag followed!' : 'Unfollowed hashtag', 'success');
      loadHashtags();
    }
  } catch (err) {
    showToast('Failed to update hashtag follow', 'error');
  }
}

// --- TAB: DATABASE TABLES EXPLORER ---

let currentExplorerTable = 'users';
let currentExplorerOffset = 0;
const explorerLimit = 50;

async function loadDbTables() {
  const list = document.getElementById('tables-sidebar-list');
  if (!list) return;

  function renderTablesList(tables) {
    const badge = document.getElementById('tables-badge-count');
    if (badge) badge.innerText = tables.length;
    list.innerHTML = tables.map(t => `
      <div class="table-sidebar-item ${t.table_name === currentExplorerTable ? 'active' : ''}" 
           id="table-item-${t.table_name}"
           onclick="showTableData('${t.table_name}', 0)">
        <span class="table-sidebar-name">${escapeHtml(t.table_name)}</span>
        <span class="table-sidebar-badge">${t.row_count !== '' ? t.row_count.toLocaleString() : 'view'}</span>
      </div>
    `).join('');
    showTableData(currentExplorerTable, currentExplorerOffset);
  }

  try {
    const res = await fetch('/api/db/tables');
    if (res.ok) {
      const data = await res.json();
      if (data.success && data.tables) {
        renderTablesList(data.tables);
        return;
      }
    }
  } catch (err) {}

  // Fallback via /api/query
  try {
    const qRes = await fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sql: "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;" })
    });
    const qData = await qRes.json();
    if (qData.success) {
      const tables = qData.result.rows.map(r => ({ table_name: r.name, row_count: '' }));
      renderTablesList(tables);
    }
  } catch (e) {}
}

async function showTableData(tableName, offset = 0) {
  currentExplorerTable = tableName;
  currentExplorerOffset = offset;

  document.querySelectorAll('.table-sidebar-item').forEach(el => el.classList.remove('active'));
  const activeEl = document.getElementById(`table-item-${tableName}`);
  if (activeEl) activeEl.classList.add('active');

  const title = document.getElementById('table-viewer-title');
  const subtitle = document.getElementById('table-viewer-subtitle');
  const pagination = document.getElementById('table-viewer-pagination');
  const gridWrap = document.getElementById('table-grid-wrap');

  gridWrap.innerHTML = `<div class="loading-state"><div class="spinner"></div><p>Fetching records from table <code>${tableName}</code>...</p></div>`;

  let data = null;
  try {
    const res = await fetch(`/api/db/table/${tableName}?limit=${explorerLimit}&offset=${offset}`);
    if (res.ok) {
      data = await res.json();
    }
  } catch (err) {}

  // Fallback to /api/query (handles un-restarted servers automatically)
  if (!data || !data.success) {
    try {
      const countRes = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sql: `SELECT COUNT(*) AS total FROM ${tableName};` })
      });
      const countData = await countRes.json();
      const total = countData.success && countData.result.rows.length ? Object.values(countData.result.rows[0])[0] : 0;

      const qRes = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sql: `SELECT * FROM ${tableName} LIMIT ${explorerLimit} OFFSET ${offset};` })
      });
      const qData = await qRes.json();
      if (qData.success) {
        data = {
          success: true,
          columns: qData.result.columns,
          rows: qData.result.rows,
          total_count: total
        };
      }
    } catch (e) {
      console.error(e);
    }
  }

  if (data && data.success) {
    const start = offset + 1;
    const end = Math.min(offset + explorerLimit, data.total_count);
    title.innerText = `Table: ${tableName}`;
    subtitle.innerText = `Showing records ${data.total_count > 0 ? start : 0} to ${end} of ${data.total_count.toLocaleString()}`;

    // Pagination
    const hasPrev = offset > 0;
    const hasNext = offset + explorerLimit < data.total_count;

    pagination.innerHTML = `
      <button class="secondary-btn btn-sm" ${!hasPrev ? 'disabled style="opacity:0.4;cursor:not-allowed;"' : ''} 
              onclick="showTableData('${tableName}', ${Math.max(0, offset - explorerLimit)})">
        &larr; Prev
      </button>
      <span style="font-size:0.8rem; color:var(--text-muted); padding: 0 0.5rem;">
        Page ${Math.floor(offset / explorerLimit) + 1} of ${Math.ceil(data.total_count / explorerLimit) || 1}
      </span>
      <button class="secondary-btn btn-sm" ${!hasNext ? 'disabled style="opacity:0.4;cursor:not-allowed;"' : ''} 
              onclick="showTableData('${tableName}', ${offset + explorerLimit})">
        Next &rarr;
      </button>
    `;

    gridWrap.innerHTML = renderTableHtml(data.columns, data.rows);
  } else {
    gridWrap.innerHTML = `<div class="loading-state"><p style="color:var(--danger)">Could not load table data. Please restart <code>run.bat</code> and refresh!</p></div>`;
  }
}

// --- TAB 4: DBMS ANALYTICS & 16 QUERIES ---

async function loadQueries() {
  try {
    const res = await fetch('/api/analytics');
    const data = await res.json();
    if (data.success) {
      state.queries = data.queries;
      renderAnalyticsMetrics(data.stats);
      renderQueriesList(data.queries);
      // Auto-run first query by default
      if (data.queries.length > 0) {
        runQueryById(data.queries[0].id);
      }
    }
  } catch (err) {
    console.error('Failed to load analytics', err);
  }
}

function renderAnalyticsMetrics(stats) {
  const row = document.getElementById('analytics-metrics-row');
  if (!row || !stats) return;
  row.innerHTML = `
    <div class="metric-card"><span class="metric-card-val">${(stats.users || 0).toLocaleString()}</span><span class="metric-card-lbl">Total Users</span></div>
    <div class="metric-card"><span class="metric-card-val">${(stats.post || 0).toLocaleString()}</span><span class="metric-card-lbl">Published Posts</span></div>
    <div class="metric-card"><span class="metric-card-val">${(stats.comments || 0).toLocaleString()}</span><span class="metric-card-lbl">User Comments</span></div>
    <div class="metric-card"><span class="metric-card-val">${(stats.post_likes || 0).toLocaleString()}</span><span class="metric-card-lbl">Post Likes</span></div>
    <div class="metric-card"><span class="metric-card-val">${(stats.follows || 0).toLocaleString()}</span><span class="metric-card-lbl">Follow Relations</span></div>
    <div class="metric-card"><span class="metric-card-val">${(stats.hashtags || 0).toLocaleString()}</span><span class="metric-card-lbl">Hashtags</span></div>
  `;
}

function renderQueriesList(queries) {
  const list = document.getElementById('queries-list');
  if (!list) return;
  list.innerHTML = queries.map(q => `
    <div class="query-item" id="query-item-${q.id}" onclick="runQueryById(${q.id})">
      <div class="query-item-head">
        <span class="query-num">Query #${q.id}</span>
      </div>
      <div class="query-item-title">${escapeHtml(q.title)}</div>
      <div class="query-item-desc">${escapeHtml(q.description)}</div>
    </div>
  `).join('');
}

async function runQueryById(qid) {
  document.querySelectorAll('.query-item').forEach(el => el.classList.remove('active'));
  const activeEl = document.getElementById(`query-item-${qid}`);
  if (activeEl) activeEl.classList.add('active');

  const placeholder = document.getElementById('viewer-placeholder');
  const content = document.getElementById('viewer-content');
  const tableWrap = document.getElementById('view-table-wrap');

  placeholder.style.display = 'none';
  content.style.display = 'block';
  tableWrap.innerHTML = `<div class="loading-state"><div class="spinner"></div><p>Executing Query #${qid}...</p></div>`;

  try {
    const res = await fetch(`/api/analytics/run/${qid}`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      state.currentQuery = data.query;
      document.getElementById('view-query-title').innerText = `#${data.query.id}. ${data.query.title}`;
      document.getElementById('view-query-desc').innerText = data.query.description;
      document.getElementById('view-perf-badge').innerText = `⚡ ${data.result.execution_time_ms} ms (${data.result.count} rows)`;
      document.getElementById('view-query-sql').innerText = data.query.sql;

      renderTable(tableWrap, data.result.columns, data.result.rows);
    } else {
      tableWrap.innerHTML = `<p style="color:var(--danger)">Error: ${data.error}</p>`;
    }
  } catch (err) {
    tableWrap.innerHTML = `<p style="color:var(--danger)">Execution failed.</p>`;
  }
}

function copyCurrentSQL() {
  if (state.currentQuery && state.currentQuery.sql) {
    navigator.clipboard.writeText(state.currentQuery.sql).then(() => {
      showToast('SQL query copied to clipboard!', 'success');
    });
  }
}

async function runAllQueriesSequentially() {
  showToast('Benchmarking all 16 queries against SQLite...', 'info');
  let totalTime = 0;
  for (const q of state.queries) {
    const start = performance.now();
    await fetch(`/api/analytics/run/${q.id}`, { method: 'POST' });
    totalTime += (performance.now() - start);
  }
  showToast(`All 16 queries executed in ${totalTime.toFixed(1)} ms!`, 'success');
}

// --- TAB 5: INTERACTIVE SQL CONSOLE ---

function applySqlPreset(val) {
  if (val) {
    document.getElementById('custom-sql-input').value = val;
  }
}

async function executeCustomSql() {
  const sql = document.getElementById('custom-sql-input').value.trim();
  const resultsBox = document.getElementById('console-results');
  if (!sql) {
    showToast('Please type a SQL query', 'error');
    return;
  }

  resultsBox.innerHTML = `<div class="loading-state"><div class="spinner"></div><p>Executing query...</p></div>`;

  try {
    const res = await fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sql })
    });
    const data = await res.json();

    if (data.success) {
      const { columns, rows, count, execution_time_ms } = data.result;
      resultsBox.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
          <span style="font-weight:700; font-size:0.9rem;">Returned ${count} rows</span>
          <span class="perf-badge">⚡ ${execution_time_ms} ms</span>
        </div>
        <div class="results-table-wrap">
          ${renderTableHtml(columns, rows)}
        </div>
      `;
    } else {
      resultsBox.innerHTML = `
        <div style="background:rgba(239, 68, 68, 0.1); border:1px solid var(--danger); border-radius:var(--radius-md); padding:1rem; color:var(--danger);">
          <strong>SQL Error:</strong> ${escapeHtml(data.error)}
        </div>
      `;
    }
  } catch (err) {
    resultsBox.innerHTML = `<p style="color:var(--danger)">Network or execution error.</p>`;
  }
}

function renderTable(container, columns, rows) {
  container.innerHTML = renderTableHtml(columns, rows);
}

function renderTableHtml(columns, rows) {
  if (!columns || columns.length === 0) {
    return `<div style="padding:1.5rem; text-align:center; color:var(--text-muted);">Query executed successfully with 0 columns returned.</div>`;
  }
  if (!rows || rows.length === 0) {
    return `
      <table class="sql-table">
        <thead><tr>${columns.map(c => `<th>${escapeHtml(c)}</th>`).join('')}</tr></thead>
        <tbody><tr><td colspan="${columns.length}" style="text-align:center; color:var(--text-muted); padding:2rem;">0 rows matching criteria.</td></tr></tbody>
      </table>
    `;
  }

  return `
    <table class="sql-table">
      <thead>
        <tr>${columns.map(c => `<th>${escapeHtml(c)}</th>`).join('')}</tr>
      </thead>
      <tbody>
        ${rows.map(row => `
          <tr>${columns.map(c => `<td>${escapeHtml(String(row[c] !== null && row[c] !== undefined ? row[c] : 'NULL'))}</td>`).join('')}</tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

// --- Create Post & Create User Modals ---

function openCreatePostModal() {
  document.getElementById('create-post-modal').style.display = 'flex';
}

function openCreateUserModal() {
  document.getElementById('create-user-modal').style.display = 'flex';
}

function closeModal(id) {
  document.getElementById(id).style.display = 'none';
}

function closeModalOnBackdrop(e, id) {
  if (e.target.id === id) {
    closeModal(id);
  }
}

async function handleCreatePostSubmit(e) {
  e.preventDefault();
  const caption = document.getElementById('post-caption').value.trim();
  const location = document.getElementById('post-location').value.trim();
  const photoUrl = document.getElementById('post-photo-url').value.trim();
  const videoUrl = document.getElementById('post-video-url').value.trim();
  const rawTags = document.getElementById('post-tags').value.trim();

  const tags = rawTags ? rawTags.split(',').map(t => t.trim()).filter(Boolean) : [];

  try {
    const res = await fetch('/api/posts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        caption,
        location,
        photo_url: photoUrl,
        video_url: videoUrl,
        tags,
        user_id: state.currentUser ? state.currentUser.user_id : 1
      })
    });
    const data = await res.json();
    if (data.success) {
      closeModal('create-post-modal');
      document.getElementById('create-post-form').reset();
      showToast('New post published to database!', 'success');
      switchTab('feed');
      loadFeed();
      loadStats();
    } else {
      showToast(data.error || 'Failed to publish post', 'error');
    }
  } catch (err) {
    showToast('Failed to create post', 'error');
  }
}

async function handleCreateUserSubmit(e) {
  e.preventDefault();
  const username = document.getElementById('user-username').value.trim();
  const email = document.getElementById('user-email').value.trim();
  const bio = document.getElementById('user-bio').value.trim();
  const photoUrl = document.getElementById('user-photo-url').value.trim();

  try {
    const res = await fetch('/api/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, bio, profile_photo_url: photoUrl })
    });
    const data = await res.json();
    if (data.success) {
      closeModal('create-user-modal');
      document.getElementById('create-user-form').reset();
      showToast(`User @${data.user.username} registered!`, 'success');
      loadUsers();
      loadStats();
    } else {
      showToast(data.error || 'Failed to create user', 'error');
    }
  } catch (err) {
    showToast('Failed to register user', 'error');
  }
}

// --- Keyboard Shortcuts & Utilities ---

function setupKeyboardShortcuts() {
  const sqlInput = document.getElementById('custom-sql-input');
  if (sqlInput) {
    sqlInput.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        executeCustomSql();
      }
    });
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeModal('create-post-modal');
      closeModal('create-user-modal');
      closeModal('user-profile-modal');
    }
  });
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function highlightHashtags(text) {
  if (!text) return '';
  return text.replace(/(#[a-zA-Z0-9_]+)/g, '<span class="tag-pill" onclick="filterByTag(\'$1\')">$1</span>');
}

function formatDate(dateStr) {
  if (!dateStr) return 'Recently';
  try {
    const d = new Date(dateStr.replace(' ', 'T'));
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  } catch {
    return dateStr;
  }
}
