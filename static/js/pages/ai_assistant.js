/* ==== AI Study Assistant — conversations sidebar + chat pane ==== */

(function () {
  'use strict';

  const shell = document.querySelector('.ai-shell');
  const chatBody = document.getElementById('chatBody');
  const input = document.getElementById('questionInput');
  const sendBtn = document.getElementById('sendBtn');
  const clearBtn = document.getElementById('clearChatBtn');
  const statusBox = document.getElementById('aiStatus');
  const courseSelect = document.getElementById('courseSelect');
  const charCount = document.getElementById('charCount');
  const sidebar = document.getElementById('aiSidebar');
  const sidebarToggle = document.getElementById('sidebarToggle');

  /* The conversation this page opened with ('' = fresh chat). */
  let conversationId = (shell && shell.dataset.conversationId) || '';

  /* ====================== HELPERS ====================== */

  function esc(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }

  function csrfToken() {
    const el = document.querySelector('input[name=csrfmiddlewaretoken]');
    if (el) return el.value;
    const m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  function postJSON(url, body) {
    return fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken(),
      },
      body: JSON.stringify(body || {}),
    });
  }

  function pageTitle() {
    const el = document.querySelector('.ai-head-title h1');
    return el ? el.textContent.trim() : '';
  }

  function addMessage(role, text) {
    const wrap = document.createElement('div');
    wrap.className = 'msg ' + role;
    const icon = role === 'assistant' ? 'fa-robot' : 'fa-user';
    wrap.innerHTML =
      '<div class="avatar"><i class="fa-solid ' + icon + '"></i></div>' +
      '<div class="bubble"></div>';
    wrap.querySelector('.bubble').textContent = text;
    chatBody.appendChild(wrap);
    chatBody.scrollTop = chatBody.scrollHeight;
    return wrap;
  }

  function showStatus(kind, html) {
    statusBox.hidden = false;
    statusBox.innerHTML = '<div class="alert alert-' + kind + '">' +
      '<i class="fa-solid ' + (kind === 'error' ? 'fa-circle-exclamation' : 'fa-circle-info') + '"></i>' +
      '<span>' + html + '</span></div>';
  }

  function hideStatus() { statusBox.hidden = true; statusBox.innerHTML = ''; }

  /* Keep the sidebar in sync after the first exchange of a new chat. */
  function ensureSidebarEntry(id, title) {
    let item = document.querySelector('.ai-chat-item[data-id="' + id + '"]');
    if (!item) {
      const list = document.getElementById('chatList');
      const empty = list.querySelector('.ai-chat-empty');
      if (empty) empty.remove();
      item = document.createElement('div');
      item.className = 'ai-chat-item active';
      item.dataset.id = id;
      item.innerHTML =
        '<a class="ai-chat-link" href="' + window.__CFG__.PAGE + '?c=' + id + '">' +
        '<i class="fa fa-comment-dots"></i><span class="ai-chat-name"></span></a>' +
        '<button type="button" class="ai-chat-del" title="Delete chat">' +
        '<i class="fa fa-trash-can"></i></button>';
      list.prepend(item);
    } else {
      document.querySelectorAll('.ai-chat-item').forEach(function (el) {
        el.classList.remove('active');
      });
      item.classList.add('active');
    }
    item.querySelector('.ai-chat-name').textContent = title;
    if (pageTitle() && !document.querySelector('.ai-head-title h1').dataset.fixed) {
      document.querySelector('.ai-head-title h1').textContent = title;
      document.querySelector('.ai-head-title h1').dataset.fixed = '1';
    }
    conversationId = id;
  }

  /* ====================== SIDEBAR DRAWER (mobile) ====================== */

  if (sidebarToggle) {
    const overlay = document.createElement('div');
    overlay.className = 'ai-overlay';
    sidebarToggle.parentNode.insertBefore(overlay, sidebarToggle);

    function closeDrawer() {
      sidebar.classList.remove('open');
      overlay.classList.remove('show');
    }
    sidebarToggle.addEventListener('click', function () {
      sidebar.classList.toggle('open');
      overlay.classList.toggle('show', sidebar.classList.contains('open'));
    });
    overlay.addEventListener('click', closeDrawer);
    sidebar.addEventListener('click', function (e) {
      if (e.target.closest('a')) closeDrawer();
    });
  }

  /* ====================== ASK ====================== */

  async function ask() {
    const question = input.value.trim();
    if (!question || sendBtn.disabled) return;

    addMessage('user', question);
    input.value = '';
    charCount.textContent = '0 / 2000';
    hideStatus();
    sendBtn.disabled = true;
    const typing = addMessage('assistant', '');
    typing.querySelector('.bubble').innerHTML =
      '<span class="typing"><span></span><span></span><span></span></span>';
    chatBody.scrollTop = chatBody.scrollHeight;

    try {
      const response = await fetch(window.__CFG__.CFG0, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken(),
        },
        body: JSON.stringify({
          question: question,
          course_id: courseSelect ? courseSelect.value : null,
          conversation_id: conversationId ? Number(conversationId) : null,
        }),
      });
      const payload = await response.json().catch(() => ({}));

      if (payload.success) {
        typing.querySelector('.bubble').textContent = payload.reply;
        chatBody.scrollTop = chatBody.scrollHeight;
        if (payload.conversation && payload.conversation.id) {
          ensureSidebarEntry(payload.conversation.id, payload.conversation.title);
        }
      } else {
        typing.remove();
        showStatus('error', esc(payload.error || 'Something went wrong. Please try again.'));
        input.value = question;
      }
    } catch (err) {
      typing.remove();
      showStatus('error', 'Could not reach the server. Check your connection and try again.');
      input.value = question;
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  }

  sendBtn.addEventListener('click', ask);
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      ask();
    }
  });
  input.addEventListener('input', function () {
    charCount.textContent = input.value.length + ' / 2000';
  });

  /* ====================== CLEAR CURRENT CHAT ====================== */

  if (clearBtn) {
    clearBtn.addEventListener('click', async function () {
      const confirmed = await ConfirmModal.confirm({
        title: 'Clear Conversation',
        message: 'Delete this conversation? This cannot be undone.',
        confirmText: 'Delete',
        cancelText: 'Cancel'
      });
      if (!confirmed) return;
      try {
        await postJSON(window.__CFG__.CFG1, {
          conversation_id: conversationId ? Number(conversationId) : null,
        });
      } catch (err) { /* the reload below still empties the view */ }
      window.location.href = window.__CFG__.PAGE + '?new=1';
    });
  }

  /* ====================== DELETE A SIDEBAR CHAT ====================== */

  document.getElementById('chatList').addEventListener('click', async function (e) {
    const btn = e.target.closest('.ai-chat-del');
    if (!btn) return;
    e.preventDefault();
    const id = btn.dataset.id;
    const item = btn.closest('.ai-chat-item');
    if (!id || !item) return;

    const confirmed = await ConfirmModal.confirm({
      title: 'Delete Chat',
      message: 'Delete this chat and its messages?',
      confirmText: 'Delete',
      cancelText: 'Cancel'
    });

    if (!confirmed) return;

    try {
      const response = await postJSON(window.__CFG__.CFG2, {
        conversation_id: Number(id),
      });
      const payload = await response.json().catch(() => ({}));
      if (!payload.success) {
        showStatus('error', esc(payload.error || 'Could not delete the chat.'));
        return;
      }
      item.remove();
      if (String(id) === String(conversationId)) {
        window.location.href = window.__CFG__.PAGE + '?new=1';
      }
      if (!document.getElementById('chatList').querySelector('.ai-chat-item')) {
        document.getElementById('chatList').innerHTML =
          '<div class="ai-chat-empty">No chats yet.<br>Your conversations will appear here.</div>';
      }
    } catch (err) {
      showStatus('error', 'Could not reach the server.');
    }
  });

  input.focus();
})();
