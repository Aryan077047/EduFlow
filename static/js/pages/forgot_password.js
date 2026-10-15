/* ==== extracted from template forgot_password.html ==== */

const resendLabel = window.__PAGECFG__.resendLabel;

(function () {
  'use strict';

  /* keep the OTP box numeric-only and auto-submit once 6 digits are typed */
  const otpInput = document.getElementById('id_code');
  if (otpInput) {
    otpInput.focus();
    otpInput.addEventListener('input', function () {
      this.value = this.value.replace(/\D/g, '').slice(0, 6);
      if (this.value.length === 6) {
        const form = document.getElementById('otpForm');
        if (form) form.submit();
      }
    });
  }

  /* expiry countdown */
  const timerEl = document.getElementById('timer');
  let seconds = parseInt(timerEl ? timerEl.dataset.seconds : '0', 10) || 0;

  function two(n) { return n < 10 ? '0' + n : String(n); }

  function tick() {
    if (seconds <= 0) {
      timerEl.textContent = 'expired';
      timerEl.style.color = '#b91c1c';
      clearInterval(handle);
      return;
    }
    timerEl.textContent = two(Math.floor(seconds / 60)) + ':' + two(seconds % 60);
    seconds -= 1;
  }

  let handle = null;
  if (timerEl) {
    tick();
    handle = setInterval(tick, 1000);
  }

  /* resend cooldown */
  const resendBtn = document.getElementById('resendBtn');
  const resendTimer = document.getElementById('resendTimer');
  let wait = parseInt(resendTimer ? resendTimer.textContent : '0', 10) || 0;

  if (resendBtn && wait > 0) {
    let handle2 = setInterval(function () {
      wait -= 1;
      if (resendTimer) resendTimer.textContent = wait;
      if (wait <= 0) {
        clearInterval(handle2);
        resendBtn.disabled = false;
        resendBtn.innerHTML = '<i class="fa-solid fa-rotate"></i> ' + resendLabel + '
      }
    }, 1000);
  }
})();
