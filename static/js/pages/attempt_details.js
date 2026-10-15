/* ==== extracted from template attempt_details.html ==== */

const ATTEMPT_ID = window.__PAGECFG__.ATTEMPT_ID;
const CSRF_TOKEN = window.__PAGECFG__.CSRF_TOKEN;

    function showToast(msg, type) {
      const t = document.createElement('div');
      t.className = 'toast';
      t.textContent = msg;
      t.style.background = type === 'error' ? '#dc2626' : '#18311f';
      document.body.appendChild(t);
      requestAnimationFrame(() => t.style.opacity = '1');
      setTimeout(() => {
        t.style.opacity = '0';
        setTimeout(() => t.remove(), 300);
      }, 2500);
    }

    document.getElementById('saveGradesBtn').addEventListener('click', async function () {
      const btn = this;
      const cards = document.querySelectorAll('.answer-card[data-question-type="explain"]');
      const grades = [];

      cards.forEach(card => {
        const answerId = parseInt(card.dataset.answerId);
        const maxPts   = parseFloat(card.dataset.maxPoints);
        const pointsEl = card.querySelector('.grade-points');
        const feedEl   = card.querySelector('.grade-feedback');

        let pts = parseFloat(pointsEl.value);
        if (isNaN(pts)) pts = 0;
        pts = Math.max(0, Math.min(pts, maxPts));

        grades.push({
          answer_id: answerId,
          points:    pts,
          feedback:  feedEl ? feedEl.value.trim() : '',
        });
      });

      btn.disabled = true;
      const orig = btn.innerHTML;
      btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

      try {
        const res = await fetch(`/quiz/attempt/${ATTEMPT_ID}/grade/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': CSRF_TOKEN,
          },
          credentials: 'same-origin',
          body: JSON.stringify({ grades }),
        });

        const data = await res.json();
        if (data.status === 'success') {
          showToast('Grades saved!', 'success');
          setTimeout(() => location.reload(), 800);
        } else {
          showToast(data.message || 'Save failed', 'error');
        }
      } catch (err) {
        console.error(err);
        showToast('Network error.', 'error');
      } finally {
        btn.disabled = false;
        btn.innerHTML = orig;
      }
    });
  
