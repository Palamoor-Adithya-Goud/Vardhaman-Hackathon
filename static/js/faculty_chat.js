/**
 * faculty_chat.js — Direct Student ↔ Faculty Chat Controller
 * Students pick a faculty member and send messages.
 * Faculty see an inbox of all conversations directed to them.
 * Messages sync via backend API (Supabase/local DB).
 */

import { getRole } from './auth.js';
import { toast } from './toast.js';
import { getInitials, stringToColor } from './utils.js';

// ── Faculty Seed Data (mirrors faculty.js) ──
const FACULTY_MEMBERS = [
  {
    name: 'Dr. Padmaja',
    domain: 'Agriculture AI / Computer Vision',
    dept: 'Computer Science & Engineering'
  },
  {
    name: 'Dr. Venkateshwara',
    domain: 'Machine Learning / Feature Engineering',
    dept: 'Computer Science & Engineering'
  },
  {
    name: 'Dr. Madhurya',
    domain: 'IoT / Networking Protocols',
    dept: 'Information Technology'
  },
  {
    name: 'Dr. Gagandeep',
    domain: 'IoT / Healthcare Tech',
    dept: 'Electronics & Communication'
  },
  {
    name: 'Dr. Vasantha',
    domain: 'Network Infrastructure Energy',
    dept: 'Information Technology'
  },
  {
    name: 'Prof. Srinivas Gongula',
    domain: 'Big Data / Accident Detection',
    dept: 'Computer Science & Engineering'
  },
  {
    name: 'Dr. Ravikumar',
    domain: 'IPv6 Network Protocols',
    dept: 'Electronics & Communication'
  },
  {
    name: 'Prof. Manzoor',
    domain: 'Generative Models / CNN',
    dept: 'Computer Science & Engineering'
  }
];

// ── State ──
let selectedFaculty = null;
let currentMessages = [];
let pollingInterval = null;
let userRole = 'student';

// ── DOM ──
const listContainer  = document.getElementById('fc-list-container');
const searchInput    = document.getElementById('fc-search');
const sidebarTitle   = document.getElementById('fc-sidebar-title');
const activeName     = document.getElementById('fc-active-name');
const activeDomain   = document.getElementById('fc-active-domain');
const activeAvatar   = document.getElementById('fc-active-avatar');
const usernameInput  = document.getElementById('fc-username');
const messagesArea   = document.getElementById('fc-messages-container');
const chatInput      = document.getElementById('fc-chat-input');
const sendBtn        = document.getElementById('fc-send-btn');
const syncIndicator  = document.getElementById('fc-sync-indicator');
const modeBadge      = document.getElementById('fc-mode-badge');
const emptyDesc      = document.getElementById('fc-empty-desc');

document.addEventListener('DOMContentLoaded', () => {
  userRole = getRole() || 'student';

  // Configure UI based on role
  if (userRole === 'faculty') {
    modeBadge.textContent = '👨‍🏫 Faculty Mode';
    modeBadge.style.background = 'rgba(16,185,129,0.15)';
    modeBadge.style.color = '#34d399';
    modeBadge.style.border = '1px solid rgba(16,185,129,0.3)';
    sidebarTitle.textContent = 'Student Messages';
    emptyDesc.textContent = 'View and reply to student messages. Select a conversation from the inbox.';
    usernameInput.value = localStorage.getItem('frip_username') || 'Professor';
  } else {
    modeBadge.textContent = '🎓 Student Mode';
    modeBadge.style.background = 'rgba(79,70,229,0.15)';
    modeBadge.style.color = '#818cf8';
    modeBadge.style.border = '1px solid rgba(79,70,229,0.3)';
    sidebarTitle.textContent = 'Choose a Faculty';
    emptyDesc.textContent = 'Select a faculty member from the list to start chatting. Your messages will appear in their inbox in real time.';
    usernameInput.value = localStorage.getItem('frip_username') || 'Student';
  }

  usernameInput.addEventListener('input', () => {
    localStorage.setItem('frip_username', usernameInput.value.trim());
  });

  // Render sidebar
  renderSidebar();

  // Search filter
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      renderSidebar(e.target.value.toLowerCase().trim());
    });
  }

  // Auto-grow textarea
  chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = chatInput.scrollHeight + 'px';
    sendBtn.disabled = !chatInput.value.trim();
  });

  // Enter to send
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  });

  sendBtn.addEventListener('click', handleSend);

  // Check URL params for pre-selected faculty
  const params = new URLSearchParams(window.location.search);
  const preselect = params.get('faculty');
  if (preselect) {
    const found = FACULTY_MEMBERS.find(f => f.name.toLowerCase() === preselect.toLowerCase());
    if (found) {
      selectFaculty(found);
    }
  }
});

