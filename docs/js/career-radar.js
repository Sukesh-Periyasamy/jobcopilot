/**
 * JobCopilot — Career Radar Page
 * Fetches personalized scored jobs and renders them with tabs.
 */

(function () {
  'use strict';

  const loadingState = document.getElementById('loading-state');
  const errorState = document.getElementById('error-state');
  const jobsContainer = document.getElementById('jobs-container');
  const radarStats = document.getElementById('radar-stats');
  const statTotal = document.getElementById('stat-total');
  const statMatches = document.getElementById('stat-matches');
  const retryBtn = document.getElementById('retry-btn');
  const tabsContainer = document.getElementById('radar-tabs');

  let radarData = null;
  let activeTab = 'top_matches';

  function showState(state) {
    loadingState.style.display = state === 'loading' ? '' : 'none';
    errorState.style.display = state === 'error' ? '' : 'none';
    jobsContainer.style.display = state === 'jobs' ? '' : 'none';
    radarStats.style.display = state === 'jobs' ? '' : 'none';
  }

  function createJobCard(job) {
    const card = document.createElement('div');
    card.className = 'job-card';

    const collections = (job.collections || [])
      .map(function (c) { return '<span class="job-card__tag">' + escapeHtml(c) + '</span>'; })
      .join('');

    card.innerHTML =
      '<div class="job-card__header">' +
        '<div>' +
          '<div class="job-card__title">' + escapeHtml(job.title) + '</div>' +
          '<div class="job-card__company">' + escapeHtml(job.company) + '</div>' +
        '</div>' +
        '<div class="job-card__score">⭐ ' + job.score + '</div>' +
      '</div>' +
      '<div class="job-card__meta">' +
        '<span>📍 ' + escapeHtml(job.location || 'Unknown') + '</span>' +
        '<span>📅 ' + escapeHtml(job.date_posted || '') + '</span>' +
        '<span>🔌 ' + escapeHtml(job.source_platform || '') + '</span>' +
      '</div>' +
      (collections ? '<div class="job-card__collections">' + collections + '</div>' : '') +
      '<a href="' + escapeHtml(job.job_url) + '" target="_blank" rel="noopener noreferrer" class="job-card__link">View Job ↗</a>';

    return card;
  }

  function renderJobs(jobs) {
    jobsContainer.innerHTML = '';

    if (!jobs || jobs.length === 0) {
      jobsContainer.innerHTML =
        '<div class="empty-state">' +
          '<div class="empty-state__icon">📭</div>' +
          '<p>No matches in this category</p>' +
        '</div>';
      return;
    }

    jobs.forEach(function (job) {
      jobsContainer.appendChild(createJobCard(job));
    });
  }

  function setActiveTab(tab) {
    activeTab = tab;

    // Update tab styles
    var tabs = tabsContainer.querySelectorAll('.radar-tab');
    tabs.forEach(function (t) {
      if (t.getAttribute('data-tab') === tab) {
        t.classList.add('radar-tab--active');
      } else {
        t.classList.remove('radar-tab--active');
      }
    });

    // Render the selected category
    if (radarData) {
      renderJobs(radarData[tab] || []);
    }
  }

  async function loadCareerRadar() {
    showState('loading');

    var result = await window.JobCopilotAPI.getCareerRadar();

    if (!result.ok) {
      showState('error');
      return;
    }

    radarData = result.data;

    // Update stats
    if (radarData.stats) {
      statTotal.textContent = radarData.stats.total_scored || 0;
      statMatches.textContent = radarData.stats.matches_found || 0;
    }

    showState('jobs');
    setActiveTab(activeTab);
  }

  function escapeHtml(str) {
    if (!str) return '';
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  // Tab click handlers
  tabsContainer.addEventListener('click', function (e) {
    var tab = e.target.getAttribute('data-tab');
    if (tab) {
      setActiveTab(tab);
    }
  });

  retryBtn.addEventListener('click', loadCareerRadar);

  // Initial load
  loadCareerRadar();
})();
