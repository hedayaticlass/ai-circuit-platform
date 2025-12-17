// Utility functions
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

// State
let currentSessionId = 'default';
let isLoading = false;

// Elements
const chatMessages = $('#chatMessages');
const chatInput = $('#chatInput');
const btnSend = $('#btnSend');
const btnNewChat = $('#btnNewChat');
const btnClearChat = $('#btnClearChat');
const btnToggleSidebar = $('#btnToggleSidebar');
const statusMessage = $('#statusMessage');
const chatSessions = $('#chatSessions');
const sidebar = $('.sidebar');
const llmBaseUrl = $('#llmBaseUrl');
const llmModel = $('#llmModel');
const llmApiKey = $('#llmApiKey');
const chatSessionTitle = $('#chatSessionTitle');
const btnToggleSettings = $('#btnToggleSettings');
const settingsSection = $('#settingsSection');
const historySection = $('#historySection');
const sidebarContentWrapper = $('#sidebarContentWrapper');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  loadChatSessions();
  loadChatHistory(currentSessionId);
  setupEventListeners();
  autoResizeTextarea();
  loadSidebarState();
  // Close sidebar on outside click
  document.addEventListener('click', (e) => {
    if (!sidebar.contains(e.target) && !btnToggleSidebar.contains(e.target) && !sidebar.classList.contains('collapsed')) {
      sidebar.classList.add('collapsed');
      localStorage.setItem('sidebarCollapsed', 'true');
    }
  });
  // Update chat session title on load
  updateChatSessionTitle('چت جدید');
});

// Event Listeners
function setupEventListeners() {
  btnSend.addEventListener('click', sendMessage);
  btnNewChat.addEventListener('click', createNewChat);
  btnClearChat.addEventListener('click', clearCurrentChat);
  btnToggleSidebar.addEventListener('click', toggleSidebar);
  btnToggleSettings.addEventListener('click', toggleSettingsHistory);
  
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Example prompts
  $$('.example-prompt').forEach(prompt => {
    prompt.addEventListener('click', () => {
      const text = prompt.getAttribute('data-prompt');
      chatInput.value = text;
      chatInput.focus();
    });
  });

  // Session click handlers
  chatSessions.addEventListener('click', (e) => {
    const sessionItem = e.target.closest('.session-item');
    if (sessionItem) {
      const sessionId = sessionItem.getAttribute('data-session');
      if (sessionId && sessionId !== currentSessionId) {
        switchSession(sessionId);
      }
    }

    const deleteBtn = e.target.closest('.btn-delete-session');
    if (deleteBtn) {
      e.stopPropagation();
      const sessionId = deleteBtn.getAttribute('data-session');
      if (sessionId && sessionId !== 'default') {
        deleteSession(sessionId);
      }
    }

    const editBtn = e.target.closest('.btn-edit-session');
    if (editBtn) {
      e.stopPropagation();
      const sessionId = editBtn.getAttribute('data-session');
      editSessionName(sessionId);
    }
  });
}

// Auto-resize textarea
function autoResizeTextarea() {
  chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 150) + 'px';
  });
}

// Send Message
async function sendMessage() {
  const message = chatInput.value.trim();
  if (!message || isLoading) return;

  // Clear input
  chatInput.value = '';
  chatInput.style.height = 'auto';
  
  // Hide welcome message
  const welcomeMsg = $('.welcome-message');
  if (welcomeMsg) {
    welcomeMsg.remove();
  }

  // Add user message
  addMessage('user', message);

  // Show loading
  const loadingId = addLoadingMessage();
  setStatus('در حال تولید مدار...', '');
  btnSend.disabled = true;
  isLoading = true;

  try {
    const response = await fetch('/api/chat/message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        sessionId: currentSessionId,
        llmBaseUrl: llmBaseUrl.value.trim(),
        llmModel: llmModel.value.trim(),
        llmApiKey: llmApiKey.value.trim()
      })
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error || 'خطای نامشخص');
    }

    // Remove loading
    removeMessage(loadingId);

    // Add assistant message
    addAssistantMessage(data.message);
    // Collapse sidebar after successful assistant response
    if (!sidebar.classList.contains('collapsed')) {
      sidebar.classList.add('collapsed');
      localStorage.setItem('sidebarCollapsed', 'true');
    }
    setStatus('', '');
    
    // Reload sessions to update last message time
    loadChatSessions();
  } catch (error) {
    removeMessage(loadingId);
    addMessage('assistant', `خطا: ${error.message}`, true);
    showToast(`خطا: ${error.message}`, 'error');
  } finally {
    btnSend.disabled = false;
    isLoading = false;
    chatInput.focus();
  }
}

