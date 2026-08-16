// Notification permission management
(function() {
  const toggle = document.getElementById('notificationsEnabled');
  const permissionStatus = document.getElementById('permissionStatus');
  const permissionDenied = document.getElementById('permissionDenied');
  const statusTitle = document.getElementById('statusTitle');
  const statusMessage = document.getElementById('statusMessage');
  const systemSettingsLink = document.getElementById('systemSettingsLink');
  
  // Check current permission status
  function updateUI() {
    if (!('Notification' in window)) {
      return;
    }
    
    const permission = Notification.permission;
    
    if (permission === 'granted') {
      toggle.checked = true;
      permissionStatus.style.display = 'block';
      permissionDenied.style.display = 'none';
      statusTitle.textContent = 'Notifications Enabled';
      statusMessage.textContent = "You'll receive reminders when your cooling-off periods end.";
    } else if (permission === 'denied') {
      toggle.checked = false;
      permissionStatus.style.display = 'none';
      permissionDenied.style.display = 'block';
    } else {
      toggle.checked = false;
      permissionStatus.style.display = 'none';
      permissionDenied.style.display = 'none';
    }
  }
  
  // Handle toggle change
  toggle.addEventListener('change', async function() {
    if (!('Notification' in window)) {
      alert('This browser does not support notifications');
      toggle.checked = false;
      return;
    }
    
    if (this.checked) {
      const permission = await Notification.requestPermission();
      if (permission === 'granted') {
        permissionStatus.style.display = 'block';
        permissionDenied.style.display = 'none';
        statusTitle.textContent = 'Notifications Enabled';
        statusMessage.textContent = "You'll receive reminders when your cooling-off periods end.";
      } else if (permission === 'denied') {
        this.checked = false;
        permissionStatus.style.display = 'none';
        permissionDenied.style.display = 'block';
      } else {
        this.checked = false;
      }
    } else {
      permissionStatus.style.display = 'block';
      statusTitle.textContent = 'Notifications Disabled';
      statusMessage.textContent = "You won't receive reminders, but you can still check your saved items anytime.";
    }
  });
  
  // System settings link
  systemSettingsLink.addEventListener('click', function(e) {
    e.preventDefault();
    alert('Please open your browser settings and allow notifications for this site.');
  });
  
  // Toggle switch styling
  const toggleInput = toggle;
  const toggleContainer = toggleInput.parentElement;
  const slider = toggleContainer.querySelector('span:first-of-type');
  const knob = toggleContainer.querySelector('span:last-of-type');
  
  toggleInput.addEventListener('change', function() {
    if (this.checked) {
      slider.style.backgroundColor = '#6366F1';
      knob.style.transform = 'translateX(20px)';
    } else {
      slider.style.backgroundColor = '#E5E7EB';
      knob.style.transform = 'translateX(0)';
    }
  });
  
  // Initialize
  updateUI();
})();