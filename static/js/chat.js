/**
 * chat.js — Chat Controller
 * Manages user message entries, API fetching, Markdown conversion,
 * citations list, and user feedback actions.
 */

import { chat, submitFeedback } from './api.js';
import { renderMarkdown, copyToClipboard } from './utils.js';
import { toast } from './toast.js';

// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('chat-send-btn');
const welcomeScreen = document.getElementById('chat-welcome');

// Conversation State
let lastQueryLogId = null;

// Load query from URL if passed (e.g. from global search)
document.addEventListener('DOMContentLoaded', () => {
  const urlParams = new URLSearchParams(window.location.search);
  const query = urlParams.get('q');
  if (query) {
    chatInput.value = query;
    handleSend();
  }

  // Bind suggested question buttons
  document.querySelectorAll('.suggestion-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      chatInput.value = btn.dataset.query;
      handleSend();
    });
  });
});

// Auto-grow textarea
chatInput.addEventListener('input', () => {
  chatInput.style.height = 'auto';
  chatInput.style.height = (chatInput.scrollHeight) + 'px';
  sendBtn.disabled = !chatInput.value.trim();
});

// Submit on Enter (except Shift+Enter)
chatInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
});

sendBtn.addEventListener('click', handleSend);

/**
 * Handle message sending
 */
async function handleSend() {
  const query = chatInput.value.trim();
  if (!query) return;

  // Clear input
  chatInput.value = '';
  chatInput.style.height = 'auto';
  sendBtn.disabled = true;

  // Remove welcome screen if visible
  if (welcomeScreen) {
    welcomeScreen.style.display = 'none';
  }

  // 1. Render User Message
  appendMessage(query, 'user');

  // 2. Render Typing Indicator
  const typingIndicator = appendTypingIndicator();
  scrollToBottom();

  try {
    // 3. Request API
    const roleSelect = document.getElementById('chat-role');
    const role = roleSelect ? roleSelect.value : 'student';
    const result = await chat(query, role);

    // Remove typing indicator
    typingIndicator.remove();

    // 4. Render AI Message
    appendMessage(result.response_text, 'ai', result.data, result.intent);
    if (result.data && result.data.query_log_id) {
      lastQueryLogId = result.data.query_log_id;
    }

  } catch (err) {
    typingIndicator.remove();
    appendMessage(`An error occurred processing your query: ${err.message}`, 'ai-error');
    toast.error(err.message || 'Request failed.');
  }

  scrollToBottom();
}

/**
 * Appends a message bubble to the messages container
 */
function appendMessage(text, sender, data = null, intent = '') {
  const messageEl = document.createElement('div');
  messageEl.className = `message ${sender === 'user' ? 'user' : 'ai'}`;

  // Avatar Initials
  const initials = sender === 'user' ? 'U' : 'AI';
  const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  // Main text container
  let contentHTML = `
    <div class="message-avatar">${initials}</div>
    <div class="message-content">
      <div class="message-bubble md-content">
        ${sender === 'user' ? renderMarkdown(text) : renderMarkdown(text)}
      </div>
      <div class="flex-between">
        <span class="message-time">${time}</span>
        ${sender === 'ai' && data && data.query_log_id ? renderActions(data.query_log_id, text) : ''}
      </div>
  `;

  // Render sources / papers citations if present
  if (sender === 'ai' && data) {
    const matches = data.internal_matches || [];
    if (matches.length > 0) {
      contentHTML += `
        <div class="citations-panel">
          <span class="citations-label">Sources Cited (${matches.length})</span>
          <div class="flex-wrap">
      `;
      // Distinct sources list
      const sourcesSeen = new Set();
      matches.forEach((match, idx) => {
        const sourceName = match.metadata.source || 'Faculty Publication';
        if (!sourcesSeen.has(sourceName)) {
          sourcesSeen.add(sourceName);
          const page = match.metadata.page ? ` (p. ${match.metadata.page})` : '';
          const distanceStr = match.distance !== undefined ? ` [Distance: ${match.distance.toFixed(4)}]` : '';
          contentHTML += `
            <div class="citation-card" title="Click to view match summary">
              <div class="citation-source">${sourceName}${page}${distanceStr}</div>
              <div style="font-size: 11px; color: var(--text-muted); line-height: 1.3;">
                ${match.document.slice(0, 120)}...
              </div>
            </div>
          `;
        }
      });
      contentHTML += `</div></div>`;
    }
  }

  contentHTML += `</div>`;
  messageEl.innerHTML = contentHTML;
  chatMessages.appendChild(messageEl);

  // Bind Actions if AI message
  if (sender === 'ai' && data && data.query_log_id) {
    bindMessageActions(messageEl, data.query_log_id, text);
  }
}