// Add Message
function addMessage(role, content, isError = false) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${role}`;
  
  const avatar = document.createElement('div');
  avatar.className = 'message-avatar';
  avatar.innerHTML = role === 'user' ? '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-user"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>' : '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-bot"><path d="M12 8V4H8"/><path d="M22 17H2a4 4 0 0 1 4-4h12a4 4 0 0 1 4 4v2a2 2 0 0 1-2 2h-2a2 2 0 0 1-2-2v-2a2 2 0 0 0-2-2h-2a2 2 0 0 0-2 2v2a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2Z"/><path d="M2 17a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2"/></svg>';
  
  const messageContent = document.createElement('div');
  messageContent.className = 'message-content';
  
  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';
  
  if (isError) {
    bubble.style.background = 'var(--error)';
    bubble.style.color = 'white';
  }
  
  bubble.textContent = content;

  // Add copy button for user messages
  if (role === 'user') {
    const copyBtn = document.createElement('button');
    copyBtn.className = 'btn-copy-message';
    copyBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-copy"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1-1.1-2-2.5-2-4 0-1.5 1.1-3 2.5-4.5S7 2 8.5 2C10 2 11.4 1.1 12 2.5"/></svg>';
    copyBtn.title = 'کپی کردن پیام';
    copyBtn.addEventListener('click', () => {
      navigator.clipboard.writeText(content).then(() => {
        showToast('پیام کپی شد!', 'success', 2000);
      }).catch(err => {
        console.error('Failed to copy message: ', err);
        showToast('خطا در کپی پیام', 'error', 2000);
      });
    });
    messageContent.appendChild(copyBtn);
  }
  
  messageContent.appendChild(bubble);
  messageDiv.appendChild(avatar);
  messageDiv.appendChild(messageContent);
  
  chatMessages.appendChild(messageDiv);
  scrollToBottom();
  
  return messageDiv;
}

// Add Assistant Message with full output
function addAssistantMessage(messageData) {
  const messageDiv = document.createElement('div');
  messageDiv.className = 'message assistant';
  
  const avatar = document.createElement('div');
  avatar.className = 'message-avatar';
  avatar.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-bot"><path d="M12 8V4H8"/><path d="M22 17H2a4 4 0 0 1 4-4h12a4 4 0 0 1 4 4v2a2 2 0 0 1-2 2h-2a2 2 0 0 1-2-2v-2a2 2 0 0 0-2-2h-2a2 2 0 0 0-2 2v2a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2Z"/><path d="M2 17a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2"/></svg>';
  
  const messageContent = document.createElement('div');
  messageContent.className = 'message-content';
  
  const assistantOutput = document.createElement('div');
  assistantOutput.className = 'assistant-output';
  
  const content = messageData.content;
  
  // 1. Model Output (collapsible)
  if (content.modelOutput) {
    const { section: modelSection, contentDiv: modelContentDiv } = createOutputSection('1️⃣ خروجی مدل', 'model', true, true);
    const modelContent = document.createElement('div');
    modelContent.className = 'output-text';
    modelContent.textContent = content.modelOutput;
    modelContentDiv.appendChild(modelContent);
    assistantOutput.appendChild(modelSection);
  }
  
  // 2. Python Code (collapsible)
  if (content.pythonCode) {
    const { section: codeSection, contentDiv: codeContentDiv } = createOutputSection('2️⃣ کد پایتون تولید شده', 'code', true, true);
    const codeContent = document.createElement('div');
    codeContent.className = 'output-code';
    const pre = document.createElement('pre');
    pre.textContent = content.pythonCode;
    codeContent.appendChild(pre);
    codeContentDiv.appendChild(codeContent);
    assistantOutput.appendChild(codeSection);
  }
  
  // Legacy support for elements list
  if (content.elements) {
    const { section: elementsSection, contentDiv: elementsContentDiv } = createOutputSection('2️⃣ لیست المان‌های مدار', 'elements', true, true);
    const elementsContent = document.createElement('div');
    elementsContent.className = 'output-code';
    const pre = document.createElement('pre');
    pre.textContent = JSON.stringify(content.elements, null, 2);
    elementsContent.appendChild(pre);
    elementsContentDiv.appendChild(elementsContent);
    assistantOutput.appendChild(elementsSection);
  }
  
  // Legacy support for code
  if (content.code) {
    const { section: codeSection, contentDiv: codeContentDiv } = createOutputSection('2️⃣ کد تولیدی', 'code', true, true);
    const codeContent = document.createElement('div');
    codeContent.className = 'output-code';
    const pre = document.createElement('pre');
    pre.textContent = content.code;
    codeContent.appendChild(pre);
    codeContentDiv.appendChild(codeContent);
    assistantOutput.appendChild(codeSection);
  }
  
  // SPICE Code (collapsible)
  if (content.spiceCode) {
    const { section: spiceSection, contentDiv: spiceContentDiv } = createOutputSection('🔌 کد SPICE', 'spice', true, true);
    const spiceContent = document.createElement('div');
    spiceContent.className = 'output-code';
    const pre = document.createElement('pre');
    pre.textContent = content.spiceCode;
    spiceContent.appendChild(pre);
    spiceContentDiv.appendChild(spiceContent);
    assistantOutput.appendChild(spiceSection);
  }
  
  // Components List (collapsible)
  if (content.components && Array.isArray(content.components) && content.components.length > 0) {
    const { section: componentsSection, contentDiv: componentsContentDiv } = createOutputSection('📋 لیست المان‌های مدار', 'components', true, true);
    const componentsContent = document.createElement('div');
    componentsContent.className = 'output-code';
    const pre = document.createElement('pre');
    pre.textContent = JSON.stringify(content.components, null, 2);
    componentsContent.appendChild(pre);
    componentsContentDiv.appendChild(componentsContent);
    assistantOutput.appendChild(componentsSection);
  }
  
  // 3. Image
  if (content.imageBase64) {
    const { section: imageSection, contentDiv: imageContentDiv } = createOutputSection('3️⃣ تصویر مدار', 'image', true, true);
    const imageContent = document.createElement('div');
    const img = document.createElement('img');
    img.src = content.imageBase64;
    img.alt = 'مدار تولید شده';
    img.className = 'output-image';
    
    // Download button
    const downloadBtn = document.createElement('a');
    downloadBtn.href = content.imageBase64;
    downloadBtn.download = `circuit-${Date.now()}.png`;
    downloadBtn.textContent = '📥 دانلود تصویر';
    downloadBtn.className = 'btn-glass';
    downloadBtn.style.cssText = 'display: inline-block; margin-top: 16px; padding: 10px 20px; text-decoration: none; font-size: 13px; font-weight: 500; color: rgba(255, 255, 255, 0.9);';
    downloadBtn.addEventListener('mouseenter', () => {
      downloadBtn.style.color = 'rgba(255, 255, 255, 1)';
    });
    downloadBtn.addEventListener('mouseleave', () => {
      downloadBtn.style.color = 'rgba(255, 255, 255, 0.9)';
    });
    
    imageContent.appendChild(img);
    imageContent.appendChild(downloadBtn);
    imageContentDiv.appendChild(imageContent);
    assistantOutput.appendChild(imageSection);
  }
  
  messageContent.appendChild(assistantOutput);
  messageDiv.appendChild(avatar);
  messageDiv.appendChild(messageContent);
  
  chatMessages.appendChild(messageDiv);
  scrollToBottom();
}

// Create Output Section
function createOutputSection(title, type, isCollapsible = false, isCollapsed = false) {
  const section = document.createElement('div');
  section.className = 'output-section';
  
  if (isCollapsible) {
    section.classList.add('collapsible');
    if (isCollapsed) {
      section.classList.add('collapsed');
    }
    
    const header = document.createElement('div');
    header.className = 'output-section-header';
    
    const titleDiv = document.createElement('div');
    titleDiv.className = 'output-section-title';
    titleDiv.textContent = title;
    
    const collapseIcon = document.createElement('div');
    collapseIcon.className = 'collapse-icon';
    collapseIcon.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>';
    
    header.appendChild(titleDiv);
    header.appendChild(collapseIcon);
    
    header.addEventListener('click', () => {
      section.classList.toggle('collapsed');
    });
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'output-section-content';
    
    section.appendChild(header);
    section.appendChild(contentDiv);
    
    return { section, contentDiv };
  } else {
    const titleDiv = document.createElement('div');
    titleDiv.className = 'output-section-title';
    titleDiv.textContent = title;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'output-section-content';
    
    section.appendChild(titleDiv);
    section.appendChild(contentDiv);
    
    return { section, contentDiv };
  }
}

// Add Loading Message
function addLoadingMessage() {
  const messageDiv = document.createElement('div');
  messageDiv.className = 'message assistant';
  messageDiv.id = `loading-${Date.now()}`;
  
  const avatar = document.createElement('div');
  avatar.className = 'message-avatar';
  avatar.textContent = '🤖';
  
  const messageContent = document.createElement('div');
  messageContent.className = 'message-content';
  
  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';
  
  const loading = document.createElement('div');
  loading.className = 'loading';
  for (let i = 0; i < 3; i++) {
    const dot = document.createElement('div');
    dot.className = 'loading-dot';
    loading.appendChild(dot);
  }
  
  bubble.appendChild(loading);
  messageContent.appendChild(bubble);
  messageDiv.appendChild(avatar);
  messageDiv.appendChild(messageContent);
  
  chatMessages.appendChild(messageDiv);
  scrollToBottom();
  
  return messageDiv.id;
}

// Remove Message
function removeMessage(messageId) {
  const message = document.getElementById(messageId);
  if (message) {
    message.remove();
  }
}

// Scroll to Bottom
function scrollToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Set Status (deprecated - using toast now)
function setStatus(text, type = '') {
  if (text) {
    showToast(text, type);
  }
}

// Show Toast Notification
function showToast(message, type = 'info', duration = 3000) {
  const container = $('#toastContainer') || createToastContainer();
  
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  
  const messageSpan = document.createElement('span');
  messageSpan.textContent = message;
  
  const closeBtn = document.createElement('button');
  closeBtn.className = 'toast-close';
  closeBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';
  closeBtn.addEventListener('click', () => {
    removeToast(toast);
  });
  
  toast.appendChild(messageSpan);
  toast.appendChild(closeBtn);
  container.appendChild(toast);
  
  // Auto remove after duration
  if (duration > 0) {
    setTimeout(() => {
      removeToast(toast);
    }, duration);
  }
  
  return toast;
}

function createToastContainer() {
  const container = document.createElement('div');
  container.id = 'toastContainer';
  container.className = 'toast-container';
  document.body.appendChild(container);
  return container;
}

function removeToast(toast) {
  toast.style.animation = 'toastSlideIn 0.3s ease-out reverse';
  setTimeout(() => {
    if (toast.parentNode) {
      toast.parentNode.removeChild(toast);
    }
  }, 300);
}

// Create New Chat
function createNewChat() {
  const newSessionId = `session-${Date.now()}`;
  switchSession(newSessionId);
  showToast('چت جدید ایجاد شد', 'success');
  // Close sidebar after creating a new chat
  if (!sidebar.classList.contains('collapsed')) {
    sidebar.classList.add('collapsed');
    localStorage.setItem('sidebarCollapsed', 'true');
  }
  updateChatSessionTitle('چت جدید');
}

// Switch Session
async function switchSession(sessionId) {
  if (sessionId === currentSessionId) return;
  
  currentSessionId = sessionId;

  // Close sidebar if open
  if (!sidebar.classList.contains('collapsed')) {
    sidebar.classList.add('collapsed');
    localStorage.setItem('sidebarCollapsed', 'true');
  }

  // Update active session
  $$('.session-item').forEach(item => {
    item.classList.remove('active');
  });
  const activeItem = $(`.session-item[data-session="${sessionId}"]`);
  if (activeItem) {
    activeItem.classList.add('active');
  } else {
    // Create new session item if it doesn't exist
    addSessionItem(sessionId, 'چت جدید');
    $(`.session-item[data-session="${sessionId}"]`).classList.add('active');
  }
  
  // Load chat history
  await loadChatHistory(sessionId);
  const sessionName = $(`.session-item[data-session="${sessionId}"] .session-name`).textContent;
  updateChatSessionTitle(sessionName);
}

// Load Chat History
async function loadChatHistory(sessionId) {
  try {
    const response = await fetch(`/api/chat/history/${sessionId}`);
    const data = await response.json();
    
    // Clear messages
    chatMessages.innerHTML = '';
    
    if (data.messages && data.messages.length > 0) {
      data.messages.forEach(msg => {
        if (msg.role === 'user') {
          // برای پیام‌های کاربر، content یک رشته است
          const content = typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content);
          addMessage('user', content);
        } else if (msg.role === 'assistant') {
          // برای پیام‌های assistant، content یک object است
          addAssistantMessage({ content: msg.content });
        }
      });
      // Update chat session title with the latest session name
      const sessionName = $(`.session-item[data-session="${sessionId}"] .session-name`).textContent;
      updateChatSessionTitle(sessionName);
    } else {
      // Show welcome message
      showWelcomeMessage();
      updateChatSessionTitle('چت جدید'); // Reset title for empty chat
    }
    
    scrollToBottom();
  } catch (error) {
    console.error('Error loading chat history:', error);
    showWelcomeMessage();
    updateChatSessionTitle('چت جدید'); // Reset title on error
  }
}

// Show Welcome Message
function showWelcomeMessage() {
  chatMessages.innerHTML = `
    <div class="welcome-message">
      <div class="welcome-icon">⚡</div>
      <h2>خوش آمدید!</h2>
      <p>توضیح مدار خود را به فارسی بنویسید و من برای شما کد و تصویر مدار را تولید می‌کنم.</p>
      <div class="example-prompts">
        <div class="example-prompt" data-prompt="یک فیلتر RC پایین‌گذر با مقاومت 10k و خازن 10nF">
          یک فیلتر RC پایین‌گذر
        </div>
        <div class="example-prompt" data-prompt="یک تقویت‌کننده عملیاتی با فیدبک منفی">
          تقویت‌کننده عملیاتی
        </div>
        <div class="example-prompt" data-prompt="یک مدار نوسان‌ساز RC">
          نوسان‌ساز RC
        </div>
      </div>
    </div>
  `;
  
  // Re-attach event listeners for example prompts
  $$('.example-prompt').forEach(prompt => {
    prompt.addEventListener('click', () => {
      const text = prompt.getAttribute('data-prompt');
      chatInput.value = text;
      chatInput.focus();
    });
  });
}

// Load Chat Sessions
async function loadChatSessions() {
  try {
    const response = await fetch('/api/chat/sessions');
    const data = await response.json();
    
    chatSessions.innerHTML = '';
    
    // Add default session
    addSessionItem('default', 'چت جدید', currentSessionId === 'default');
    
    // Add other sessions
    data.sessions.forEach(session => {
      if (session.sessionId !== 'default') {
        const displayName = session.displayName || (() => {
          const date = new Date(session.lastMessage);
          return date.toLocaleDateString('fa-IR', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          });
        })();
        addSessionItem(session.sessionId, displayName, session.sessionId === currentSessionId);
      }
    });
    // Update chat session title if it's the current session and not 'default'
    const currentSessionItem = $(`.session-item[data-session="${currentSessionId}"]`);
    if (currentSessionItem) {
      updateChatSessionTitle(currentSessionItem.querySelector('.session-name').textContent);
    } else {
      updateChatSessionTitle('چت جدید'); // Fallback if current session not found
    }
  } catch (error) {
    console.error('Error loading sessions:', error);
  }
}

// Add Session Item
function addSessionItem(sessionId, name, isActive = false) {
  const item = document.createElement('div');
  item.className = `session-item ${isActive ? 'active' : ''}`;
  item.setAttribute('data-session', sessionId);
  
  const nameSpan = document.createElement('span');
  nameSpan.className = 'session-name';
  nameSpan.textContent = name;
  nameSpan.setAttribute('contenteditable', 'false');
  
  const actionsDiv = document.createElement('div');
  actionsDiv.className = 'session-actions';
  
  const editBtn = document.createElement('button');
  editBtn.className = 'btn-edit-session';
  editBtn.setAttribute('data-session', sessionId);
  editBtn.title = 'ویرایش نام';
  editBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>';
  
  const deleteBtn = document.createElement('button');
  deleteBtn.className = 'btn-delete-session';
  deleteBtn.setAttribute('data-session', sessionId);
  deleteBtn.title = 'حذف';
  deleteBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';
  
  actionsDiv.appendChild(editBtn);
  if (sessionId !== 'default') {
    actionsDiv.appendChild(deleteBtn);
  }
  
  item.appendChild(nameSpan);
  item.appendChild(actionsDiv);
  
  chatSessions.appendChild(item);
}

// Clear Current Chat
async function clearCurrentChat() {
  if (!confirm('آیا مطمئن هستید که می‌خواهید این چت را پاک کنید؟')) {
    return;
  }
  
  try {
    const response = await fetch(`/api/chat/history/${currentSessionId}`, {
      method: 'DELETE'
    });
    
    if (response.ok) {
      chatMessages.innerHTML = '';
      showWelcomeMessage();
      showToast('چت پاک شد', 'success');
      loadChatSessions();
      updateChatSessionTitle('چت جدید'); // Reset title after clearing chat
    }
  } catch (error) {
    showToast(`خطا در پاک کردن چت: ${error.message}`, 'error');
  }
}

// Delete Session
async function deleteSession(sessionId) {
  if (!confirm('آیا مطمئن هستید که می‌خواهید این سشن را حذف کنید؟')) {
    return;
  }
  
  try {
    const response = await fetch(`/api/chat/history/${sessionId}`, {
      method: 'DELETE'
    });
    
    if (response.ok) {
      if (sessionId === currentSessionId) {
        currentSessionId = 'default';
        await loadChatHistory('default');
        updateChatSessionTitle('چت جدید'); // Reset title after deleting active chat
      }
      loadChatSessions();
      showToast('سشن حذف شد', 'success');
    }
  } catch (error) {
    showToast(`خطا در حذف سشن: ${error.message}`, 'error');
  }
}

// Toggle Sidebar
function toggleSidebar() {
  const isCollapsed = sidebar.classList.toggle('collapsed');
  // No need to add/remove class to body, as chat-main adjusts its margin
  // Save state to localStorage
  localStorage.setItem('sidebarCollapsed', isCollapsed);
}

// Edit Session Name
function editSessionName(sessionId) {
  const sessionItem = $(`.session-item[data-session="${sessionId}"]`);
  if (!sessionItem) return;
  
  const nameSpan = sessionItem.querySelector('.session-name');
  if (!nameSpan) return;
  
  const originalName = nameSpan.textContent;
  nameSpan.setAttribute('contenteditable', 'true');
  nameSpan.focus();
  
  // Select all text
  const range = document.createRange();
  range.selectNodeContents(nameSpan);
  const selection = window.getSelection();
  selection.removeAllRanges();
  selection.addRange(range);
  
  const finishEdit = async () => {
    const newName = nameSpan.textContent.trim() || originalName;
    nameSpan.setAttribute('contenteditable', 'false');
    
    if (newName !== originalName && sessionId !== 'default') {
      try {
        const response = await fetch(`/api/chat/history/${sessionId}/rename`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: newName })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
          // Update session ID if it changed
          if (data.newSessionId !== sessionId) {
            sessionItem.setAttribute('data-session', data.newSessionId);
            sessionItem.querySelector('.btn-edit-session').setAttribute('data-session', data.newSessionId);
            if (sessionItem.querySelector('.btn-delete-session')) {
              sessionItem.querySelector('.btn-delete-session').setAttribute('data-session', data.newSessionId);
            }
            
            // Update current session ID if it was the active one
            if (currentSessionId === sessionId) {
              currentSessionId = data.newSessionId;
            }
          }
          
          nameSpan.textContent = data.displayName || newName;
          showToast('نام چت به‌روزرسانی شد', 'success');
          // Close sidebar after renaming a session
          if (!sidebar.classList.contains('collapsed')) {
            sidebar.classList.add('collapsed');
            localStorage.setItem('sidebarCollapsed', 'true');
          }
          updateChatSessionTitle(newName); // Update header title after successful rename
        } else {
          nameSpan.textContent = originalName;
          showToast(data.error || 'خطا در تغییر نام', 'error');
        }
      } catch (error) {
        nameSpan.textContent = originalName;
        showToast('خطا در تغییر نام', 'error');
      }
    } else {
      nameSpan.textContent = originalName;
    }
  };
  
  nameSpan.addEventListener('blur', finishEdit, { once: true });
  nameSpan.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      nameSpan.blur();
    } else if (e.key === 'Escape') {
      nameSpan.textContent = originalName;
      nameSpan.setAttribute('contenteditable', 'false');
    }
  }, { once: true });
}

// Load sidebar state from localStorage
function loadSidebarState() {
  const collapsed = localStorage.getItem('sidebarCollapsed') === 'true';
  // If no state saved, default to collapsed for this new behavior
  if (collapsed || localStorage.getItem('sidebarCollapsed') === null) {
    sidebar.classList.add('collapsed');
  } else {
    sidebar.classList.remove('collapsed');
  }
}

// Function to update the chat session title in the header
function updateChatSessionTitle(title) {
  if (chatSessionTitle) {
    chatSessionTitle.textContent = title;
  }
}

// Function to toggle between settings and history
function toggleSettingsHistory() {
  if (settingsSection.classList.contains('active')) {
    settingsSection.classList.remove('active');
    historySection.classList.add('active');
  } else {
    historySection.classList.remove('active');
    settingsSection.classList.add('active');
  }
}