// ── Render Sidebar ──
function renderSidebar(filter = '') {
  listContainer.innerHTML = '';

  if (userRole === 'faculty') {
    // Faculty sees an inbox view — show all faculty members (including self) with message counts
    renderFacultyInbox(filter);
  } else {
    // Student sees a list of faculty members to message
    renderFacultyList(filter);
  }
}

function renderFacultyList(filter) {
  const filtered = FACULTY_MEMBERS.filter(f =>
    f.name.toLowerCase().includes(filter) ||
    f.domain.toLowerCase().includes(filter) ||
    f.dept.toLowerCase().includes(filter)
  );

  if (filtered.length === 0) {
    listContainer.innerHTML = `
      <div style="font-size: var(--text-xs); color: var(--text-muted); padding: var(--space-4); text-align: center;">
        No faculty found
      </div>
    `;
    return;
  }

  filtered.forEach(f => {
    const initials = getInitials(f.name);
    const color = stringToColor(f.name);
    const isActive = selectedFaculty && selectedFaculty.name === f.name;

    const item = document.createElement('div');
    item.className = `fc-item ${isActive ? 'active' : ''}`;
    item.innerHTML = `
      <div class="fc-item-avatar" style="background: ${color};">
        ${initials}
        <span class="online-dot"></span>
      </div>
      <div class="fc-item-info">
        <div class="fc-item-name">${f.name}</div>
        <div class="fc-item-domain">${f.domain}</div>
      </div>
    `;
    item.addEventListener('click', () => selectFaculty(f));
    listContainer.appendChild(item);
  });
}

async function renderFacultyInbox(filter) {
  // For faculty, show all faculty members with any conversation threads
  const filtered = FACULTY_MEMBERS.filter(f =>
    f.name.toLowerCase().includes(filter) ||
    f.domain.toLowerCase().includes(filter)
  );

  // Fetch thread counts from API
  let threadData = [];
  try {
    const res = await fetch('/api/faculty-chat/all');
    if (res.ok) threadData = await res.json();
  } catch (_) {}

  const threadMap = {};
  threadData.forEach(t => {
    threadMap[t.faculty_name.toLowerCase()] = t;
  });

  if (filtered.length === 0) {
    listContainer.innerHTML = `
      <div style="font-size: var(--text-xs); color: var(--text-muted); padding: var(--space-4); text-align: center;">
        No conversations found
      </div>
    `;
    return;
  }

  // Sort: those with messages first
  const sorted = [...filtered].sort((a, b) => {
    const aData = threadMap[a.name.toLowerCase()];
    const bData = threadMap[b.name.toLowerCase()];
    if (aData && !bData) return -1;
    if (!aData && bData) return 1;
    if (aData && bData) {
      return new Date(bData.last_message_at) - new Date(aData.last_message_at);
    }
    return 0;
  });

  sorted.forEach(f => {
    const initials = getInitials(f.name);
    const color = stringToColor(f.name);
    const isActive = selectedFaculty && selectedFaculty.name === f.name;
    const tData = threadMap[f.name.toLowerCase()];
    const count = tData ? tData.message_count : 0;
    const lastTime = tData ? formatTimeShort(new Date(tData.last_message_at)) : '';

    const item = document.createElement('div');
    item.className = `fc-item ${isActive ? 'active' : ''}`;
    item.innerHTML = `
      <div class="fc-item-avatar" style="background: ${color};">
        ${initials}
        ${count > 0 ? '<span class="online-dot"></span>' : ''}
      </div>
      <div class="fc-item-info">
        <div class="fc-item-name">${f.name}</div>
        <div class="fc-item-domain">${count > 0 ? `${count} messages` : 'No messages yet'}</div>
      </div>
      ${count > 0 ? `
        <div class="fc-item-meta">
          <span class="fc-item-time">${lastTime}</span>
          <span class="fc-item-badge">${count}</span>
        </div>
      ` : ''}
    `;
    item.addEventListener('click', () => selectFaculty(f));
    listContainer.appendChild(item);
  });
}

// ── Select Faculty Thread ──
function selectFaculty(faculty) {
  selectedFaculty = faculty;

  // Update sidebar selection
  renderSidebar(searchInput ? searchInput.value.toLowerCase().trim() : '');

  // Update header
  const initials = getInitials(faculty.name);
  activeAvatar.textContent = initials;
  activeAvatar.style.background = stringToColor(faculty.name);
  activeName.textContent = faculty.name;
  activeDomain.textContent = `${faculty.domain} • ${faculty.dept}`;

  // Enable input
  chatInput.disabled = false;
  chatInput.placeholder = `Message ${faculty.name}...`;
  chatInput.focus();

  // Show loading
  messagesArea.innerHTML = `
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%;">
      <div class="skeleton" style="width: 80%; height: 20px; margin-bottom: 10px;"></div>
      <div class="skeleton" style="width: 60%; height: 20px; margin-bottom: 10px;"></div>
      <div style="font-size: var(--text-xs); color: var(--text-muted);">Loading conversation...</div>
    </div>
  `;

  // Fetch messages
  fetchMessages();

  // Reset polling
  if (pollingInterval) clearInterval(pollingInterval);
  pollingInterval = setInterval(fetchMessages, 4000);
}

