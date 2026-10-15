/**
 * Confirmation Modal - Reusable styled confirm dialog
 * Replaces native confirm() with a styled modal
 * 
 * Usage:
 *   ConfirmModal.show({
 *     title: 'Delete Course',
 *     message: 'Are you sure you want to delete "Course Name"?',
 *     confirmText: 'Delete',
 *     cancelText: 'Cancel',
 *     onConfirm: () => { /* handle delete *\/ },
 *     onCancel: () => { /* optional *\/ }
 *   });
 * 
 * For simple link/button confirmation with data-confirm attribute:
 *   <a href="/delete/1/" data-confirm="Are you sure?">Delete</a>
 */

(function () {
  'use strict';

  // Create modal HTML if it does not already exist; always make sure its
  // event listeners are attached (the markup may be pre-rendered by the
  // template, so "element exists" alone must not skip event wiring).
  function ensureModal() {
    if (document.getElementById('confirmModal')) {
      initModalEvents();
      return;
    }
    const modalHtml = `
      <div class="confirm-modal-overlay" id="confirmModal" role="dialog" aria-modal="true" aria-labelledby="confirmModalTitle" style="display: none;">
        <div class="confirm-modal">
          <div class="confirm-modal-header">
            <h3 class="confirm-modal-title" id="confirmModalTitle">Confirm Action</h3>
            <button type="button" class="confirm-modal-close" id="confirmModalClose" aria-label="Close">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <div class="confirm-modal-body">
            <p class="confirm-modal-message" id="confirmModalMessage"></p>
          </div>
          <div class="confirm-modal-footer">
            <button type="button" class="btn btn-secondary" id="confirmModalCancel">Cancel</button>
            <button type="button" class="btn btn-danger" id="confirmModalConfirm">Delete</button>
          </div>
        </div>
      </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    initModalEvents();
  }

  let currentResolve = null;
  let currentConfig = null;

  const overlay = () => document.getElementById('confirmModal');
  const titleEl = () => document.getElementById('confirmModalTitle');
  const messageEl = () => document.getElementById('confirmModalMessage');
  const confirmBtn = () => document.getElementById('confirmModalConfirm');
  const cancelBtn = () => document.getElementById('confirmModalCancel');
  const closeBtn = () => document.getElementById('confirmModalClose');

  function initModalEvents() {
    const o = overlay();
    if (!o || o.dataset.eventsBound) return;
    o.dataset.eventsBound = 'true';

    // Close on overlay click
    o.addEventListener('click', (e) => {
      if (e.target === o) hide(false);
    });

    // Close button
    closeBtn()?.addEventListener('click', () => hide(false));

    // Cancel button
    cancelBtn()?.addEventListener('click', () => hide(false));

    // Confirm button
    confirmBtn()?.addEventListener('click', () => hide(true));

    // Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && o.classList.contains('show')) {
        hide(false);
      }
    });

    // Trap focus within modal when open
    o.addEventListener('keydown', (e) => {
      if (e.key === 'Tab' && o.classList.contains('show')) {
        const focusable = o.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    });
  }

  function show(config) {
    return new Promise((resolve) => {
      ensureModal();
      const o = overlay();
      if (!o) {
        resolve(false);
        return;
      }

      // If a dialog is already open, instantly resolve the previous request as
      // cancelled so its awaiting code never hangs.
      if (o.classList.contains('show') && currentResolve) {
        const prev = currentResolve;
        currentResolve = null;
        prev(false);
      }

      currentResolve = resolve;
      currentConfig = config = {
        title: config?.title || 'Confirm Action',
        message: config?.message || 'Are you sure?',
        confirmText: config?.confirmText || 'Delete',
        cancelText: config?.cancelText || 'Cancel',
        danger: config?.danger !== false,
        onConfirm: config?.onConfirm,
        onCancel: config?.onCancel
      };

      // Update modal content
      titleEl().textContent = config.title;
      messageEl().textContent = config.message;
      confirmBtn().textContent = config.confirmText;
      cancelBtn().textContent = config.cancelText;

      // Style confirm button based on danger level
      confirmBtn().className = 'btn ' + (config.danger ? 'btn-danger' : 'btn-primary');

      // Show modal
      o.style.display = 'flex';
      // Force reflow for animation
      o.offsetHeight;
      o.classList.add('show');

      // Focus confirm button for keyboard users
      setTimeout(() => confirmBtn()?.focus(), 50);
    });
  }

  function hide(confirmed) {
    const o = overlay();
    if (!o) return;

    o.classList.remove('show');
    setTimeout(() => {
      o.style.display = 'none';
    }, 250);

    if (currentResolve) {
      currentResolve(confirmed);
      currentResolve = null;
    }

    if (confirmed && currentConfig?.onConfirm) {
      currentConfig.onConfirm();
    } else if (!confirmed && currentConfig?.onCancel) {
      currentConfig.onCancel();
    }
    currentConfig = null;
  }

  // Public API
  window.ConfirmModal = {
    show,
    hide: () => hide(false),
    confirm: (config) => show({ ...config, danger: true }),
    info: (config) => show({ ...config, danger: false })
  };

  /**
   * Auto-bind data-confirm attributes on links/buttons.
   * Usage: <a href="/delete/1/" data-confirm="Are you sure?">Delete</a>
   *        <button type="submit" form="f" formaction="/delete/">Delete</button>
   *        <button data-confirm="Delete?" data-confirm-callback="myFunction">Delete</button>
   *
   * IMPORTANT: preventDefault() must run synchronously in the click handler.
   * If it runs after an await, the browser has already followed the link /
   * submitted the form and the modal can no longer control the action.
   */
  function bindDataConfirm() {
    document.querySelectorAll('[data-confirm]').forEach((el) => {
      if (el.dataset.confirmBound) return;
      el.dataset.confirmBound = 'true';

      el.addEventListener('click', async (e) => {
        // Cancel the browser's action up-front, synchronously. We replay it
        // ourselves only if the user confirms.
        e.preventDefault();
        e.stopPropagation();

        const message = el.dataset.confirm;
        const confirmText = el.dataset.confirmText || 'Delete';
        const cancelText = el.dataset.cancelText || 'Cancel';
        const callback = el.dataset.confirmCallback;

        const href = el.getAttribute('href') || '';
        const isLink = el.tagName === 'A' && href && href !== '#';
        const isFormSubmit = (el.type === 'submit' || el.getAttribute('form')) && !!el.form;

        const confirmed = await show({
          title: el.dataset.confirmTitle || 'Confirm Action',
          message,
          confirmText,
          cancelText,
          danger: el.dataset.confirmDanger !== 'false'
        });

        if (!confirmed) return false;

        // Optional callback takes precedence
        if (callback && typeof window[callback] === 'function') {
          window[callback](el, confirmed);
          return false;
        }

        // Replay the action we cancelled earlier
        if (isLink) {
          window.location.href = href;
        } else if (isFormSubmit) {
          // requestSubmit runs the form's regular submit flow (incl. validators
          // and submit buttons with formaction); fallback covers old browsers.
          if (typeof el.form.requestSubmit === 'function') {
            el.form.requestSubmit(el);
          } else {
            el.form.submit();
          }
        }
        return false;
      });
    });
  }

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bindDataConfirm);
  } else {
    bindDataConfirm();
  }

  // Also bind for dynamically added content (SPA re-renders, HTMX, deep
  // children of any inserted DOM node).
  document.addEventListener('ajaxComplete', bindDataConfirm);
  document.addEventListener('htmx:afterSettle', bindDataConfirm);

  if (typeof MutationObserver === 'function') {
    new MutationObserver(bindDataConfirm).observe(document.documentElement, {
      childList: true,
      subtree: true
    });
  }

})();