/* ============================================================
   INDEX PAGE JAVASCRIPT
============================================================ */

function getCSRFToken() {
    const el = document.querySelector('[name=csrfmiddlewaretoken]');
    if (el && el.value) return el.value;
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/* ====================== COURSE SEARCH ====================== */
document.addEventListener('DOMContentLoaded', function() {
    const videoCards = document.querySelectorAll('.video-card');
    const globalSearch = document.getElementById('globalSearch');

    function filterCourses(searchTerm) {
        searchTerm = searchTerm.toLowerCase().trim();

        videoCards.forEach(card => {
            const title = card.querySelector('.video-title')?.textContent.toLowerCase() || '';
            const description = card.querySelector('.video-description')?.textContent.toLowerCase() || '';
            const category = card.querySelector('.video-category')?.textContent.toLowerCase() || '';
            const instructor = card.querySelector('.author-name')?.textContent.toLowerCase() || '';

            const matches = title.includes(searchTerm) ||
                            description.includes(searchTerm) ||
                            category.includes(searchTerm) ||
                            instructor.includes(searchTerm);

            card.style.display = matches ? 'flex' : 'none';
        });

        // Show empty state if no results
        const visibleCards = Array.from(videoCards).filter(card => card.style.display !== 'none');
        const emptyState = document.querySelector('.empty-state');
        if (emptyState) {
            if (visibleCards.length === 0 && searchTerm !== '') {
                emptyState.style.display = 'block';
                emptyState.innerHTML = '<i class="fa fa-search"></i><p>No courses found matching your search.</p>';
            } else {
                emptyState.style.display = 'none';
            }
        }
    }

    // Global search in header - only works on index page
    if (globalSearch && videoCards.length > 0) {
        globalSearch.addEventListener('input', function() {
            filterCourses(this.value);
        });
    }
});

/* 1. LIKE */
document.querySelectorAll('.like-stat').forEach(btn => {
    btn.addEventListener('click', function () {
        const courseId = this.dataset.courseId;
        const likeSpan = this.querySelector('.like-count');
        const icon = this.querySelector('i');

        fetch(`/like-course/${courseId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json'
            }
        })
        .then(r => r.json())
        .then(data => {
            if (data.status === 'liked') {
                likeSpan.textContent = data.likes;
                icon.style.color = '#dc2626';
                this.classList.add('liked');
            } else if (data.status === 'unliked') {
                likeSpan.textContent = data.likes;
                icon.style.color = '#5d9c59';
                this.classList.remove('liked');
            }
        })
        .catch(err => console.error('Like error:', err));
    });
});

/* 2. ENROLL (only exists if user logged in) */
document.querySelectorAll('.btn-enroll').forEach(btn => {
    btn.addEventListener('click', function (e) {
        e.preventDefault();

        if (this.dataset.enrolled === 'true') {
            alert('You are already enrolled in this course!');
            return;
        }
        if (this.dataset.submitting === 'true') return;

        this.dataset.submitting = 'true';
        const url = this.dataset.url;
        const textSpan = this.querySelector('.enroll-text');
        const originalHTML = textSpan.innerHTML;
        textSpan.innerHTML = '...';

        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(r => {
            if (r.redirected) {
                window.location.href = r.url;
                return Promise.resolve({ _redirected: true });
            }
            if (!r.ok) return r.json().catch(() => ({}));
            return r.json();
        })
        .then(data => {
            if (data && data._redirected) return;
            if (data && data.checkout_url) {
                window.location.href = data.checkout_url;
                return;
            }
            if (data && data.status === 'info') {
                alert(data.message || 'You are already enrolled in this course!');
                return;
            }
            if (data && data.status === 'error') {
                alert(data.error || 'Enrollment failed.');
                return;
            }
            this.classList.add('enrolled');
            this.dataset.enrolled = 'true';
            textSpan.innerHTML = '✓ Enrolled';
        })
        .catch(err => {
            console.error('Enroll error:', err);
            textSpan.innerHTML = originalHTML;
        })
        .finally(() => {
            this.dataset.submitting = 'false';
        });
    });
});

/* 3. TOGGLE COMMENTS */
document.querySelectorAll('.comment-stat').forEach(btn => {
    btn.addEventListener('click', function () {
        const courseId = this.dataset.courseId;
        const section = document.getElementById(`comment-section-${courseId}`);
        if (!section) return;

        if (section.style.display === 'none' || section.style.display === '') {
            section.style.display = 'block';
            setTimeout(() => {
                section.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }, 100);
        } else {
            section.style.display = 'none';
        }
    });
});

/* 4. SUBMIT COMMENT */
document.querySelectorAll('.comment-submit').forEach(btn => {
    btn.addEventListener('click', function () {
        const courseId = this.dataset.courseId;
        const input = document.getElementById(`comment-input-${courseId}`);
        const text = input.value.trim();
        if (!text) return;

        this.disabled = true;
        const oldLabel = this.textContent;
        this.textContent = '...';

        fetch(`/add-comment/${courseId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: text })
        })
        .then(r => r.json())
        .then(data => {
            if (data.status !== 'success') {
                alert(data.error || 'Error sending comment');
                return;
            }

            const list = document.getElementById(`comment-list-${courseId}`);
            const emptyMsg = list.querySelector('.comment-empty');
            if (emptyMsg) emptyMsg.remove();

            const newComment = document.createElement('div');
            newComment.className = 'comment-item';
            newComment.dataset.commentId = data.comment_id;
            newComment.innerHTML = `
                <div class="comment-text">
                    <span class="comment-author">${escapeHtml(data.author)}:</span>
                    ${escapeHtml(text)}
                    <span class="comment-time">just now</span>
                </div>
                <button class="remove-comment-btn" data-comment-id="${data.comment_id}">
                    <i class="fa fa-times-circle"></i>
                </button>
            `;
            list.insertAdjacentElement('afterbegin', newComment);
            input.value = '';

            const countSpan = document.querySelector(
                `.comment-stat[data-course-id="${courseId}"] .comment-count`
            );
            if (countSpan) {
                countSpan.textContent = (parseInt(countSpan.textContent) || 0) + 1;
            }

            const items = list.querySelectorAll('.comment-item:not(.comment-empty)');
            if (items.length > 5) {
                items[items.length - 1].remove();
            }
        })
        .catch(err => console.error('Comment error:', err))
        .finally(() => {
            this.disabled = false;
            this.textContent = oldLabel;
        });
    });
});

