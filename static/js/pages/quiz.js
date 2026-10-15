/* ==== extracted (bridge) from template quiz.html ==== */

    // ============================================================
    // QUESTION BUILDER LOGIC
    // ============================================================
    const questionsList = document.getElementById('questionsList');
    const addQuestionBtn = document.getElementById('addQuestionBtn');
    const typePicker = document.getElementById('typePicker');
    const sumQuestions = document.getElementById('sumQuestions');
    const sumPoints = document.getElementById('sumPoints');
    const countMC = document.getElementById('countMC');
    const countExplain = document.getElementById('countExplain');
    const emptyState = document.getElementById('emptyState');

    let qCounter = window.__CFG__.cfg0;

    function updateSummary() {
      const blocks = questionsList.querySelectorAll('.q-block');
      let totalPoints = 0;
      let mcCount = 0;
      let explainCount = 0;

      blocks.forEach(b => {
        const type = b.dataset.type;
        if (type === 'explain') {
          totalPoints += 5;
          explainCount++;
        } else {
          totalPoints += 2;
          mcCount++;
        }
      });

      sumQuestions.textContent = blocks.length;
      sumPoints.textContent = totalPoints;
      countMC.textContent = mcCount;
      countExplain.textContent = explainCount;

      if (emptyState) {
        emptyState.style.display = blocks.length === 0 ? 'block' : 'none';
      }
    }

    function renumberQuestions() {
      const blocks = questionsList.querySelectorAll('.q-block');
      blocks.forEach((block, i) => {
        const idx = i + 1;
        block.querySelector('.q-index').textContent = idx;
        block.querySelector('.q-title').textContent = 'Question ' + idx;
        block.querySelectorAll('.answer-mark input[type="radio"]').forEach(r => {
          r.name = 'q' + idx + '-correct';
        });
      });
    }

    function answerRow(qNum, letter, checked) {
      return `
        <div class="answer-row">
          <label class="answer-mark">
            <input type="radio" name="q${qNum}-correct" ${checked ? 'checked' : ''}>
            <span class="circle"></span>
          </label>
          <input type="text" placeholder="Answer option ${letter}">
          <button class="del-ans" title="Remove" type="button"><i class="fas fa-xmark"></i></button>
        </div>
      `;
    }

    function createMCBlock(qNum) {
      const block = document.createElement('section');
      block.className = 'q-block';
      block.setAttribute('data-q', '');
      block.setAttribute('data-type', 'mc');

      block.innerHTML = `
        <div class="q-block-head">
          <span class="q-drag"><i class="fas fa-grip-vertical"></i></span>
          <div class="q-index">${qNum}</div>
          <div class="q-title">Question ${qNum}</div>
          <span class="q-type-badge mc"><i class="fas fa-list-ul"></i> window.__CFG__.cfg1</span>
          <div class="q-tools">
            <button class="btn-icon" title="Duplicate" data-action="duplicate" type="button"><i class="fas fa-copy"></i></button>
            <button class="btn-icon danger" title="Delete" data-action="delete" type="button"><i class="fas fa-trash-alt"></i></button>
          </div>
        </div>
        <div class="q-block-body">
          <div class="field">
            <label>window.__CFG__.cfg2</label>
            <textarea placeholder="Type your question here..."></textarea>
          </div>
          <div class="answers-label">
            <span class="al-title">window.__CFG__.cfg3</span>
            <span class="al-hint">window.__CFG__.cfg4</span>
          </div>
          <div class="answer-list">
            ${answerRow(qNum, 'A', false)}
            ${answerRow(qNum, 'B', false)}
            ${answerRow(qNum, 'C', false)}
            ${answerRow(qNum, 'D', false)}
          </div>
          <button class="add-answer" type="button"><i class="fas fa-plus"></i> window.__CFG__.cfg5</button>
        </div>
        <div class="q-block-foot">
          <div class="q-meta">
            <span><i class="fas fa-star"></i> 2 points</span>
            <span><i class="fas fa-check-circle"></i> window.__CFG__.cfg6</span>
          </div>
        </div>
      `;
      return block;
    }

    function createExplainBlock(qNum) {
      const block = document.createElement('section');
      block.className = 'q-block';
      block.setAttribute('data-q', '');
      block.setAttribute('data-type', 'explain');

      block.innerHTML = `
        <div class="q-block-head">
          <span class="q-drag"><i class="fas fa-grip-vertical"></i></span>
          <div class="q-index">${qNum}</div>
          <div class="q-title">Question ${qNum}</div>
          <span class="q-type-badge explain"><i class="fas fa-pen"></i> window.__CFG__.cfg7</span>
          <div class="q-tools">
            <button class="btn-icon" title="Duplicate" data-action="duplicate" type="button"><i class="fas fa-copy"></i></button>
            <button class="btn-icon danger" title="Delete" data-action="delete" type="button"><i class="fas fa-trash-alt"></i></button>
          </div>
        </div>
        <div class="q-block-body">
          <div class="field">
            <label>window.__CFG__.cfg2</label>
            <textarea placeholder="Type your question here..."></textarea>
          </div>
          <div class="explain-box">
            <div class="eb-head"><i class="fas fa-pen-fancy"></i> window.__CFG__.cfg8</div>
            <div class="explain-preview">
              <i class="fas fa-keyboard"></i>
              <span>window.__CFG__.cfg9</span>
            </div>
            <div class="explain-info">
              <i class="fas fa-circle-info"></i>
              <span>window.__CFG__.cfg10</span>
            </div>
          </div>
        </div>
        <div class="q-block-foot">
          <div class="q-meta">
            <span><i class="fas fa-star"></i> 5 points</span>
            <span><i class="fas fa-pen"></i> window.__CFG__.cfg11</span>
          </div>
        </div>
      `;
      return block;
    }

    addQuestionBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = typePicker.classList.contains('open');
      if (isOpen) {
        typePicker.classList.remove('open');
        addQuestionBtn.classList.remove('active');
      } else {
        typePicker.classList.add('open');
        addQuestionBtn.classList.add('active');
        typePicker.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    });

    typePicker.querySelectorAll('.type-opt').forEach(opt => {
      opt.addEventListener('click', () => {
        const type = opt.dataset.type;
        const qNum = qCounter + 1;
        qCounter++;

        const block = type === 'explain'
          ? createExplainBlock(qNum)
          : createMCBlock(qNum);

        questionsList.insertBefore(block, addQuestionBtn.parentElement);
        renumberQuestions();
        updateSummary();

        typePicker.classList.remove('open');
        addQuestionBtn.classList.remove('active');

        block.scrollIntoView({ behavior: 'smooth', block: 'center' });
        block.querySelector('textarea').focus();
      });
    });

    document.addEventListener('click', (e) => {
      if (!e.target.closest('.add-wrap')) {
        typePicker.classList.remove('open');
        addQuestionBtn.classList.remove('active');
      }
    });

    questionsList.addEventListener('click', async (e) => {
      const deleteBtn    = e.target.closest('[data-action="delete"]');
      const duplicateBtn = e.target.closest('[data-action="duplicate"]');
      const removeAnswer = e.target.closest('.del-ans');
      const addAnswer    = e.target.closest('.add-answer');

      if (deleteBtn) {
        const block = deleteBtn.closest('.q-block');
        const confirmed = await ConfirmModal.confirm({
          title: 'Delete Question',
          message: 'Delete this question?',
          confirmText: 'Delete',
          cancelText: 'Cancel'
        });
        if (confirmed) {
          block.remove();
          renumberQuestions();
          updateSummary();
        }
      }

      if (duplicateBtn) {
        const block = duplicateBtn.closest('.q-block');
        const clone = block.cloneNode(true);
        clone.querySelectorAll('textarea').forEach(t => t.value = '');
        clone.querySelectorAll('input[type="radio"]').forEach(r => r.checked = false);
        clone.querySelectorAll('.answer-row input[type="text"]').forEach(i => i.value = '');
        questionsList.insertBefore(clone, addQuestionBtn.parentElement);
        renumberQuestions();
        updateSummary();
        clone.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }

      if (removeAnswer) {
        const list = removeAnswer.closest('.answer-list');
        if (list.querySelectorAll('.answer-row').length > 2) {
          removeAnswer.closest('.answer-row').remove();
        } else {
          alert('A multiple choice question needs at least 2 answer options.');
        }
      }

      if (addAnswer) {
        const body = addAnswer.closest('.q-block-body');
        const list = body.querySelector('.answer-list');
        const block = addAnswer.closest('.q-block');
        const qIndex = Array.from(questionsList.querySelectorAll('.q-block')).indexOf(block) + 1;
        const count = list.querySelectorAll('.answer-row').length;
        const letters = ['A','B','C','D','E','F','G','H'];
        const letter = letters[count] || '?';
        const wrapper = document.createElement('div');
        wrapper.innerHTML = answerRow(qIndex, letter, false).trim();
        list.appendChild(wrapper.firstChild);
      }
    });

    updateSummary();

    // ============================================================
    // SAVE QUIZ
    // ============================================================
    function collectQuizData() {
      const payload = {
        course_id: window.COURSE_ID,
        title: document.getElementById('quizTitle').value.trim(),
        description: document.getElementById('quizDescription').value.trim(),
        subject: document.getElementById('quizSubject').value,
        chapter: document.getElementById('quizChapter').value.trim(),
        difficulty: document.getElementById('quizDifficulty').value,
        duration: parseInt(document.getElementById('quizDuration').value) || 30,
        passing_score: parseInt(document.getElementById('quizPassing').value) || 70,
        attempts_allowed: document.getElementById('quizAttempts').value,
        questions: [],
      };

      document.querySelectorAll('.q-block').forEach((block) => {
        const type = block.dataset.type;
        const text = block.querySelector('textarea').value.trim();
        const q = { type, text, points: type === 'explain' ? 5 : 2 };

        if (type === 'mc') {
          q.answers = [];
          block.querySelectorAll('.answer-row').forEach((row) => {
            q.answers.push({
              text: row.querySelector('input[type="text"]').value.trim(),
              is_correct: row.querySelector('input[type="radio"]').checked,
            });
          });
        }

        payload.questions.push(q);
      });

      return payload;
    }

    async function saveQuiz(btn) {
      if (!window.COURSE_ID) {
        alert('No course selected. Open this page from a course.');
        return;
      }

      const payload = collectQuizData();

      if (!payload.title) return alert('Please enter a quiz title.');
      if (payload.questions.length === 0) return alert('Please add at least one question.');

      for (let i = 0; i < payload.questions.length; i++) {
        const q = payload.questions[i];
        if (!q.text) {
          return alert(`Question ${i + 1}: Question text is empty.`);
        }
        if (q.type === 'mc') {
          if (!q.answers.some(a => a.is_correct)) {
            return alert(`Question ${i + 1}: Please select the correct answer.`);
          }
          if (q.answers.some(a => !a.text)) {
            return alert(`Question ${i + 1}: All answer options must have text.`);
          }
        }
      }

      const originalHTML = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

      try {
        const res = await fetch(window.SAVE_QUIZ_URL, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.CSRF_TOKEN,
          },
          credentials: 'same-origin',
          body: JSON.stringify(payload),
        });

        const data = await res.json();

        if (data.status === 'success') {
          showQuizToast(data.message || 'Quiz saved!', 'success');
          if (data.quiz_id) {
            window.QUIZ_ID = data.quiz_id;
          }
        } else {
          showQuizToast(data.message || 'Save failed', 'error');
        }
      } catch (err) {
        console.error(err);
        showQuizToast('Network error. Try again.', 'error');
      } finally {
        btn.disabled = false;
        btn.innerHTML = originalHTML;
      }
    }

    function showQuizToast(message, type) {
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

    // Bind sidebar Save button
    document.getElementById('saveQuizBtn2').addEventListener('click', function(e) {
      e.preventDefault();
      saveQuiz(this);
    });

    // ============================================================
    // PUBLISH QUIZ
    // ============================================================
    document.getElementById('publishQuizBtn')?.addEventListener('click', async function(e) {
      e.preventDefault();

      if (!window.QUIZ_ID) {
        alert('Please save the quiz first before publishing.');
        return;
      }

      const ok = await ConfirmModal.confirm({
        title: 'Publish Quiz',
        message: 'Publish this quiz?\n\nOnce published, you CANNOT change it.\nIt will become visible to students.',
        confirmText: 'Publish',
        cancelText: 'Cancel'
      });
      if (!ok) return;

      const btn = this;
      const orig = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Publishing...';

      try {
        const res = await fetch(`/quiz/publish/${window.QUIZ_ID}/`, {
          method: 'POST',
          headers: { 'X-CSRFToken': window.CSRF_TOKEN },
          credentials: 'same-origin',
        });

        const data = await res.json();

        if (data.status === 'success') {
          showQuizToast(data.message || 'Quiz published!', 'success');
          setTimeout(() => location.reload(), 1200);
        } else {
          showQuizToast(data.message || 'Publish failed', 'error');
          btn.disabled = false;
          btn.innerHTML = orig;
        }
      } catch (err) {
        console.error(err);
        showQuizToast('Network error. Try again.', 'error');
        btn.disabled = false;
        btn.innerHTML = orig;
      }
    });

    // ============================================================
    // LOCK QUIZ IF PUBLISHED
    // ============================================================
    if (window.QUIZ_IS_PUBLISHED) {
      document.querySelectorAll(
        '#questionsList input, #questionsList textarea, ' +
        '#questionsList select, #questionsList button, ' +
        '#quizTitle, #quizDescription, #quizSubject, #quizChapter, ' +
        '#quizDifficulty, #quizDuration, #quizPassing, #quizAttempts, ' +
        '#saveQuizBtn2, #publishQuizBtn'
      ).forEach(el => {
        el.disabled = true;
        el.style.pointerEvents = 'none';
        el.style.opacity = '0.5';
      });

      document.getElementById('addQuestionBtn')?.setAttribute('disabled', true);
    }
