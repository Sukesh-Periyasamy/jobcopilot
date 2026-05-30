/**
 * JobCopilot — Internships Page Logic
 * Fetches and displays internship listings from the /internships endpoint.
 */

(function () {
  'use strict';

  // State
  let currentPage = 1;
  const pageSize = 50;
  let currentKeyword = '';

  // DOM references
  const container = document.getElementById('internships-container');
  const paginationContainer = document.getElementById('pagination-container');
  const filterKeyword = document.getElementById('filter-keyword');
  const btnApply = document.getElementById('btn-apply-filter');
  const btnClear = document.getElementById('btn-clear-filter');

  /**
   * Fetch internships from the API with optional keyword filter.
   * @param {number} page - Page number
   * @param {string} keyword - Optional keyword filter
   */
  async function fetchInternships(page, keyword) {
    showLoading();

    const params = { page: page, page_size: pageSize };
    if (keyword) {
      params.keyword = keyword;
    }

    const result = await window.JobCopilotAPI.getInternships(params);

    if (!result.ok) {
      showError();
      return;
    }

    const data = result.data;
    const items = data.items || [];
    const total = data.total || 0;
    const totalPages = Math.ceil(total / pageSize);

    if (items.length === 0) {
      showEmpty();
    } else {
      renderInternships(items);
    }

    renderPagination(page, totalPages);
  }

  /**
   * Show loading skeleton state.
   */
  function showLoading() {
    container.innerHTML = '';
    for (let i = 0; i < 6; i++) {
      const skeleton = document.createElement('div');
      skeleton.className = 'skeleton skeleton--row';
      container.appendChild(skeleton);
    }
    paginationContainer.innerHTML = '';
  }

  /**
   * Show error state.
   */
  function showError() {
    container.innerHTML = '';
    const errorState = document.createElement('div');
    errorState.classList.add('empty-state');
    errorState.innerHTML = `
      <div class="empty-state__icon">⚠️</div>
      <p class="empty-state__message">Failed to load internships</p>
      <div class="empty-state__action">
        <button class="btn btn--primary" id="btn-retry">Retry</button>
      </div>
    `;
    container.appendChild(errorState);
    paginationContainer.innerHTML = '';

    document.getElementById('btn-retry').addEventListener('click', function () {
      fetchInternships(currentPage, currentKeyword);
    });
  }

  /**
   * Show empty state when no results found.
   */
  function showEmpty() {
    container.innerHTML = '';
    const emptyState = document.createElement('div');
    emptyState.classList.add('empty-state');
    emptyState.innerHTML = `
      <div class="empty-state__icon">📭</div>
      <p class="empty-state__message">No internships found</p>
    `;
    container.appendChild(emptyState);
    paginationContainer.innerHTML = '';
  }

  /**
   * Render internship listings as a data table.
   * @param {Array} internships - Array of internship job objects
   */
  function renderInternships(internships) {
    container.innerHTML = '';

    const headers = ['Title', 'Company', 'Location', 'Date Posted', 'Link'];
    const rows = internships.map(function (job) {
      const link = document.createElement('a');
      link.href = job.job_url || '#';
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.className = 'btn btn--primary btn--sm';
      link.textContent = 'View ↗';

      return [
        job.title || '—',
        job.company || '—',
        job.location || '—',
        job.date_posted || '—',
        link,
      ];
    });

    const table = window.JobCopilotUI.createDataTable(headers, rows);
    container.appendChild(table);
  }

  /**
   * Render pagination controls.
   * @param {number} page - Current page
   * @param {number} totalPages - Total pages
   */
  function renderPagination(page, totalPages) {
    paginationContainer.innerHTML = '';
    if (totalPages <= 1) return;

    const pagination = window.JobCopilotUI.createPagination(page, totalPages, function (newPage) {
      currentPage = newPage;
      fetchInternships(currentPage, currentKeyword);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    paginationContainer.appendChild(pagination);
  }

  // Event listeners
  btnApply.addEventListener('click', function () {
    currentKeyword = filterKeyword.value;
    currentPage = 1;
    fetchInternships(currentPage, currentKeyword);
  });

  btnClear.addEventListener('click', function () {
    filterKeyword.value = '';
    currentKeyword = '';
    currentPage = 1;
    fetchInternships(currentPage, currentKeyword);
  });

  // Apply filter immediately on dropdown change
  filterKeyword.addEventListener('change', function () {
    currentKeyword = filterKeyword.value;
    currentPage = 1;
    fetchInternships(currentPage, currentKeyword);
  });

  // Initial load
  fetchInternships(currentPage, currentKeyword);
})();
