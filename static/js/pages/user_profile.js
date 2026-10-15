/* ==== extracted (bridge) from template user_profile.html ==== */

  (function () {
    'use strict';

    const $ = function (id) { return document.getElementById(id); };

    function esc(value) {
      return String(value === null || value === undefined ? '' : value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    }

    function getCsrfToken() {
      const name = 'csrftoken';
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const trimmed = cookies[i].trim();
        if (trimmed.indexOf(name + '=') === 0) {
          return decodeURIComponent(trimmed.substring(name.length + 1));
        }
      }
      return null;
    }

    let toastTimer = null;
    const toast = $('toast');
    const toastMessage = $('toastMessage');
    const toastIcon = toast ? toast.querySelector('i') : null;

    function showToast(message, type) {
      if (!toast || !toastMessage) return;
      toastMessage.textContent = message;
      if (type === 'error') {
        if (toastIcon) toastIcon.className = 'fa-solid fa-circle-exclamation';
        toast.style.background = '#dc2626';
      } else {
        if (toastIcon) toastIcon.className = 'fa-solid fa-circle-check';
        toast.style.background = '#18311f';
      }
      toast.classList.add('show');
      if (toastTimer) clearTimeout(toastTimer);
      toastTimer = setTimeout(function () { toast.classList.remove('show'); }, 4000);
    }
    window.showToast = showToast;

    const courseModal = $('courseModal');
    const teacherModal = $('teacherModal');
    const applyTeacherBtn = $('applyTeacherBtn');
    const courseForm = $('courseForm');
    const courseIdInput = $('courseIdInput');
    const courseModalTitle = $('courseModalTitle');
    const courseSubmitBtn = $('courseSubmitBtn');
    const videoFileInput = $('videoFileInput');

    /* -------- FIX 1: Null-guard the Apply Teacher button -------- */
    if (applyTeacherBtn) {
      applyTeacherBtn.addEventListener('click', function () {
        setModalState(teacherModal, true);
      });
    }

    function setModalState(modal, open) {
      if (!modal) return;
      modal.classList.toggle('active', open);
      if (open) {
        document.body.style.overflow = 'hidden';
      } else if (!($('playlistSidebar') && $('playlistSidebar').classList.contains('open'))) {
        document.body.style.overflow = '';
      }
    }

    function closeCourseModal() {
      setModalState(courseModal, false);
      if (courseForm) courseForm.reset();
      if (courseIdInput) courseIdInput.value = '';
      if (courseModalTitle) courseModalTitle.textContent = 'Add New Course';
      if (courseSubmitBtn) {
        courseSubmitBtn.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i> Create Draft';
      }
      if (courseForm) {
        courseForm.querySelectorAll('.field-error, .modal-error').forEach(function (el) { el.remove(); });
      }
    }

    function openCourseModal(course) {
      if (!courseModal) return;
      if (course) {
        if (courseIdInput) courseIdInput.value = course.id || '';
        if (courseModalTitle) courseModalTitle.textContent = 'Edit Course';
        if (courseSubmitBtn) {
          courseSubmitBtn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Save Changes';
        }
        if (courseForm) {
          const setValue = function (name, value) {
            const field = courseForm.querySelector('[name="' + name + '"]');
            if (field) field.value = value === null || value === undefined ? '' : value;
          };
          setValue('title', course.title);
          setValue('category', course.category);
          setValue('level', course.level);
          setValue('Course_price', course.price);
          setValue('description', course.description);
          const video = courseForm.querySelector('[name="vedio"]');
          if (video) video.value = '';
        }
      } else {
        if (courseIdInput) courseIdInput.value = '';
        if (courseForm) courseForm.reset();
        if (courseModalTitle) courseModalTitle.textContent = 'Add New Course';
        if (courseSubmitBtn) {
          courseSubmitBtn.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i> Create Draft';
        }
      }
      setModalState(courseModal, true);
    }

    const openCourseBtn = $('openModal');
    if (openCourseBtn) {
      openCourseBtn.addEventListener('click', function (e) {
        e.preventDefault();
        openCourseModal(null);
      });
    }
    const emptyCreateBtn = $('emptyCreateCourse');
    if (emptyCreateBtn) {
      emptyCreateBtn.addEventListener('click', function () { openCourseModal(null); });
    }
    if ($('closeModal')) {
      $('closeModal').addEventListener('click', closeCourseModal);
    }
    if ($('closeTeacherModal')) {
      $('closeTeacherModal').addEventListener('click', function () {
        setModalState(teacherModal, false);
      });
    }

    document.addEventListener('click', function (e) {
      if (e.target === courseModal) closeCourseModal();
      if (e.target === teacherModal) setModalState(teacherModal, false);
      if (e.target === $('profileModal')) setModalState($('profileModal'), false);
      if (e.target === $('playlistEditModal')) closePlaylistEdit();
    });

    document.addEventListener('keydown', function (e) {
      if (e.key !== 'Escape') return;
      const confirmOverlay = $('confirmModal');
      if (confirmOverlay && confirmOverlay.classList.contains('show')) return;
      if ($('playlistEditModal') && $('playlistEditModal').classList.contains('active')) {
        closePlaylistEdit();
        return;
      }
      if ($('profileModal') && $('profileModal').classList.contains('active')) {
        setModalState($('profileModal'), false);
        return;
      }
      const sidebar = $('playlistSidebar');
      if (sidebar && sidebar.classList.contains('open')) {
        closePlaylist();
        return;
      }
      if (courseModal && courseModal.classList.contains('active')) closeCourseModal();
      if (teacherModal && teacherModal.classList.contains('active')) setModalState(teacherModal, false);
    });

    if (courseModal && courseModal.dataset.autopen === '1') {
      openCourseModal(courseIdInput && courseIdInput.value
        ? { id: courseIdInput.value, title: '', category: '', level: '', price: '', description: '' }
        : null);
    }
    if (teacherModal && teacherModal.dataset.autopen === '1') {
      setModalState(teacherModal, true);
    }

    document.querySelectorAll('[data-edit-btn]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        openCourseModal({
          id: this.dataset.courseId,
          title: this.dataset.title,
          category: this.dataset.category,
          level: this.dataset.level,
          price: this.dataset.price,
          description: this.dataset.description
        });
      });
    });

    // data-confirm is now handled automatically by ConfirmModal.js
    // No manual handler needed

    document.querySelectorAll('[data-publish-btn]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const self = this;
        const csrfToken = getCsrfToken();
        if (!csrfToken) {
          showToast('CSRF token not found. Please refresh the page.', 'error');
          return;
        }

        const isPublished = self.dataset.isPublished === '1';
        const body = new FormData();
        body.append('action', isPublished ? 'unpublish' : 'publish');

        self.disabled = true;
        const original = self.innerHTML;
        self.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Working...';

        fetch(self.dataset.publishUrl, {
          method: 'POST',
          body: body,
          headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
          },
          credentials: 'same-origin'
        })
          .then(function (response) {
            return response.json().then(function (data) {
              if (!response.ok) {
                throw new Error(data.error || data.message || ('Server error: ' + response.status));
              }
              return data;
            });
          })
          .then(function (data) {
            const published = data.is_published === true;
            self.dataset.isPublished = published ? '1' : '0';
            self.classList.toggle('published', published);
            self.innerHTML = published
              ? '<i class="fas fa-circle-check"></i> window.__CFG__.publishedLabel'
              : '<i class="fa-solid fa-rocket"></i> window.__CFG__.publishLabel';
            self.title = published
              ? 'Visible to students \u2014 click to move back to draft'
              : 'Click to publish this course';

            const item = self.closest('.premium-item');
            const chip = item ? item.querySelector('.draft-chip') : null;
            if (!published && item && !chip) {
              const thumb = item.querySelector('.course-thumb-wrapper');
              if (thumb) {
                const badge = document.createElement('span');
                badge.className = 'draft-chip';
                badge.textContent = 'Draft';
                thumb.appendChild(badge);
              }
            } else if (published && chip) {
              chip.remove();
            }

            showToast(data.message || (published ? 'Course published.' : 'Course moved to draft.'), 'success');
          })
          .catch(function (error) {
            self.innerHTML = original;
            showToast(error.message || 'Could not update the course.', 'error');
          })
          .finally(function () { self.disabled = false; });
      });
    });

    const overlay = $('playlistOverlay');
    const sidebar = $('playlistSidebar');
    const playlistTitle = $('playlistCourseTitle');
    const playlistContent = $('playlistContent');
    const playlistTotal = $('playlistTotal');
    const showAddBtn = $('showAddVideoBtn');
    const ownerNote = $('playlistOwnerNote');
    const addForm = $('addVideoForm');
    const fileNameDisplay = $('fileNameDisplay');
    const confirmUploadBtn = $('confirmFileUpload');
    const cancelUploadBtn = $('cancelFileUpload');

    const videoContainer = $('videoPlayerContainer');
    const videoPlayer = $('videoPlayer');

    let currentCourseId = null;
    let currentPlaylistUrl = '';
    let currentUploadUrl = '';
    let selectedFile = null;
    let requestToken = 0;
    let currentVideos = {};
    const I18N = (window.__CFG__ && window.__CFG__.i18n) || {};

    function playVideo(title, src) {
      if (!src) {
        showToast('This video file is missing.', 'error');
        return;
      }
      if (!videoPlayer) return;
      $('videoPlayerTitle').textContent = title || 'Now Playing';
      const source = videoPlayer.querySelector('source');
      source.src = src;
      videoPlayer.load();
      const attempt = videoPlayer.play();
      if (attempt && typeof attempt.catch === 'function') {
        attempt.catch(function () {});
      }
      videoContainer.classList.remove('hidden');
    }

    function closeVideoPlayer() {
      if (videoPlayer) {
        videoPlayer.pause();
        const source = videoPlayer.querySelector('source');
        if (source) source.removeAttribute('src');
        videoPlayer.load();
      }
      if (videoContainer) videoContainer.classList.add('hidden');
    }
    if ($('closeVideoPlayer')) {
      $('closeVideoPlayer').addEventListener('click', closeVideoPlayer);
    }

    function renderPlaylist(data, token) {
      const videos = Array.isArray(data.videos) ? data.videos : [];
      const quizzes = Array.isArray(data.quizzes) ? data.quizzes : [];

      if (token !== requestToken) return;

      if (videos.length === 0 && quizzes.length === 0) {
        playlistContent.innerHTML =
          '<div class="playlist-empty">' +
            '<i class="fa-solid fa-film"></i>' +
            '<p>No videos or quizzes in this course yet.</p>' +
          '</div>';
        playlistTotal.textContent = 'Total: 0 videos, 0 quizzes';
        return;
      }

      let html = '';

      if (videos.length > 0) {
        html += '<div class="playlist-section-title">&#127916; Videos (' + videos.length + ')</div>';
        currentVideos = {};
        videos.forEach(function (video, index) {
          const url = video.video_url || '';
          const title = video.title || ('Video ' + (index + 1));
          currentVideos[video.id] = video;
          let manage = '';
          if (video.edit_url || video.delete_url) {
            manage = '<div class="playlist-manage">' +
              (video.edit_url
                ? '<button class="manage-btn edit" type="button" data-edit-video="' + esc(video.id) + '" title="' + esc(I18N.editVideo) + '" aria-label="' + esc(I18N.editVideo) + '"><i class="fa-regular fa-pen-to-square"></i></button>'
                : '') +
              (video.delete_url
                ? '<button class="manage-btn delete" type="button" data-delete-video="' + esc(video.id) + '" title="' + esc(I18N.deleteVideo) + '" aria-label="' + esc(I18N.deleteVideo) + '"><i class="fa-regular fa-trash-can"></i></button>'
                : '') +
              '</div>';
          }
          html +=
            '<div class="playlist-item" data-video-id="' + esc(video.id) + '">' +
              '<div class="thumb"><i class="fa-solid fa-play"></i></div>' +
              '<div class="info">' +
                '<h4>' + (index + 1) + '. ' + esc(title) + '</h4>' +
                (video.description ? '<p class="video-desc">' + esc(video.description) + '</p>' : '') +
              '</div>' +
              manage +
              '<button class="play-btn" type="button" data-play-video data-src="' + esc(url) + '" data-title="' + esc(title) + '" title="Play video">' +
                '<i class="fa-solid fa-play"></i>' +
              '</button>' +
            '</div>';
        });
      }

      if (quizzes.length > 0) {
        html += '<div class="playlist-section-title">&#9997; Quizzes (' + quizzes.length + ')</div>';
        quizzes.forEach(function (quiz, index) {
          const title = quiz.title || ('Quiz ' + (index + 1));
          const isDraft = quiz.is_published === false;

          const url = quiz.quiz_url || '';
          let action;
          if (!url || quiz.quiz_mode === 'locked') {
            action =
              '<button class="play-btn quiz-play" type="button" disabled ' +
                'title="Not published yet" style="opacity:.45;cursor:not-allowed;">' +
                '<i class="fa-solid fa-lock"></i>' +
              '</button>';
          } else {
            const isSubmissions = quiz.quiz_mode === 'submissions';
            const label = isSubmissions ? 'View submissions' : 'Take quiz';
            const icon = isSubmissions ? 'fa-users' : 'fa-play';
            action =
              '<a class="play-btn quiz-play" href="' + esc(url) + '" title="' + label + '">' +
                '<i class="fa-solid ' + icon + '"></i>' +
              '</a>';
          }

          const draftBadge = isDraft
            ? '<span class="enrolled-badge" style="background:rgba(234,179,8,.15);color:#ca8a04;">DRAFT</span>'
            : '';

          const meta = [];
          if (quiz.difficulty) meta.push(esc(quiz.difficulty));
          if (quiz.total_questions) meta.push(quiz.total_questions + ' questions');
          if (quiz.duration) meta.push(quiz.duration + ' min');
          if (quiz.total_points) meta.push(quiz.total_points + ' pts');

          html +=
            '<div class="playlist-item quiz-item">' +
              '<div class="thumb"><i class="fa-solid fa-circle-question"></i></div>' +
              '<div class="info">' +
                '<h4>' + (index + 1) + '. ' + esc(title) + ' ' + draftBadge + '</h4>' +
                (meta.length ? '<div class="quiz-meta">' + meta.join(' &middot; ') + '</div>' : '') +
              '</div>' +
              action +
            '</div>';
        });
      }

      playlistContent.innerHTML = html;
      playlistTotal.textContent = 'Total: ' + videos.length + ' videos, ' + quizzes.length + ' quizzes';

      playlistContent.querySelectorAll('[data-play-video]').forEach(function (btn) {
        btn.addEventListener('click', function () {
          playVideo(this.dataset.title, this.dataset.src);
        });
      });
      playlistContent.querySelectorAll('[data-edit-video]').forEach(function (btn) {
        btn.addEventListener('click', function () {
          openPlaylistEdit(currentVideos[this.dataset.editVideo], videos.length);
        });
      });
      playlistContent.querySelectorAll('[data-delete-video]').forEach(function (btn) {
        btn.addEventListener('click', function () {
          deletePlaylistVideo(currentVideos[this.dataset.deleteVideo], this);
        });
      });
    }

    function fetchPlaylist(url) {
      if (!url) {
        showToast('Playlist URL is missing.', 'error');
        return;
      }
      requestToken += 1;
      const token = requestToken;

      playlistContent.innerHTML =
        '<div class="playlist-empty">' +
          '<i class="fa-solid fa-spinner fa-spin"></i>' +
          '<p>Loading playlist...</p>' +
        '</div>';
      playlistTotal.textContent = 'Loading...';

      fetch(url, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        credentials: 'same-origin'
      })
        .then(function (response) {
          return response.json().then(function (data) {
            if (!response.ok) {
              throw new Error(data.error || ('Server error: ' + response.status));
            }
            return data;
          });
        })
        .then(function (data) {
          if (token !== requestToken) return;
          const canUpload = (typeof data.can_upload === 'boolean') ? data.can_upload : !!currentUploadUrl;
          applyUploadAvailability(canUpload, data.owner_name);
          if (playlistTitle && data.course_title) {
            playlistTitle.textContent = data.course_title + ' \u2014 Playlist';
          }
          renderPlaylist(data, token);
        })
        .catch(function (error) {
          if (token !== requestToken) return;
          playlistTotal.textContent = 'Total: 0 videos, 0 quizzes';
          playlistContent.innerHTML =
            '<div class="playlist-empty">' +
              '<i class="fa-solid fa-circle-exclamation"></i>' +
              '<p>' + esc(error.message) + '</p>' +
              '<button type="button" class="add-video-btn" id="retryPlaylist" style="margin-top:0.8rem;">' +
                '<i class="fa-solid fa-rotate"></i> Retry' +
              '</button>' +
            '</div>';
          const retry = $('retryPlaylist');
          if (retry) {
            retry.addEventListener('click', function () { fetchPlaylist(currentPlaylistUrl); });
          }
          showToast(error.message, 'error');
        });
    }

    function closePlaylist() {
      requestToken += 1;
      closeVideoPlayer();
      if (overlay) overlay.classList.remove('active');
      if (sidebar) sidebar.classList.remove('open');
      if (!courseModal || !courseModal.classList.contains('active')) {
        document.body.style.overflow = '';
      }
      resetUploadForm();
      currentCourseId = null;
      currentPlaylistUrl = '';
      currentUploadUrl = '';
    }

    if ($('closePlaylist')) {
      $('closePlaylist').addEventListener('click', closePlaylist);
    }
    if (overlay) overlay.addEventListener('click', closePlaylist);

    document.querySelectorAll('[data-playlist-btn]').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        currentCourseId = this.dataset.courseId || null;
        currentPlaylistUrl = this.dataset.playlistUrl || '';
        currentUploadUrl = this.dataset.addVideoUrl || '';
        if (playlistTitle) {
          playlistTitle.textContent = (this.dataset.courseTitle || 'Course') + ' — Playlist';
        }
        closeVideoPlayer();
        resetUploadForm();
        applyUploadAvailability(!!currentUploadUrl);
        if (overlay) overlay.classList.add('active');
        if (sidebar) sidebar.classList.add('open');
        document.body.style.overflow = 'hidden';
        fetchPlaylist(currentPlaylistUrl);
      });
    });

    const MAX_UPLOAD_BYTES = window.__CFG__.maxUploadBytes;

    const VIDEO_EXTENSIONS = [
      'mp4', 'webm', 'ogv', 'ogg', 'mov', 'mkv', 'avi', 'wmv', 'flv', 'm4v', 'mpg', 'mpeg', '3gp'
    ];

    function videoExtension(name) {
      const parts = String(name || '').split('.');
      return parts.length > 1 ? parts.pop().toLowerCase() : '';
    }

    function looksLikeVideo(file) {
      if (VIDEO_EXTENSIONS.indexOf(videoExtension(file.name)) !== -1) return true;
      return /^video\//.test(file.type || '');
    }

    function humanSize(bytes) {
      if (!bytes) return '0 B';
      const mb = bytes / (1024 * 1024);
      if (mb >= 1024) return (mb / 1024).toFixed(2) + ' GB';
      if (mb >= 1) return mb.toFixed(1) + ' MB';
      return Math.max(1, Math.round(bytes / 1024)) + ' KB';
    }

    function setUploadReady(ready) {
      if (confirmUploadBtn) confirmUploadBtn.disabled = !ready;
    }

    function applyUploadAvailability(canUpload, ownerName) {
      if (showAddBtn) {
        if (canUpload) {
          showAddBtn.style.display = 'inline-flex';
          showAddBtn.classList.remove('is-disabled');
          showAddBtn.style.pointerEvents = '';
          showAddBtn.style.opacity = '';
        } else {
          showAddBtn.style.display = 'none';
        }
      }
      if (ownerNote) {
        ownerNote.style.display = canUpload ? 'none' : 'block';
        if (!canUpload && ownerName) {
          ownerNote.innerHTML = '<i class="fa-solid fa-lock"></i> Only ' +
            esc(ownerName) + ' can add videos to this course.';
        }
      }
    }

    function resetUploadForm() {
      if (addForm) addForm.style.display = 'none';
      if (videoFileInput) videoFileInput.value = '';
      if (fileNameDisplay) fileNameDisplay.textContent = 'No file selected';
      selectedFile = null;
      setUploadReady(false);
    }

    if (confirmUploadBtn) setUploadReady(false);

    if (videoFileInput) {
      videoFileInput.addEventListener('change', function () {
        const file = this.files && this.files[0];
        if (!file) {
          selectedFile = null;
          setUploadReady(false);
          if (fileNameDisplay) fileNameDisplay.textContent = 'No file selected';
          return;
        }
        if (!looksLikeVideo(file)) {
          showToast('That is not a video file. Allowed: ' + VIDEO_EXTENSIONS.join(', '), 'error');
          resetUploadForm();
          return;
        }
        if (file.size === 0) {
          showToast('That file is empty (0 bytes).', 'error');
          resetUploadForm();
          return;
        }
        if (file.size > MAX_UPLOAD_BYTES) {
          showToast('That file is ' + humanSize(file.size) + '. The limit is ' +
                    humanSize(MAX_UPLOAD_BYTES) + '.', 'error');
          resetUploadForm();
          return;
        }
        selectedFile = file;
        setUploadReady(true);
        if (fileNameDisplay) fileNameDisplay.textContent = file.name + '  (' + humanSize(file.size) + ')';
      });
    }

    if (showAddBtn) {
      showAddBtn.addEventListener('click', function () {
        if (!addForm) return;

        if (!currentUploadUrl) {
          showToast('You can only add videos to your own courses.', 'error');
          return;
        }

        const isHidden = addForm.style.display === 'none' || addForm.style.display === '';
        addForm.style.display = isHidden ? 'block' : 'none';
        if (isHidden) {
          if (videoFileInput) videoFileInput.value = '';
          if (fileNameDisplay) fileNameDisplay.textContent = 'No file selected';
          selectedFile = null;
          setUploadReady(false);
          if (videoFileInput) videoFileInput.focus();
        }
      });
    }

    if (cancelUploadBtn) cancelUploadBtn.addEventListener('click', resetUploadForm);

    if (confirmUploadBtn) {
      confirmUploadBtn.addEventListener('click', function () {
        if (!selectedFile) {
          showToast('Please select a video file first.', 'error');
          return;
        }
        if (!currentUploadUrl) {
          showToast('You can only upload videos to your own courses.', 'error');
          return;
        }

        const csrfToken = getCsrfToken();
        if (!csrfToken) {
          showToast('CSRF token not found. Please refresh the page.', 'error');
          return;
        }

        const formData = new FormData();
        formData.append('video', selectedFile);

        const button = this;
        const original = button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Uploading...';

        fetch(currentUploadUrl, {
          method: 'POST',
          body: formData,
          headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
          },
          credentials: 'same-origin'
        })
          .then(function (response) {
            return response.json().then(function (data) {
              if (!response.ok) {
                throw new Error(data.error || data.message || ('Server error: ' + response.status));
              }
              return data;
            });
          })
          .then(function (data) {
            if (data.success) {
              showToast(data.message || 'Video added successfully.', 'success');
              resetUploadForm();
              fetchPlaylist(currentPlaylistUrl);
            } else {
              showToast(data.error || 'Upload failed.', 'error');
            }
          })
          .catch(function (error) {
            showToast(error.message || 'Upload failed. Please try again.', 'error');
          })
          .finally(function () {
            button.disabled = false;
            button.innerHTML = original;
          });
      });
    }

    function postForm(url, body) {
      return fetch(url, {
        method: 'POST',
        body: body,
        headers: {
          'X-CSRFToken': getCsrfToken() || '',
          'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
      }).then(function (response) {
        return response.json().catch(function () { return {}; }).then(function (data) {
          if (!response.ok) {
            const error = new Error(data.error || data.message || ('Server error: ' + response.status));
            error.fields = data.errors || {};
            throw error;
          }
          return data;
        });
      });
    }

    function setBusy(button, busy, label) {
      if (!button) return;
      if (busy) {
        button.dataset.original = button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> ' + esc(label || '');
      } else {
        button.disabled = false;
        if (button.dataset.original) button.innerHTML = button.dataset.original;
      }
    }

    /* -------- Edit profile -------- */
    const profileModal = $('profileModal');
    const profileForm = $('profileForm');
    const profileInput = $('id_profile_picture');
    const profilePreview = $('profilePreview');
    if ($('openProfileModal') && profileModal) {
      $('openProfileModal').addEventListener('click', function () {
        setModalState(profileModal, true);
        const first = $('id_profile_first_name');
        if (first) setTimeout(function () { first.focus(); }, 60);
      });
    }
    if ($('closeProfileModal')) {
      $('closeProfileModal').addEventListener('click', function () { setModalState(profileModal, false); });
    }
    if (profileModal && profileModal.dataset.autopen === '1') setModalState(profileModal, true);
    if (profileInput) {
      const IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp'];
      profileInput.addEventListener('change', function () {
        const file = this.files && this.files[0];
        if (!file) return;
        const maxBytes = window.__CFG__.profileImageMaxBytes;
        if (IMAGE_EXTENSIONS.indexOf(videoExtension(file.name)) === -1 || file.size > maxBytes) {
          showToast(I18N.profilePictureHint || 'Invalid image.', 'error');
          this.value = '';
          return;
        }
        if (profilePreview && window.URL) profilePreview.src = URL.createObjectURL(file);
      });
    }
    if (profileForm) {
      profileForm.addEventListener('submit', function () {
        setBusy($('profileSubmitBtn'), true, I18N.saving);
      });
    }

    /* -------- Edit / delete playlist videos -------- */
    const playlistEditModal = $('playlistEditModal');
    const playlistEditForm = $('playlistEditForm');
    const playlistEditError = $('playlistEditError');

    function clearPlaylistErrors() {
      if (playlistEditError) { playlistEditError.hidden = true; playlistEditError.textContent = ''; }
      if (playlistEditForm) {
        playlistEditForm.querySelectorAll('[data-error-for]').forEach(function (el) { el.textContent = ''; });
      }
    }

    function closePlaylistEdit() {
      if (!playlistEditModal) return;
      playlistEditModal.classList.remove('active');
      if (!(sidebar && sidebar.classList.contains('open'))) document.body.style.overflow = '';
    }

    function openPlaylistEdit(video, total) {
      if (!video || !video.edit_url || !playlistEditForm) return;
      clearPlaylistErrors();
      playlistEditForm.reset();
      playlistEditForm.dataset.url = video.edit_url;
      $('pe_title').value = video.custom_title || '';
      $('pe_title').placeholder = video.file_name || '';
      $('pe_description').value = video.description || '';
      $('pe_position').value = video.position || 1;
      $('pe_position').max = total || 1;
      playlistEditModal.classList.add('active');
      setTimeout(function () { $('pe_title').focus(); }, 60);
    }

    if ($('closePlaylistEdit')) $('closePlaylistEdit').addEventListener('click', closePlaylistEdit);

    if (playlistEditForm) {
      playlistEditForm.addEventListener('submit', function (e) {
        e.preventDefault();
        clearPlaylistErrors();
        const url = playlistEditForm.dataset.url;
        if (!url) return;
        const file = $('pe_video').files && $('pe_video').files[0];
        if (file && (!looksLikeVideo(file) || file.size === 0 || file.size > MAX_UPLOAD_BYTES)) {
          playlistEditForm.querySelector('[data-error-for="video"]').textContent =
            'Choose a non-empty video file up to ' + humanSize(MAX_UPLOAD_BYTES) + '.';
          return;
        }
        const button = $('playlistEditSubmit');
        setBusy(button, true, I18N.saving);
        postForm(url, new FormData(playlistEditForm))
          .then(function (data) {
            closePlaylistEdit();
            showToast(data.message || 'Video updated.', 'success');
            fetchPlaylist(currentPlaylistUrl);
          })
          .catch(function (error) {
            const fields = error.fields || {};
            Object.keys(fields).forEach(function (name) {
              const slot = playlistEditForm.querySelector('[data-error-for="' + name + '"]');
              if (slot) {
                slot.textContent = fields[name].join(' ');
              } else if (playlistEditError) {
                playlistEditError.hidden = false;
                playlistEditError.textContent = fields[name].join(' ');
              }
            });
            if (!Object.keys(fields).length && playlistEditError) {
              playlistEditError.hidden = false;
              playlistEditError.textContent = error.message;
            }
            showToast(error.message, 'error');
          })
          .finally(function () { setBusy(button, false); });
      });
    }

    function deletePlaylistVideo(video, button) {
      if (!video || !video.delete_url || !window.ConfirmModal) return;
      window.ConfirmModal.show({
        title: I18N.deleteVideo || 'Delete video',
        message: '"' + video.title + '" — ' + (I18N.deleteVideoConfirm || 'This cannot be undone.'),
        confirmText: I18N.del || 'Delete',
        cancelText: I18N.cancel || 'Cancel'
      }).then(function (confirmed) {
        if (!confirmed) return;
        setBusy(button, true, '');
        postForm(video.delete_url, new FormData())
          .then(function (data) {
            showToast(data.message || 'Video deleted.', 'success');
            const src = videoPlayer && videoPlayer.querySelector('source');
            if (src && video.video_url && src.getAttribute('src') === video.video_url) closeVideoPlayer();
            fetchPlaylist(currentPlaylistUrl);
          })
          .catch(function (error) {
            setBusy(button, false);
            showToast(error.message, 'error');
          });
      });
    }

/* Django messages -> toast (config injected from template) */
(window.__djangoMessages || []).forEach(function (message) {
  showToast(message.text, message.level);
});
})();
