// Auto-refresh countdown timers every minute
setInterval(function() {
  const cards = document.querySelectorAll('.data-card');
  cards.forEach(function(card) {
    // Trigger a subtle visual update indicator
    const timerDisplay = card.querySelector('[style*="Time Remaining"]');
    if (timerDisplay) {
      timerDisplay.style.opacity = '0.8';
      setTimeout(function() {
        timerDisplay.style.opacity = '1';
      }, 200);
    }
  });
}, 60000);