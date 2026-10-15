/* ============================================================
   COMMON JAVASCRIPT - Shared utilities for all pages
============================================================ */

// Theme initialization (must run before CSS loads to prevent flash)
(function () {
    try {
        var saved = localStorage.getItem('theme');
        var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        document.documentElement.setAttribute(
            'data-theme',
            saved || (prefersDark ? 'dark' : 'light')
        );
    } catch (e) {
        document.documentElement.setAttribute('data-theme', 'light');
    }
})();

// RTL font support
(function () {
    var dir = document.documentElement.getAttribute('dir');
    if (dir === 'rtl') {
        var link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = 'https://fonts.googleapis.com/css2?family=Noto+Naskh+Arabic:wght@400;600;700;800&display=swap';
        document.head.appendChild(link);
    }
})();

// Get CSRF token
function getCSRFToken() {
    const el = document.querySelector('[name=csrfmiddlewaretoken]');
    if (el && el.value) return el.value;
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Toast helper
function showToast(message, type) {
    type = type || 'info';
    const toast = document.createElement('div');
    toast.className = 'toast toast-' + type;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(function () { toast.remove(); }, 3000);
}

// Toggle theme
function toggleTheme() {
    var html = document.documentElement;
    var next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    try { localStorage.setItem('theme', next); } catch (e) {}
    var icon = document.getElementById('themeIcon');
    if (icon) {
        icon.className = next === 'dark' ? 'fa fa-sun' : 'fa fa-moon';
    }
}

// Toggle fullscreen
function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
    } else {
        document.exitFullscreen();
    }
}

// Header scroll effect
function initHeaderScroll() {
    var header = document.querySelector('.main-header');
    if (!header) return;
    var onScroll = function () {
        header.classList.toggle('scrolled', window.scrollY > 50);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
}

// Profile dropdown
function initProfileDropdown() {
    var profileBtn = document.getElementById('profileBtn');
    var profileMenu = document.getElementById('profileMenu');
    if (!profileBtn || !profileMenu) return;
    profileBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        profileMenu.classList.toggle('active');
    });
    document.addEventListener('click', function (e) {
        if (!profileBtn.contains(e.target) && !profileMenu.contains(e.target)) {
            profileMenu.classList.remove('active');
        }
    });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') profileMenu.classList.remove('active');
    });
}

// Global search focus (Ctrl+K)
function initGlobalSearch() {
    document.addEventListener('keydown', function (e) {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            var s = document.getElementById('globalSearch');
            if (s) s.focus();
        }
    });
}

// Initialize common functionality
document.addEventListener('DOMContentLoaded', function () {
    initHeaderScroll();
    initProfileDropdown();
    initGlobalSearch();
});