/**
 * JobCopilot — Dashboard Page Logic
 * Fetches stats, recent jobs, and personal dashboard data.
 * Renders metric cards, table, and personalized opportunity sections.
 */

(function () {
  const API = window.JobCopilotAPI;
  const UI = window.JobCopilotUI;

  const metricsContainer = document.getElementById('metrics-container');
  const recentJobsContainer = document.getElementById('recent-jobs-container');
  const personalDashboard = document.getElementById('personal-dashboard');
  const pinnedCompanySection = document.getElementById('pinned-company-jobs-section');
  const pinnedCompanyContainer = document.getElementById('pinned-company-jobs-container');
  const pinnedCollectionSection = document.getElementById('pinned-collection-jobs-section');
  const pinnedCollectionContainer = document.getElementById('pinned-collection-jobs-container');
  const newResearchSection = document.getElementById('new-research-section');
  const newResearchContainer = document.getElementById('new-research-container');

  /**
   * Creates a compact job card for the personal dashboard sections.
   * Shows title, company, location, date_posted, and a link to job_url.
   * @param {Object} job - Job object from API
   * @returns {HTMLElement} Compact job card element
   */
  function createCompactJobCard(job) {
    const card = document.createElement('div');
    card.classList.add('card', 'job-card');

    const title = UI.escapeHtml(job.title || 'Untitled');
    const company = UI.escapeHtml(job.company || 'Unknown');
    const location = UI.escapeHtml(job.location || 'Remote');
    const datePosted = job.date_posted || '';
    const jobUrl = UI.escapeHtml(job.job_url || '#');

    card.innerHTML = `
      <div class="job-card__header">
        <div>
          <div class="job-card__title">${title}</div>
          <div class="job-card__company">${company}</div>
        </div>
      </div>
      <div class="job-card__meta">
        <span>${location}</span>
        ${datePosted ? `<span>${datePosted}</span>` : ''}
      </div>
      <div class="job-card__actions">
        <a href="${jobUrl}" target="_blank" rel="noopener noreferrer" class="btn btn--primary btn--sm">View ↗</a>
      </div>
    `;

    return card;
  }

  /**
   * Render a list of jobs into a container, showing the section if non-empty.
   * @param {Array} jobs - Array of job objects
   * @param {HTMLElement} container - Container to render cards into
   * @param {HTMLElement} section - Section element to show/hide
   */
  function renderDashboardSection(jobs, container, section) {
    if (!jobs || jobs.length === 0) {
      section.style.display = 'none';
      return;
    }

    container.innerHTML = '';
    jobs.forEach(function (job) {
      container.appendChild(createCompactJobCard(job));
    });
    section.style.display = '';
  }

  /**
   * Load personal dashboard data from /preferences/dashboard.
   * Gracefully hides sections if API fails or returns empty data.
   */
  async function loadPersonalDashboard() {
    const result = await API.getDashboardPreferences();

    if (!result.ok) {
      // Gracefully hide — existing v1.1 content still shows
      personalDashboard.style.display = 'none';
      return;
    }

    const data = result.data;
    const pinnedCompanyJobs = data.pinned_company_jobs || [];
    const pinnedCollectionJobs = data.pinned_collection_jobs || [];
    const newResearchOpportunities = data.new_research_opportunities || [];

    // If all sections are empty, hide the entire personal dashboard wrapper
    if (pinnedCompanyJobs.length === 0 && pinnedCollectionJobs.length === 0 && newResearchOpportunities.length === 0) {
      personalDashboard.style.display = 'none';
      return;
    }

    // Show the personal dashboard wrapper
    personalDashboard.style.display = '';

    // Render each section
    renderDashboardSection(pinnedCompanyJobs, pinnedCompanyContainer, pinnedCompanySection);
    renderDashboardSection(pinnedCollectionJobs, pinnedCollectionContainer, pinnedCollectionSection);
    renderDashboardSection(newResearchOpportunities, newResearchContainer, newResearchSection);
  }

  /**
   * Load and render dashboard metrics.
   */
  async function loadMetrics() {
    const result = await API.getStats();

    if (!result.ok) {
      metricsContainer.innerHTML = '';
      metricsContainer.appendChild(UI.createEmptyState('Unable to load metrics. Is the backend running?', '⚠️'));
      return;
    }

    const stats = result.data;
    metricsContainer.innerHTML = '';

    const metrics = [
      { title: 'Total Jobs', value: stats.total_jobs ?? 0, icon: '📋' },
      { title: "Today's Jobs", value: stats.jobs_today ?? 0, icon: '🆕' },
      { title: 'This Week', value: stats.jobs_this_week ?? 0, icon: '📅' },
      { title: 'Saved', value: stats.saved_jobs ?? 0, icon: '⭐' },
      { title: 'Applied', value: stats.applied_jobs ?? 0, icon: '✅' },
    ];

    metrics.forEach(function (m) {
      metricsContainer.appendChild(UI.createMetricCard(m.title, m.value, m.icon));
    });
  }

  /**
   * Load and render recent jobs table (top 10).
   */
  async function loadRecentJobs() {
    const result = await API.getRecentJobs();

    if (!result.ok) {
      recentJobsContainer.innerHTML = '';
      recentJobsContainer.appendChild(UI.createEmptyState('Unable to load recent jobs.', '⚠️'));
      return;
    }

    const jobs = result.data || [];

    if (jobs.length === 0) {
      recentJobsContainer.innerHTML = '';
      recentJobsContainer.appendChild(UI.createEmptyState('No jobs found yet. Run a scrape to get started.', '📭'));
      return;
    }

    const headers = ['Title', 'Company', 'Location', 'Source', 'Date Posted', 'Freshness'];
    const rows = jobs.map(function (job) {
      const badge = UI.createFreshBadge(job.date_posted);
      return [
        job.title || '—',
        job.company || '—',
        job.location || 'Remote',
        job.source || '—',
        job.date_posted || '—',
        badge,
      ];
    });

    recentJobsContainer.innerHTML = '';
    recentJobsContainer.appendChild(UI.createDataTable(headers, rows));
  }

  // Initialize dashboard
  async function init() {
    await Promise.all([loadPersonalDashboard(), loadMetrics(), loadRecentJobs()]);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