// ── Fetch Messages ──
async function fetchMessages() {
  if (!selectedFaculty) return;

  try {
    const url = `/api/faculty-chat?faculty_name=${encodeURIComponent(selectedFaculty.name)}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to load chat.');
    const data = await res.json();

    if (JSON.stringify(data) !== JSON.stringify(currentMessages)) {
      currentMessages = data;
      renderMessages();
    }

    syncIndicator.textContent = '🟢 Live';
    syncIndicator.style.color = 'var(--color-success)';
  } catch (err) {
    console.error(err);
    syncIndicator.textContent = '⚠️ Sync Error';
    syncIndicator.style.color = '#ef4444';
  }
}

// ── Render Messages ──
function renderMessages() {
  messagesArea.innerHTML = '';

  if (currentMessages.length === 0) {
    messagesArea.innerHTML = `
      <div class="fc-empty-state">
        <div class="fc-empty-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="40" height="40">
            <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
          </svg>
        </div>
        <h3>No messages yet</h3>
        <p>Start the conversation by sending a message below.</p>
      </div>
    `;
    return;
  }

  let lastDateStr = '';

  currentMessages.forEach(msg => {
    // Date separator
    const date = new Date(msg.timestamp);
    const dateStr = date.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
    if (dateStr !== lastDateStr) {
      lastDateStr = dateStr;
      const sep = document.createElement('div');
      sep.className = 'fc-date-separator';
      sep.innerHTML = `<span>${isToday(date) ? 'Today' : isYesterday(date) ? 'Yesterday' : dateStr}</span>`;
      messagesArea.appendChild(sep);
    }

    const isOutgoing = msg.sender_name === usernameInput.value.trim();
    const isFaculty = msg.sender_role === 'faculty';
    const initials = msg.sender_name ? msg.sender_name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() : 'U';
    const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const avatarColor = isFaculty ? 'var(--color-success)' : 'var(--color-primary)';

    const el = document.createElement('div');
    el.className = `fc-message ${isOutgoing ? 'outgoing' : ''}`;
    el.innerHTML = `
      <div class="fc-msg-avatar" style="background: ${avatarColor};">${initials}</div>
      <div class="fc-msg-content">
        <div class="fc-msg-header">
          <span class="fc-msg-sender">${escapeHtml(msg.sender_name)}</span>
          <span class="fc-msg-role-badge ${isFaculty ? 'faculty' : 'student'}">${msg.sender_role}</span>
        </div>
        <div class="fc-msg-bubble">${escapeHtml(msg.message)}</div>
        <span class="fc-msg-time">${timeStr}</span>
      </div>
    `;
    messagesArea.appendChild(el);
  });

  scrollToBottom();
}

// ── Send Message ──
async function handleSend() {
  const message = chatInput.value.trim();
  if (!message || !selectedFaculty) return;

  const senderName = usernameInput.value.trim() || (userRole === 'faculty' ? 'Professor' : 'Student');

  // Clear input immediately
  chatInput.value = '';
  chatInput.style.height = 'auto';
  sendBtn.disabled = true;

  try {
    const response = await fetch('/api/faculty-chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        faculty_name: selectedFaculty.name,
        sender_name: senderName,
        sender_role: userRole,
        message: message
      })
    });

    if (!response.ok) throw new Error('Failed to send message.');

    // Refresh immediately
    await fetchMessages();

    // Also update sidebar if faculty (to reflect new counts)
    if (userRole === 'faculty') {
      renderSidebar(searchInput ? searchInput.value.toLowerCase().trim() : '');
    }
  } catch (err) {
    toast.error(err.message || 'Failed to send message.');
    chatInput.value = message;
    chatInput.style.height = 'auto';
    sendBtn.disabled = false;
  }
}

// ── Helpers ──
function scrollToBottom() {
  messagesArea.scrollTop = messagesArea.scrollHeight;
}

function escapeHtml(unsafe) {
  return unsafe
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function isToday(date) {
  const today = new Date();
  return date.toDateString() === today.toDateString();
}

function isYesterday(date) {
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  return date.toDateString() === yesterday.toDateString();
}

function formatTimeShort(date) {
  if (isToday(date)) return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  if (isYesterday(date)) return 'Yesterday';
  return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
}
