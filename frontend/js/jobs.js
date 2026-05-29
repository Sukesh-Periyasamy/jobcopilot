/**
 * JobCopilot — Jobs Feed Page Logic
 * Fetches paginated jobs with filters, renders table with Apply/Save actions.
 */

(function () {
  const API = window.JobCopilotAPI;
  const UI = window.JobCopilotUI;

  const jobsTableContainer = document.getElementById('jobs-table-container');
  const paginationContainer = document.getElementById('pagination-container');

  // Filter elements
  const filterSource = document.getElementById('filter-source');
  const filterLocation = document.getElementById('filter-location');
  const filterCompany = document.getElementById('filter-company');
  const filterKeyword = document.getElementById('filter-keyword');
  const filterJobType = document.getElementById('filter-job-type');
  const filterDateFrom = document.getElementById('filter-date-from');
  const filterDateTo = document.getElementById('filter-date-to');
  const btnApplyFilters = document.getElementById('btn-apply-filters');
  const btnClearFilters = document.getElementById('btn-clear-filters');

  let currentPage = 1;
  const pageSize = 50;

  /**
   * Gather current filter values.
   */
  function getFilters() {
    return {
      source: filterSource.value,
      location: filterLocation.value.trim(),
      company: filterCompany.value.trim(),
      keyword: filterKeyword.value.trim(),
      job_type: filterJobType.value,
      date_from: filterDateFrom.value,
      date_to: filterDateTo.value,
    };
  }

  /**
   * Load jobs with current filters and page.
   */
  async function loadJobs(page) {
    currentPage = page || 1;

    // Show loading skeletons
    jobsTableContainer.innerHTML = '';
    for (let i = 0; i < 6; i++) {
      var skel = document.createElement('div');
      skel.className = 'skeleton skeleton--row';
      jobsTableContainer.appendChild(skel);
    }
    paginationContainer.innerHTML = '';

    const filters = getFilters();
    const params = Object.assign({}, filters, {
      page: currentPage,
      page_size: pageSize,
    });

    const result = await API.getJobs(params);

    if (!result.ok) {
      jobsTableContainer.innerHTML = '';
      jobsTableContainer.appendChild(UI.createEmptyState('Unable to load jobs. Is the backend running?', '⚠️'));
      return;
    }

    const data = result.data;
    const jobs = data.jobs || [];
    const totalPages = data.total_pages || 1;

    if (jobs.length === 0) {
      jobsTableContainer.innerHTML = '';
      jobsTableContainer.appendChild(UI.createEmptyState('No jobs match your filters.', '🔍'));
      paginationContainer.innerHTML = '';
      return;
    }

    renderJobsTable(jobs);
    renderPagination(currentPage, totalPages);
  }

  /**
   * Render the jobs table.
   */
  function renderJobsTable(jobs) {
    const headers = ['Title', 'Company', 'Location', 'Source', 'Date Posted', 'Fresh', 'Actions'];

    const rows = jobs.map(function (job) {
      // Fresh badge
      var badge = UI.createFreshBadge(job.date_posted);

      // Actions container
      var actionsDiv = document.createElement('div');
      actionsDiv.style.display = 'flex';
      actionsDiv.style.gap = 'var(--space-xs)';

      // Apply button
      var applyBtn = document.createElement('a');
      applyBtn.href = job.job_url || '#';
      applyBtn.target = '_blank';
      applyBtn.rel = 'noopener noreferrer';
      applyBtn.className = 'btn btn--primary btn--sm';
      applyBtn.textContent = 'Apply ↗';
      actionsDiv.appendChild(applyBtn);

      // Save button
      var saveBtn = document.createElement('button');
      saveBtn.className = 'btn btn--secondary btn--sm';
      saveBtn.textContent = 'Save';
      saveBtn.addEventListener('click', function () {
        handleSaveJob(job, saveBtn);
      });
      actionsDiv.appendChild(saveBtn);

      return [
        job.title || '—',
        job.company || '—',
        job.location || 'Remote',
        job.source || '—',
        job.date_posted || '—',
        badge,
        actionsDiv,
      ];
    });

    jobsTableContainer.innerHTML = '';
    jobsTableContainer.appendChild(UI.createDataTable(headers, rows));
  }

  /**
   * Render pagination controls.
   */
  function renderPagination(page, totalPages) {
    paginationContainer.innerHTML = '';
    var pagination = UI.createPagination(page, totalPages, function (newPage) {
      loadJobs(newPage);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    paginationContainer.appendChild(pagination);
  }

  /**
   * Handle saving a job.
   */
  async function handleSaveJob(job, btn) {
    btn.disabled = true;
    btn.textContent = 'Saving...';

    var jobData = {
      job_url: job.job_url,
      title: job.title,
      company: job.company,
      location: job.location || '',
      source: job.source || '',
      date_posted: job.date_posted || '',
    };

    var result = await API.saveJob(jobData);

    if (result.ok) {
      btn.textContent = '✓ Saved';
      btn.className = 'btn btn--ghost btn--sm';
      UI.showToast('Job saved successfully', 'success');
    } else {
      btn.disabled = false;
      btn.textContent = 'Save';
      if (result.status === 409 || (result.error && result.error.toLowerCase().includes('already'))) {
        UI.showToast('Job already saved', 'info');
        btn.textContent = '✓ Saved';
        btn.className = 'btn btn--ghost btn--sm';
      } else {
        UI.showToast('Failed to save job', 'error');
      }
    }
  }

  // Event listeners
  btnApplyFilters.addEventListener('click', function () {
    loadJobs(1);
  });

  btnClearFilters.addEventListener('click', function () {
    filterSource.value = '';
    filterLocation.value = '';
    filterCompany.value = '';
    filterKeyword.value = '';
    filterJobType.value = '';
    filterDateFrom.value = '';
    filterDateTo.value = '';
    loadJobs(1);
  });

  // Allow Enter key to trigger filter
  [filterLocation, filterCompany, filterKeyword].forEach(function (input) {
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        loadJobs(1);
      }
    });
  });

  // Initialize
  function init() {
    loadJobs(1);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
