/**
 * JobCopilot — Dashboard Page Logic
 * Fetches stats and recent jobs, renders metric cards and table.
 */

(function () {
  const API = window.JobCopilotAPI;
  const UI = window.JobCopilotUI;

  const metricsContainer = document.getElementById('metrics-container');
  const recentJobsContainer = document.getElementById('recent-jobs-container');

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
    await Promise.all([loadMetrics(), loadRecentJobs()]);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
