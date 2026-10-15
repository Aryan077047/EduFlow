/* ==== extracted from template dashboard.html ==== */

/* 🌙 Theme Toggle */
(function () {
    const btn = document.getElementById('themeToggle');
    const icon = document.getElementById('themeIcon');
    if (!btn) return;

    function updateIcon() {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        icon.className = isDark ? 'fa fa-sun' : 'fa fa-moon';
    }
    updateIcon();

    btn.addEventListener('click', (e) => {
        e.preventDefault();
        const html = document.documentElement;
        const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        html.setAttribute('data-theme', next);
        localStorage.setItem('theme', next);
        updateIcon();
    });

    new MutationObserver(updateIcon).observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-theme']
    });
})();

/* Sidebar active + smooth scroll */
document.querySelectorAll('.sidebar-link').forEach(link => {
    link.addEventListener('click', function (e) {
        if (!this.dataset.scroll) {
            if (this.getAttribute('href') === '#') e.preventDefault();
            return;
        }
        e.preventDefault();
        document.querySelectorAll('.sidebar-link').forEach(l => l.classList.remove('active'));
        this.classList.add('active');

        const target = document.getElementById(this.dataset.scroll);
        if (target) {
            const top = target.getBoundingClientRect().top + window.scrollY - 20;
            window.scrollTo({ top, behavior: 'smooth' });
        }
    });
});

/* Stat card click → scroll to section */
document.querySelectorAll('.stat-card[data-scroll]').forEach(card => {
    card.addEventListener('click', () => {
        const target = document.getElementById(card.dataset.scroll);
        if (target) {
            const top = target.getBoundingClientRect().top + window.scrollY - 20;
            window.scrollTo({ top, behavior: 'smooth' });
        }
    });
});

/* Global search */
const globalSearch = document.getElementById('globalSearch');
globalSearch.addEventListener('input', function () {
    const q = this.value.toLowerCase().trim();

    document.querySelectorAll('.data-table tbody tr').forEach(row => {
        const name = row.dataset.name || row.textContent.toLowerCase();
        row.style.display = (q === '' || name.includes(q)) ? '' : 'none';
    });

    document.querySelectorAll('.staff-row').forEach(card => {
        const name = card.dataset.name || card.textContent.toLowerCase();
        card.style.display = (q === '' || name.includes(q)) ? '' : 'none';
    });
});

/* Toast helper */
const toast = document.getElementById('toast');
const toastMsg = document.getElementById('toastMsg');
let toastTimer;

function showToast(message, type = 'success') {
    toastMsg.textContent = message;
    toast.querySelector('i').className = type === 'success'
        ? 'fa fa-check-circle'
        : 'fa fa-times-circle';
    toast.style.background = type === 'success' ? '#18311f' : '#b91c1c';
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('show'), 2600);
}

/* View / Edit buttons (demo) */
document.querySelectorAll('.icon-btn.view').forEach(btn => {
    btn.addEventListener('click', function () {
        const name = this.closest('tr')?.querySelector('.name')?.textContent || 'item';
        showToast(`Viewing: ${name}`);
    });
});

document.querySelectorAll('.icon-btn.edit').forEach(btn => {
    btn.addEventListener('click', function () {
        const name = this.closest('tr')?.querySelector('.name')?.textContent || 'item';
        showToast(`Editing: ${name}`);
    });
});

/* Add buttons (demo) */
document.querySelectorAll('.add-btn').forEach(btn => {
    btn.addEventListener('click', function () {
        const label = this.textContent.trim().replace(/^\s+/, '');
        showToast(`${label} — form would open here`);
    });
});
