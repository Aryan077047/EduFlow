/* ==== extracted from template setting.html ==== */

  (function () {
      const sw = document.getElementById('darkModeSwitch');
      if (!sw) return;
      const html = document.documentElement;

      const sync = () => {
          sw.checked = html.getAttribute('data-theme') === 'dark';
      };
      sync();

      sw.addEventListener('change', () => {
          const next = sw.checked ? 'dark' : 'light';
          html.setAttribute('data-theme', next);
          localStorage.setItem('theme', next);
      });

      new MutationObserver(sync).observe(html, {
          attributes: true,
          attributeFilter: ['data-theme']
      });
  })();
  