/**
 * Renders copy button
 */
function renderActions(queryLogId, text) {
  return `
    <div class="message-actions">
      <button class="msg-action-btn copy-btn" title="Copy response">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
      </button>
    </div>
  `;
}

/**
 * Binds actions logic to the message buttons
 */
function bindMessageActions(messageEl, queryLogId, text) {
  const copyBtn = messageEl.querySelector('.copy-btn');

  if (copyBtn) {
    copyBtn.addEventListener('click', async () => {
      try {
        await copyToClipboard(text);
        toast.success('Copied response to clipboard!');
      } catch (err) {
        toast.error('Copy failed.');
      }
    });
  }
}

/**
 * Append temporary typing indicator
 */
function appendTypingIndicator() {
  const messageEl = document.createElement('div');
  messageEl.className = 'message ai';
  messageEl.innerHTML = `
    <div class="message-avatar">AI</div>
    <div class="message-content">
      <div class="typing-bubble">
        <div class="typing-dots">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      </div>
    </div>
  `;
  chatMessages.appendChild(messageEl);
  return messageEl;
}

function scrollToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// End Conversation and Feedback Modal Logic
const endChatBtn = document.getElementById('end-chat-btn');
const feedbackModal = document.getElementById('chat-feedback-modal');
const starButtons = document.querySelectorAll('.star-btn');
const commentsTextarea = document.getElementById('feedback-comments');
const submitFeedbackBtn = document.getElementById('feedback-submit-btn');
const cancelFeedbackBtn = document.getElementById('feedback-cancel-btn');

let selectedRating = null;

if (endChatBtn) {
  endChatBtn.addEventListener('click', () => {
    if (!lastQueryLogId) {
      toast.info('No active conversation history. Resetting chat screen.');
      resetChatScreen();
      return;
    }
    // Show modal
    feedbackModal.style.display = 'flex';
  });
}

// Stars rating selection
starButtons.forEach(star => {
  star.addEventListener('click', () => {
    selectedRating = parseInt(star.dataset.star);
    // Highlight stars up to clicked one
    starButtons.forEach(s => {
      const starVal = parseInt(s.dataset.star);
      if (starVal <= selectedRating) {
        s.style.color = '#F59E0B'; // Gold star color
      } else {
        s.style.color = 'rgba(255, 255, 255, 0.15)'; // Inactive
      }
    });
    submitFeedbackBtn.disabled = false;
  });
  
  // Hover styles
  star.addEventListener('mouseover', () => {
    const hoverVal = parseInt(star.dataset.star);
    starButtons.forEach(s => {
      const starVal = parseInt(s.dataset.star);
      if (starVal <= hoverVal) {
        s.style.transform = 'scale(1.2)';
        s.style.textShadow = '0 0 8px #F59E0B';
      }
    });
  });

  star.addEventListener('mouseout', () => {
    starButtons.forEach(s => {
      s.style.transform = 'scale(1)';
      s.style.textShadow = 'none';
    });
  });
});

// Submit feedback
if (submitFeedbackBtn) {
  submitFeedbackBtn.addEventListener('click', async () => {
    if (!lastQueryLogId || !selectedRating) return;
    const comments = commentsTextarea.value.trim();
    try {
      submitFeedbackBtn.disabled = true;
      await submitFeedback(lastQueryLogId, selectedRating, comments);
      toast.success('Thank you for your feedback!');
      closeFeedbackModal();
      resetChatScreen();
    } catch (err) {
      submitFeedbackBtn.disabled = false;
      toast.error('Failed to log feedback.');
    }
  });
}

// Skip feedback
if (cancelFeedbackBtn) {
  cancelFeedbackBtn.addEventListener('click', () => {
    closeFeedbackModal();
    resetChatScreen();
    toast.info('Conversation reset.');
  });
}

function closeFeedbackModal() {
  feedbackModal.style.display = 'none';
  selectedRating = null;
  starButtons.forEach(s => {
    s.style.color = 'rgba(255, 255, 255, 0.15)';
  });
  commentsTextarea.value = '';
  submitFeedbackBtn.disabled = true;
}

function resetChatScreen() {
  // Clear messages except welcome
  chatMessages.innerHTML = '';
  // Re-append welcome screen
  if (welcomeScreen) {
    welcomeScreen.style.display = 'flex';
    chatMessages.appendChild(welcomeScreen);
  }
  lastQueryLogId = null;
}
