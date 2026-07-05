/**
 * paper_chat.js — Student & Teacher Paper Chat Controller
 * Handles selecting papers, polling messages, and posting new entries to Supabase via backend APIs.
 */

import { getRole } from './auth.js';
import { toast } from './toast.js';
import { getStats } from './api.js';

// Faculty Seed Data matching paper author profiles to get the list of papers
const FACULTY_MEMBERS = [
  {
    name: 'Dr. Padmaja',
    paper: 'Agri-Ai-Intelligent-Plant-Disease-Surveillance-and-Predictive-Forecasting_PADMAJA.pdf',
    domain: 'Agriculture AI'
  },
  {
    name: 'Dr. Venkateshwara',
    paper: 'Comprehensive Models Towards for Feature_venkateshwara.pdf',
    domain: 'Machine Learning'
  },
  {
    name: 'Dr. Madhurya',
    paper: 'Integrating Named Data Networking with IoT-Based Internet _MADHURYA.pdf',
    domain: 'IoT / Networking'
  },
  {
    name: 'Dr. Gagandeep',
    paper: 'IOT based health monitoring_gagandeep.pdf',
    domain: 'IoT / Healthcare'
  },
  {
    name: 'Dr. Vasantha',
    paper: 'Measuring Internet Energy Consumption at The Edge and Core_vasantha.pdf',
    domain: 'Network Infrastructure'
  },
  {
    name: 'Prof. Srinivas Gongula',
    paper: 'Accident Detection and Alert System Using Big Data Analytics_SRININVAS_GONGULA.pdf',
    domain: 'Big Data'
  },
  {
    name: 'Dr. Ravikumar',
    paper: 'Characterizing Ipv6 Adoption Trends Through Longitudinal _RAVIKUMAR.pdf',
    domain: 'IPv6 Network Protocols'
  },
  {
    name: 'Prof. Manzoor',
    paper: 'From CNNs to diffusion models_MANZOOR.pdf',
    domain: 'Generative Models'
  }
];

// State
let selectedPaper = null;
let currentMessages = [];
let pollingInterval = null;
let userRole = 'student';
let dynamicPapers = [];

// DOM Elements
const papersListContainer = document.getElementById('papers-list-container');
const paperSearchInput = document.getElementById('paper-search');
const activePaperTitle = document.getElementById('active-paper-title');
const activePaperAuthor = document.getElementById('active-paper-author');
const chatUsername = document.getElementById('chat-username');
const paperMessagesContainer = document.getElementById('paper-messages-container');
const paperChatInput = document.getElementById('paper-chat-input');
const paperChatSendBtn = document.getElementById('paper-chat-send-btn');
const syncIndicator = document.getElementById('chat-sync-indicator');

document.addEventListener('DOMContentLoaded', async () => {
  // Determine role
  userRole = getRole() || 'student';
  
  // Set default name based on role
  if (userRole === 'faculty') {
    chatUsername.value = 'Professor ' + (localStorage.getItem('frip_username') || 'Teacher');
  } else {
    chatUsername.value = 'Student ' + (localStorage.getItem('frip_username') || 'Alice');
  }

  // Prepopulate username changes to localStorage
  chatUsername.addEventListener('input', () => {
    localStorage.setItem('frip_username', chatUsername.value.replace(/^(Professor|Student)\s+/, ''));
  });

  // Render list of papers dynamically from Chroma DB
  await loadDynamicPapers();

  // Search input filter
  if (paperSearchInput) {
    paperSearchInput.addEventListener('input', (e) => {
      renderPapersList(e.target.value.toLowerCase().trim());
    });
  }

  // Auto-grow textarea
  paperChatInput.addEventListener('input', () => {
    paperChatInput.style.height = 'auto';
    paperChatInput.style.height = (paperChatInput.scrollHeight) + 'px';
    paperChatSendBtn.disabled = !paperChatInput.value.trim();
  });

  // Submit on Enter (except Shift+Enter)
  paperChatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  });

  paperChatSendBtn.addEventListener('click', handleSendMessage);
});

function renderPapersList(filter = '') {
  papersListContainer.innerHTML = '';
  const filtered = dynamicPapers.filter(f => 
    f.paper.toLowerCase().includes(filter) || f.name.toLowerCase().includes(filter) || f.domain.toLowerCase().includes(filter)
  );

  if (filtered.length === 0) {
    papersListContainer.innerHTML = `<div style="font-size: var(--text-xs); color: var(--text-muted); padding: var(--space-4); text-align: center;">No papers found</div>`;
    return;
  }

  filtered.forEach(p => {
    const item = document.createElement('div');
    item.className = `paper-item ${selectedPaper && selectedPaper.paper === p.paper ? 'active' : ''}`;
    item.innerHTML = `
      <div class="paper-item-title">${p.paper}</div>
      <div class="paper-item-author">Faculty: ${p.name} (${p.domain})</div>
    `;
    item.addEventListener('click', () => selectPaper(p));
    papersListContainer.appendChild(item);
  });
}

