/* ==== extracted from template priview.html ==== */

    // ========== COMPLETE VIDEO PLAYER WITH FULL CONTROLS ==========
    
    const video = document.getElementById('courseVideo');
    const playPauseBtn = document.getElementById('playPauseBtn');
    const rewindBtn = document.getElementById('rewindBtn');
    const forwardBtn = document.getElementById('forwardBtn');
    const timeDisplay = document.getElementById('timeDisplay');
    const progressFill = document.getElementById('progressFill');
    const progressBuffered = document.getElementById('progressBuffered');
    const progressContainer = document.getElementById('progressBar');
    const volumeSlider = document.getElementById('volumeSlider');
    const volumeIcon = document.getElementById('volumeIcon');
    const fullscreenBtn = document.getElementById('fullscreenBtn');
    const videoWrapper = document.getElementById('videoWrapper');
    const durationSpan = document.getElementById('videoDuration');
    
    /* Course info (title/category/description/instructor) is rendered
       server-side by Django from the Course object — this file only runs
       the video player controls. */
    
    function formatTime(seconds) {
        if (isNaN(seconds) || !isFinite(seconds) || seconds < 0) return "0:00";
        const hrs = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        if (hrs > 0) return `${hrs}:${mins.toString().padStart(2,'0')}:${secs.toString().padStart(2,'0')}`;
        return `${mins}:${secs.toString().padStart(2,'0')}`;
    }
    
    function updateProgressAndTime() {
        if (video.duration && isFinite(video.duration)) {
            const current = formatTime(video.currentTime);
            const total = formatTime(video.duration);
            timeDisplay.innerText = `${current} / ${total}`;
            const percent = (video.currentTime / video.duration) * 100;
            progressFill.style.width = `${percent}%`;
            if (durationSpan.innerText === '--:--') {
                durationSpan.innerText = formatTime(video.duration);
            }
        } else {
            timeDisplay.innerText = `0:00 / 0:00`;
        }
        
        if (video.buffered.length > 0 && video.duration) {
            const bufferedEnd = video.buffered.end(video.buffered.length - 1);
            const bufferedPercent = (bufferedEnd / video.duration) * 100;
            progressBuffered.style.width = `${bufferedPercent}%`;
        }
    }
    
    function togglePlayPause() {
        if (video.paused || video.ended) {
            video.play().catch(e => console.log("Play error:", e));
        } else {
            video.pause();
        }
    }
    
    function rewindVideo() {
        video.currentTime = Math.max(0, video.currentTime - 10);
        showToast('⏪ Rewind 10 seconds');
    }
    
    function forwardVideo() {
        if (video.duration) {
            video.currentTime = Math.min(video.duration, video.currentTime + 10);
            showToast('⏩ Forward 10 seconds');
        }
    }
    
    function updateVolumeIcon() {
        if (video.volume === 0) {
            volumeIcon.className = 'fas fa-volume-mute';
        } else if (video.volume < 0.5) {
            volumeIcon.className = 'fas fa-volume-down';
        } else {
            volumeIcon.className = 'fas fa-volume-up';
        }
    }
    
    let idleTimer;
    function resetIdleTimer() {
        videoWrapper.classList.remove('controls-idle');
        videoWrapper.classList.add('controls-active');
        clearTimeout(idleTimer);
        idleTimer = setTimeout(() => {
            if (!video.paused) {
                videoWrapper.classList.add('controls-idle');
            }
            videoWrapper.classList.remove('controls-active');
        }, 2500);
    }
    
    function initIdleControls() {
        videoWrapper.addEventListener('mousemove', resetIdleTimer);
        videoWrapper.addEventListener('click', resetIdleTimer);
        videoWrapper.addEventListener('touchstart', resetIdleTimer);
        resetIdleTimer();
        video.addEventListener('play', resetIdleTimer);
        video.addEventListener('pause', () => {
            videoWrapper.classList.remove('controls-idle');
            videoWrapper.classList.add('controls-active');
            clearTimeout(idleTimer);
        });
    }
    
    const toast = document.getElementById('toastMsg');
    function showToast(message) {
        toast.innerText = message || '✨ Done!';
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 2000);
    }
    
    video.addEventListener('play', () => {
        playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
    });
    video.addEventListener('pause', () => {
        playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
    });
    video.addEventListener('timeupdate', updateProgressAndTime);
    video.addEventListener('loadedmetadata', () => {
        updateProgressAndTime();
        if (video.duration && isFinite(video.duration)) {
            durationSpan.innerText = formatTime(video.duration);
        }
    });
    video.addEventListener('progress', updateProgressAndTime);
    
    video.addEventListener('click', (e) => {
        e.stopPropagation();
        togglePlayPause();
        resetIdleTimer();
    });
    
    playPauseBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        togglePlayPause();
        resetIdleTimer();
    });
    
    rewindBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        rewindVideo();
        resetIdleTimer();
    });
    
    forwardBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        forwardVideo();
        resetIdleTimer();
    });
    
    let isSeeking = false;
    progressContainer.addEventListener('mousedown', (e) => {
        isSeeking = true;
        const rect = progressContainer.getBoundingClientRect();
        let pos = (e.clientX - rect.left) / rect.width;
        pos = Math.min(1, Math.max(0, pos));
        if (video.duration && isFinite(video.duration)) {
            video.currentTime = pos * video.duration;
        }
        resetIdleTimer();
    });
    
    window.addEventListener('mousemove', (e) => {
        if (isSeeking) {
            const rect = progressContainer.getBoundingClientRect();
            let pos = (e.clientX - rect.left) / rect.width;
            pos = Math.min(1, Math.max(0, pos));
            if (video.duration && isFinite(video.duration)) {
                video.currentTime = pos * video.duration;
                updateProgressAndTime();
            }
            resetIdleTimer();
        }
    });
    
    window.addEventListener('mouseup', () => {
        isSeeking = false;
    });
    
    volumeSlider.addEventListener('input', (e) => {
        video.volume = parseFloat(e.target.value);
        updateVolumeIcon();
    });
    
    volumeIcon.addEventListener('click', () => {
        if (video.volume > 0) {
            video.volume = 0;
            volumeSlider.value = 0;
        } else {
            video.volume = 0.8;
            volumeSlider.value = 0.8;
        }
        updateVolumeIcon();
        showToast(`Volume: ${Math.round(video.volume * 100)}%`);
    });
    
    function toggleFullscreen() {
        if (!document.fullscreenElement) {
            videoWrapper.requestFullscreen().catch(err => console.warn(err));
        } else {
            document.exitFullscreen();
        }
    }
    
    fullscreenBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleFullscreen();
        resetIdleTimer();
    });
    
    document.addEventListener('fullscreenchange', () => {
        if (document.fullscreenElement) {
            fullscreenBtn.innerHTML = '<i class="fas fa-compress"></i>';
        } else {
            fullscreenBtn.innerHTML = '<i class="fas fa-expand"></i>';
        }
    });
    
    window.addEventListener('keydown', (e) => {
        const tag = e.target.tagName;
        if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'BUTTON') return;
        
        switch(e.code) {
            case 'Space':
                e.preventDefault();
                togglePlayPause();
                resetIdleTimer();
                break;
            case 'ArrowLeft':
                e.preventDefault();
                rewindVideo();
                resetIdleTimer();
                break;
            case 'ArrowRight':
                e.preventDefault();
                forwardVideo();
                resetIdleTimer();
                break;
            case 'ArrowUp':
                e.preventDefault();
                video.volume = Math.min(1, video.volume + 0.1);
                volumeSlider.value = video.volume;
                updateVolumeIcon();
                showToast(`Volume: ${Math.round(video.volume * 100)}%`);
                break;
            case 'ArrowDown':
                e.preventDefault();
                video.volume = Math.max(0, video.volume - 0.1);
                volumeSlider.value = video.volume;
                updateVolumeIcon();
                showToast(`Volume: ${Math.round(video.volume * 100)}%`);
                break;
            case 'KeyF':
                e.preventDefault();
                toggleFullscreen();
                break;
            case 'KeyM':
                e.preventDefault();
                if (video.volume > 0) {
                    video.volume = 0;
                    volumeSlider.value = 0;
                } else {
                    video.volume = 0.8;
                    volumeSlider.value = 0.8;
                }
                updateVolumeIcon();
                showToast(video.volume === 0 ? '🔇 Muted' : '🔊 Unmuted');
                break;
        }
    });
    
    const backBtn = document.getElementById('backToDashboardBtn');
    backBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (document.referrer && document.referrer.includes(window.location.host)) {
            window.history.back();
        } else {
            window.location.href = '/';
        }
    });
    
    const shareBtn = document.getElementById('shareCourseBtn');
    shareBtn.addEventListener('click', () => {
        const shareUrl = window.location.href;
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(shareUrl).then(() => {
                showToast('🔗 Course link copied!');
            }).catch(() => {
                showToast('📋 Press Ctrl+C to copy');
            });
        } else {
            showToast('📋 Press Ctrl+C to copy link');
        }
    });
    
    video.volume = 1;
    volumeSlider.value = 1;
    updateVolumeIcon();
    initIdleControls();
    
    video.addEventListener('error', () => {
        showToast('⚠️ Video loading failed');
    });
    
    // If the course has no video at all, disable the player controls
    if (!video.querySelector('source')) {
        video.remove();
        const bar = document.getElementById('customControls');
        if (bar) bar.remove();
    }
    
    console.log('Video player ready');
