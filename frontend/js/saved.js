/**
 * JobCopilot — Saved Jobs Page Logic
 * Fetches saved jobs and renders table with Remove action.
 */

(function () {
  const API = window.JobCopilotAPI;
  const UI = window.JobCopilotUI;

  const savedJobsContainer = document.getElementById('saved-jobs-container');

  /**
   * Load and render saved jobs.
   */
  async function loadSavedJobs() {
    const result = await API.getSavedJobs();

    if (!result.ok) {
      savedJobsContainer.innerHTML = '';
      savedJobsContainer.appendChild(UI.createEmptyState('Unable to load saved jobs.', '⚠️'));
      return;
    }

    const jobs = result.data || [];

    if (jobs.length === 0) {
      savedJobsContainer.innerHTML = '';
      savedJobsContainer.appendChild(UI.createEmptyState('No saved jobs yet. Save jobs from the Jobs Feed.', '⭐'));
      return;
    }

    renderSavedJobsTable(jobs);
  }

  /**
   * Render the saved jobs table.
   */
  function renderSavedJobsTable(jobs) {
    const headers = ['Title', 'Company', 'Location', 'Date Saved', 'Actions'];

    const rows = jobs.map(function (job) {
      // Remove button
      var removeBtn = document.createElement('button');
      removeBtn.className = 'btn btn--danger btn--sm';
      removeBtn.textContent = 'Remove';
      removeBtn.addEventListener('click', function () {
        handleRemoveJob(job.job_url, removeBtn);
      });

      return [
        job.title || '—',
        job.company || '—',
        job.location || 'Remote',
        job.date_saved ? job.date_saved.split('T')[0] : '—',
        removeBtn,
      ];
    });

    savedJobsContainer.innerHTML = '';
    savedJobsContainer.appendChild(UI.createDataTable(headers, rows));
  }

  /**
   * Handle removing a saved job.
   */
  async function handleRemoveJob(jobUrl, btn) {
    btn.disabled = true;
    btn.textContent = 'Removing...';

    var result = await API.removeSavedJob(jobUrl);

    if (result.ok) {
      UI.showToast('Job removed from saved list', 'success');
      // Reload the list
      loadSavedJobs();
    } else {
      btn.disabled = false;
      btn.textContent = 'Remove';
      UI.showToast('Failed to remove job', 'error');
    }
  }

  // Initialize
  function init() {
    loadSavedJobs();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
