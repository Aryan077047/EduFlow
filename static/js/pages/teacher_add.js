/* ==== extracted from template teacher_add.html ==== */

(function () {
    'use strict';

    // Add theme toggle button to left panel
    const leftPanel = document.querySelector('.auth-left');
    if (leftPanel) {
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'theme-toggle-btn';
        toggleBtn.innerHTML = '<i class="fa fa-moon"></i>';
        toggleBtn.title = 'Toggle theme';
        toggleBtn.style.cssText = `
            position: absolute;
            top: 20px;
            right: 20px;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: rgba(255, 255, 255, .15);
            border: 1px solid rgba(255, 255, 255, .25);
            color: white;
            font-size: 1rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all .3s ease;
            z-index: 10;
        `;
        toggleBtn.addEventListener('mouseenter', function() {
            this.style.background = 'rgba(255, 255, 255, .25)';
        });
        toggleBtn.addEventListener('mouseleave', function() {
            this.style.background = 'rgba(255, 255, 255, .15)';
        });
        toggleBtn.addEventListener('click', function() {
            const html = document.documentElement;
            const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', next);
            try { localStorage.setItem('theme', next); } catch (e) {}
            this.querySelector('i').className = next === 'dark' ? 'fa fa-sun' : 'fa fa-moon';
        });
        leftPanel.appendChild(toggleBtn);
    }
})();