async function loadDynamicPapers() {
  try {
    const stats = await getStats();
    const chromaPapers = stats.papers || [];
    
    const merged = [];
    const seenPapers = new Set();
    
    chromaPapers.forEach(paperName => {
      seenPapers.add(paperName.toLowerCase());
      const matched = FACULTY_MEMBERS.find(f => 
        f.paper.toLowerCase() === paperName.toLowerCase() || 
        paperName.toLowerCase().includes(f.paper.toLowerCase()) || 
        f.paper.toLowerCase().includes(paperName.toLowerCase())
      );
      
      if (matched) {
        merged.push({
          name: matched.name,
          paper: paperName,
          domain: matched.domain
        });
      } else {
        let authorName = "Unknown Faculty";
        let domainName = "General Research";
        
        const nameMatch = paperName.match(/_([A-Za-z]+)\.pdf$/i);
        if (nameMatch) {
          const rawName = nameMatch[1];
          authorName = "Dr. " + rawName.charAt(0).toUpperCase() + rawName.slice(1).toLowerCase();
        }
        
        merged.push({
          name: authorName,
          paper: paperName,
          domain: domainName
        });
      }
    });
    
    if (merged.length === 0) {
      dynamicPapers = [...FACULTY_MEMBERS];
    } else {
      dynamicPapers = merged;
    }
  } catch (err) {
    console.error('Failed to load dynamic papers from Chroma:', err);
    dynamicPapers = [...FACULTY_MEMBERS];
  }
  
  renderPapersList();
}

function selectPaper(paper) {
  selectedPaper = paper;
  
  // Re-render list to update active class
  renderPapersList(paperSearchInput ? paperSearchInput.value.toLowerCase().trim() : '');

  // Update header
  activePaperTitle.textContent = paper.paper;
  activePaperAuthor.textContent = `Discussion Group • Faculty Advisor: ${paper.name}`;

  // Enable inputs
  paperChatInput.disabled = false;
  paperChatInput.placeholder = "Post to this research paper group...";

  // Clear messages list, show loader
  paperMessagesContainer.innerHTML = `
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%;">
      <div class="skeleton" style="width: 80%; height: 20px; margin-bottom: 10px;"></div>
      <div class="skeleton" style="width: 60%; height: 20px; margin-bottom: 10px;"></div>
      <div style="font-size: var(--text-xs); color: var(--text-muted);">Loading discussions...</div>
    </div>
  `;

  // Fetch messages immediately
  fetchChatMessages();

  // Reset polling
  if (pollingInterval) clearInterval(pollingInterval);
  pollingInterval = setInterval(fetchChatMessages, 5000);
}

async function fetchChatMessages() {
  if (!selectedPaper) return;

  try {
    const url = `/api/paper-chat?paper_title=${encodeURIComponent(selectedPaper.paper)}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to load chat history.');
    const data = await res.json();
    
    // Compare messages count/timestamps to prevent re-rendering when no updates
    if (JSON.stringify(data) !== JSON.stringify(currentMessages)) {
      currentMessages = data;
      renderMessages();
    }
    
    // Update live status
    syncIndicator.textContent = "🟢 Live (Supabase synced)";
    syncIndicator.style.color = "var(--color-success)";
  } catch (err) {
    console.error(err);
    syncIndicator.textContent = "⚠️ Sync Error";
    syncIndicator.style.color = "#ef4444";
  }
}

function renderMessages() {
  paperMessagesContainer.innerHTML = '';
  
  if (currentMessages.length === 0) {
    paperMessagesContainer.innerHTML = `
      <div class="paper-chat-empty">
        <div class="paper-chat-empty-icon">💬</div>
        <h3>No discussions yet</h3>
        <p>Start the conversation by typing a question or comment below.</p>
      </div>
    `;
    return;
  }

  currentMessages.forEach(msg => {
    const isCurrentUser = msg.sender_name === chatUsername.value;
    const messageEl = document.createElement('div');
    messageEl.className = `message ${isCurrentUser ? 'user' : 'ai'}`;

    const date = new Date(msg.timestamp);
    const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const dateStr = date.toLocaleDateString([], { month: 'short', day: 'numeric' });

    const initials = msg.sender_name ? msg.sender_name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() : 'U';
    const isFaculty = msg.sender_role === 'faculty';

    messageEl.innerHTML = `
      <div class="message-avatar" style="background: ${isFaculty ? 'var(--color-success)' : 'var(--color-primary)'}; box-shadow: none;">${initials}</div>
      <div class="message-content" style="max-width: 80%;">
        <div class="message-header-info">
          <span class="message-sender-name">${msg.sender_name}</span>
          <span class="role-badge ${isFaculty ? 'faculty' : 'student'}">${msg.sender_role}</span>
        </div>
        <div class="message-bubble" style="${isCurrentUser ? 'background: var(--color-primary); color: white;' : 'background: var(--bg-surface-2); color: var(--text-secondary); border: 1px solid var(--border-subtle);'}">
          ${escapeHtml(msg.message)}
        </div>
        <div class="flex-between" style="margin-top: 2px;">
          <span class="message-time">${dateStr} ${timeStr}</span>
        </div>
      </div>
    `;
    
    paperMessagesContainer.appendChild(messageEl);
  });

  scrollToBottom();
}

async function handleSendMessage() {
  const message = paperChatInput.value.trim();
  if (!message || !selectedPaper) return;

  const senderName = chatUsername.value.trim() || (userRole === 'faculty' ? 'Teacher' : 'Student');

  // Disable input immediately to prevent double submissions
  paperChatInput.value = '';
  paperChatInput.style.height = 'auto';
  paperChatSendBtn.disabled = true;

  try {
    const response = await fetch('/api/paper-chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        paper_title: selectedPaper.paper,
        sender_name: senderName,
        sender_role: userRole,
        message: message
      })
    });

    if (!response.ok) throw new Error('Failed to post message.');
    
    // Fetch immediately to update view
    await fetchChatMessages();
  } catch (err) {
    toast.error(err.message || 'Failed to send message.');
    paperChatInput.value = message; // restore message in input
    paperChatInput.style.height = 'auto';
    paperChatSendBtn.disabled = false;
  }
}

function scrollToBottom() {
  paperMessagesContainer.scrollTop = paperMessagesContainer.scrollHeight;
}

function escapeHtml(unsafe) {
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
