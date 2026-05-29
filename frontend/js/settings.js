/**
 * JobCopilot — Settings Page Logic
 * Displays current configuration as read-only info.
 */

(function () {
  const UI = window.JobCopilotUI;

  const settingsContainer = document.getElementById('settings-container');

  // Default configuration values (from requirements 9.4)
  const defaultConfig = {
    searchTerms: [
      'Biomedical Engineer',
      'Medical Device Engineer',
      'Research Engineer',
      'Research Associate',
      'Healthcare Technology',
      'Healthcare AI',
      'Signal Processing Engineer',
      'Embedded Systems Engineer',
      'IoT Engineer',
      'Python Developer',
      'Backend Developer',
      'R&D Engineer',
      'Clinical Data Analyst',
      'Biomedical Research',
      'Medical Technology',
      'Research Scientist',
    ],
    locations: [
      'India',
      'Remote',
      'Bangalore',
      'Hyderabad',
      'Chennai',
      'Pune',
      'Mumbai',
      'Delhi',
      'Noida',
      'Gurugram',
      'Ahmedabad',
      'Kolkata',
    ],
    sources: ['LinkedIn', 'Indeed', 'Naukri', 'Google Jobs'],
    scheduleTime: '08:00 AM IST',
  };

  /**
   * Render settings cards.
   */
  function renderSettings() {
    settingsContainer.innerHTML = '';

    // Search Terms Card
    var searchCard = document.createElement('div');
    searchCard.className = 'card mb-lg';
    searchCard.innerHTML = '<h3 style="font-size: var(--font-size-base); font-weight: 600; margin-bottom: var(--space-md); color: var(--text-primary);">🔍 Search Terms</h3>';
    var searchBadges = document.createElement('div');
    searchBadges.style.display = 'flex';
    searchBadges.style.flexWrap = 'wrap';
    searchBadges.style.gap = 'var(--space-sm)';
    defaultConfig.searchTerms.forEach(function (term) {
      var badge = document.createElement('span');
      badge.className = 'badge badge--blue';
      badge.textContent = term;
      searchBadges.appendChild(badge);
    });
    searchCard.appendChild(searchBadges);
    settingsContainer.appendChild(searchCard);

    // Locations Card
    var locCard = document.createElement('div');
    locCard.className = 'card mb-lg';
    locCard.innerHTML = '<h3 style="font-size: var(--font-size-base); font-weight: 600; margin-bottom: var(--space-md); color: var(--text-primary);">📍 Locations</h3>';
    var locBadges = document.createElement('div');
    locBadges.style.display = 'flex';
    locBadges.style.flexWrap = 'wrap';
    locBadges.style.gap = 'var(--space-sm)';
    defaultConfig.locations.forEach(function (loc) {
      var badge = document.createElement('span');
      badge.className = 'badge badge--green';
      badge.textContent = loc;
      locBadges.appendChild(badge);
    });
    locCard.appendChild(locBadges);
    settingsContainer.appendChild(locCard);

    // Sources Card
    var srcCard = document.createElement('div');
    srcCard.className = 'card mb-lg';
    srcCard.innerHTML = '<h3 style="font-size: var(--font-size-base); font-weight: 600; margin-bottom: var(--space-md); color: var(--text-primary);">🌐 Job Sources</h3>';
    var srcBadges = document.createElement('div');
    srcBadges.style.display = 'flex';
    srcBadges.style.flexWrap = 'wrap';
    srcBadges.style.gap = 'var(--space-sm)';
    defaultConfig.sources.forEach(function (src) {
      var badge = document.createElement('span');
      badge.className = 'badge badge--yellow';
      badge.textContent = src;
      srcBadges.appendChild(badge);
    });
    srcCard.appendChild(srcBadges);
    settingsContainer.appendChild(srcCard);

    // Schedule Card
    var schedCard = document.createElement('div');
    schedCard.className = 'card mb-lg';
    schedCard.innerHTML = '<h3 style="font-size: var(--font-size-base); font-weight: 600; margin-bottom: var(--space-md); color: var(--text-primary);">⏰ Schedule</h3>' +
      '<p style="color: var(--text-secondary); font-size: var(--font-size-sm);">Daily scrape runs at <strong style="color: var(--text-primary);">' + UI.escapeHtml(defaultConfig.scheduleTime) + '</strong></p>';
    settingsContainer.appendChild(schedCard);

    // Info note
    var noteCard = document.createElement('div');
    noteCard.className = 'card';
    noteCard.style.borderColor = 'rgba(59, 130, 246, 0.2)';
    noteCard.innerHTML = '<p style="color: var(--text-secondary); font-size: var(--font-size-sm);">ℹ️ Settings are configured via environment variables on the backend. To change these values, update the <code style="color: var(--accent-blue); font-family: var(--font-mono);">.env</code> file or Render environment variables and redeploy.</p>';
    settingsContainer.appendChild(noteCard);
  }

  // Initialize
  function init() {
    renderSettings();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
