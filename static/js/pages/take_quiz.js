/* ==== extracted (data-bridge) from template take_quiz.html ==== */

let QUIZ_QUESTIONS = [];
try { QUIZ_QUESTIONS = JSON.parse(document.getElementById("quizQuestionsData").textContent); } catch (e) { QUIZ_QUESTIONS = []; }

    /* Questions data from Django */
    

    let currentIndex = 0;
    const total = QUIZ_QUESTIONS.length;
    const userAnswers = {};

    const $ = id => document.getElementById(id);
    const qNumDisplay  = $('qNumDisplay');
    const qNumLabel    = $('qNumLabel');
    const qPoints      = $('qPoints');
    const questionText = $('questionText');
    const answersCont  = $('answersContainer');
    const prevBtn      = $('prevBtn');
    const nextBtn      = $('nextBtn');
    const submitInline = $('submitInlineBtn');
    const submitSide   = $('submitSideBtn');
    const submitNote   = $('submitNote');
    const qGrid        = $('qGrid');
    const progressText = $('progressText');
    const progressFill = $('progressFill');
    const timerChip    = $('timerChip');
    const timerText    = $('timerText');

    /* ---------- Escape HTML ---------- */
    function escapeHtml(str) {
      return String(str)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;')
        .replace(/>/g, '&gt;').replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    }

    /* ---------- Build question map ---------- */
    function buildGrid() {
      qGrid.innerHTML = '';
      QUIZ_QUESTIONS.forEach((_, i) => {
        const dot = document.createElement('div');
        dot.className = 'q-dot';
        dot.textContent = i + 1;
        dot.dataset.index = i;
        dot.addEventListener('click', () => goTo(i));
        qGrid.appendChild(dot);
      });
    }

    /* ---------- Update question map ---------- */
    function updateGrid() {
      qGrid.querySelectorAll('.q-dot').forEach((dot, i) => {
        dot.classList.remove('answered', 'current');
        const q = QUIZ_QUESTIONS[i];
        if (userAnswers[q.id] !== undefined && userAnswers[q.id] !== '') {
          dot.classList.add('answered');
        }
        if (i === currentIndex) dot.classList.add('current');
      });
    }

    /* ---------- Update progress ---------- */
    function updateProgress() {
      const answered = Object.values(userAnswers).filter(v => v !== undefined && v !== '').length;
      progressText.textContent = `${answered} of ${total} answered`;
      progressFill.style.width = total ? (answered / total * 100) + '%' : '0%';

      const remaining = total - answered;
      submitNote.textContent = remaining === 0
        ? 'All questions answered ✓'
        : `${remaining} question${remaining !== 1 ? 's' : ''} remaining`;
    }

    /* ---------- Render question ---------- */
    function renderQuestion() {
      const q = QUIZ_QUESTIONS[currentIndex];
      if (!q) return;

      qNumDisplay.textContent = currentIndex + 1;
      qNumLabel.textContent = `Question ${currentIndex + 1} of ${total}`;
      qPoints.textContent = `${q.points} pt${q.points !== 1 ? 's' : ''}`;
      questionText.textContent = q.text;
      answersCont.innerHTML = '';

      if (q.type === 'mc') {
        const letters = ['A','B','C','D','E','F','G','H'];
        q.answers.forEach((a, i) => {
          const label = document.createElement('label');
          label.className = 'answer';
          label.innerHTML = `
            <input type="radio" name="q_${q.id}" value="${a.id}">
            <span class="letter">${letters[i] || '?'}</span>
            <span class="text">${escapeHtml(a.text)}</span>
          `;

          if (String(userAnswers[q.id]) === String(a.id)) {
            label.classList.add('selected');
            label.querySelector('input').checked = true;
          }

          label.addEventListener('click', e => {
            e.preventDefault();
            answersCont.querySelectorAll('.answer').forEach(el => el.classList.remove('selected'));
            label.classList.add('selected');
            label.querySelector('input').checked = true;
            userAnswers[q.id] = a.id;
            updateGrid();
            updateProgress();
          });

          answersCont.appendChild(label);
        });
      } else {
        const wrapper = document.createElement('div');
        wrapper.className = 'explain-answer';
        wrapper.innerHTML = `
          <label>Your answer</label>
          <textarea id="explain_${q.id}" placeholder="Type your answer here..." rows="7">${userAnswers[q.id] || ''}</textarea>
          <div class="explain-hint">
            <i class="fas fa-circle-info"></i>
            This question will be graded manually by your teacher.
          </div>
        `;
        answersCont.appendChild(wrapper);

        const ta = wrapper.querySelector('textarea');
        ta.addEventListener('input', () => {
          userAnswers[q.id] = ta.value;
          updateGrid();
          updateProgress();
        });
      }

      prevBtn.disabled = currentIndex === 0;
      if (currentIndex === total - 1) {
        nextBtn.style.display = 'none';
        submitInline.style.display = 'inline-flex';
      } else {
        nextBtn.style.display = 'inline-flex';
        submitInline.style.display = 'none';
      }

      updateGrid();
    }

    /* ---------- Go to question ---------- */
    function goTo(i) {
      if (i < 0 || i >= total) return;
      currentIndex = i;
      renderQuestion();
    }

    prevBtn.addEventListener('click', () => goTo(currentIndex - 1));
    nextBtn.addEventListener('click', () => goTo(currentIndex + 1));
    submitInline.addEventListener('click', submitQuiz);
    submitSide.addEventListener('click', submitQuiz);

    /* ---------- Submit ---------- */
    async function submitQuiz() {
      const unanswered = QUIZ_QUESTIONS.filter(q => {
        const v = userAnswers[q.id];
        return v === undefined || v === '';
      });

      const msg = unanswered.length > 0
        ? `You have ${unanswered.length} unanswered question(s). Submit anyway?`
        : 'Submit your quiz now? You cannot change your answers after.';

      const confirmed = await ConfirmModal.confirm({
        title: 'Submit Quiz',
        message: msg,
        confirmText: 'Submit',
        cancelText: 'Cancel'
      });

      if (!confirmed) return;

      if (!window.QUIZ_ID) { alert('Quiz ID not found.'); return; }

      const payload = {
        quiz_id: window.QUIZ_ID,
        answers: QUIZ_QUESTIONS.map(q => {
          const v = userAnswers[q.id];
          return q.type === 'mc'
            ? { question_id: q.id, answer_id: v || null }
            : { question_id: q.id, text: v || '' };
        })
      };

      [submitSide, submitInline].forEach(b => {
        b.disabled = true;
        b.dataset.orig = b.innerHTML;
        b.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
      });

      const restore = () => {
        [submitSide, submitInline].forEach(b => {
          b.disabled = false;
          b.innerHTML = b.dataset.orig;
        });
      };

      try {
        const res = await fetch(window.SUBMIT_URL, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.CSRF_TOKEN,
          },
          credentials: 'same-origin',
          body: JSON.stringify(payload),
        });

        let data = null;
        try { data = await res.json(); }
        catch {
          showToast(res.status ? `Submit failed (HTTP ${res.status}). Try again.` : 'Network error. Try again.', 'error');
          restore();
          return;
        }

        if (data.status === 'success') {
          window.location.href = data.redirect_url || `attempt_detail/${data.attempt_id}/`;
        } else {
          showToast(data.message || 'Submit failed', 'error');
          restore();
        }
      } catch (err) {
        console.error(err);
        showToast('Network error. Try again.', 'error');
        restore();
      }
    }

    /* ---------- Toast ---------- */
    function showToast(message, type) {
      const t = document.createElement('div');
      t.textContent = message;
      t.style.cssText = `
        position:fixed; bottom:30px; right:30px; z-index:9999;
        background:${type === 'error' ? '#dc2626' : '#18311f'};
        color:white; padding:12px 20px; border-radius:12px;
        font-family:'Plus Jakarta Sans',sans-serif; font-weight:600;
        font-size:.85rem; box-shadow:0 10px 25px rgba(0,0,0,.2);
        opacity:0; transition:opacity .3s ease;
      `;
      document.body.appendChild(t);
      requestAnimationFrame(() => t.style.opacity = '1');
      setTimeout(() => {
        t.style.opacity = '0';
        setTimeout(() => t.remove(), 300);
      }, 2500);
    }

    /* ---------- Timer ---------- */
    let timeLeft = (window.QUIZ_DURATION || 30) * 60;
    let timerInterval = null;

    function updateTimer() {
      if (timeLeft <= 0) {
        clearInterval(timerInterval);
        alert('Time is up! Your quiz will be submitted automatically.');
        submitQuiz();
        return;
      }
      const m = Math.floor(timeLeft / 60);
      const s = timeLeft % 60;
      timerText.textContent = `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
      if (timeLeft <= 300) timerChip.classList.add('danger');
      timeLeft--;
    }

    /* ---------- Init ---------- */
    buildGrid();
    renderQuestion();
    updateProgress();

    if (total > 0) {
      updateTimer();
      timerInterval = setInterval(updateTimer, 1000);
    }
  