/* 5. REMOVE COMMENT */
document.addEventListener('click', async function (e) {
    const btn = e.target.closest('.remove-comment-btn');
    if (!btn) return;
    e.stopPropagation();

    const commentId = btn.dataset.commentId;
    const item = btn.closest('.comment-item');
    const section = item.closest('.comment-section');
    const courseId = section.id.replace('comment-section-', '');

    const confirmed = await ConfirmModal.confirm({
      title: 'Delete Comment',
      message: 'Delete this comment?',
      confirmText: 'Delete',
      cancelText: 'Cancel'
    });

    if (!confirmed) return;

    fetch(`/remove-comment/${commentId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json'
        }
    })
    .then(r => r.json())
    .then(data => {
        if (data.status !== 'removed') return;
        item.remove();

        const countSpan = document.querySelector(
            `.comment-stat[data-course-id="${courseId}"] .comment-count`
        );
        if (countSpan) {
            countSpan.textContent = Math.max(
                0, (parseInt(countSpan.textContent) || 0) - 1
            );
        }

        const list = document.getElementById(`comment-list-${courseId}`);
        if (!list.querySelector('.comment-item')) {
            const emptyMsg = document.createElement('div');
            emptyMsg.className = 'comment-item comment-empty';
            emptyMsg.style.color = '#9ca3af';
            emptyMsg.style.fontStyle = 'italic';
            emptyMsg.style.justifyContent = 'center';
            emptyMsg.textContent = 'No comments yet';
            list.appendChild(emptyMsg);
        }
    })
    .catch(err => console.error('Remove error:', err));
});

/* 6. ENTER KEY = SUBMIT COMMENT */
document.querySelectorAll('.comment-input').forEach(input => {
    input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const btn = this.closest('.comment-input-wrapper')
                .querySelector('.comment-submit');
            if (btn) btn.click();
        }
    });
});

/* 7. RESTORE LIKED STATE */
document.querySelectorAll('.like-stat').forEach(stat => {
    const courseId = stat.dataset.courseId;
    fetch(`/get-like-status/${courseId}/`)
        .then(r => r.json())
        .then(data => {
            if (data.is_liked) {
                stat.querySelector('i').style.color = '#dc2626';
                stat.classList.add('liked');
            }
        })
        .catch(() => {});
});
