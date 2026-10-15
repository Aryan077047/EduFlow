/* ==== extracted from template header.html ==== */

(function () {
    'use strict';

    var themeBtn = document.getElementById('themeToggle');
    var themeIcon = document.getElementById('themeIcon');
    var html = document.documentElement;

    function updateThemeIcon() {
        if (!themeIcon) return;
        themeIcon.className = html.getAttribute('data-theme') === 'dark'
            ? 'fa fa-sun'
            : 'fa fa-moon';
    }
    updateThemeIcon();

    if (themeBtn) {
        themeBtn.addEventListener('click', function () {
            var next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', next);
            try { localStorage.setItem('theme', next); } catch (e) {}
            updateThemeIcon();
        });
    }

    var profileBtn = document.getElementById('profileBtn');
    var profileMenu = document.getElementById('profileMenu');
    if (profileBtn && profileMenu) {
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

    var header = document.querySelector('.main-header');
    if (header) {
        var onScroll = function () {
            header.classList.toggle('scrolled', window.scrollY > 50);
        };
        window.addEventListener('scroll', onScroll, { passive: true });
        onScroll();
    }

    document.addEventListener('keydown', function (e) {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            var s = document.getElementById('globalSearch');
            if (s) s.focus();
        }
    });
})();

function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
    } else {
        document.exitFullscreen();
    }
}
