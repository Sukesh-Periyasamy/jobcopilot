/**
 * JobCopilot — Watchlist Page Logic
 * Fetches watchlist, renders company list, add/remove companies.
 * Client-side validation: max 50 entries, max 100 chars per name.
 */

(function () {
  const API = window.JobCopilotAPI;
  const UI = window.JobCopilotUI;

  const watchlistContainer = document.getElementById('watchlist-container');
  const inputCompanyName = document.getElementById('input-company-name');
  const btnAddCompany = document.getElementById('btn-add-company');
  const watchlistStatus = document.getElementById('watchlist-status');

  const MAX_COMPANIES = 50;
  const MAX_NAME_LENGTH = 100;

  // Default companies shown as reference
  const DEFAULT_COMPANIES = [
    'Siemens Healthineers',
    'GE HealthCare',
    'Philips',
    'Medtronic',
    'Abbott',
    'Dozee',
  ];

  let currentWatchlist = [];

  /**
   * Load and render the watchlist.
   */
  async function loadWatchlist() {
    const result = await API.getWatchlist();

    if (!result.ok) {
      watchlistContainer.innerHTML = '';
      watchlistContainer.appendChild(UI.createEmptyState('Unable to load watchlist.', '⚠️'));
      updateStatus();
      return;
    }

    // API may return array of strings or array of objects
    var data = result.data || [];
    if (data.length > 0 && typeof data[0] === 'object') {
      currentWatchlist = data.map(function (item) { return item.company_name || item.name || ''; });
    } else {
      currentWatchlist = data;
    }

    renderWatchlist();
    updateStatus();
  }

  /**
   * Render the watchlist table.
   */
  function renderWatchlist() {
    if (currentWatchlist.length === 0) {
      watchlistContainer.innerHTML = '';
      var msg = 'No companies in your watchlist. Default companies: ' + DEFAULT_COMPANIES.join(', ');
      watchlistContainer.appendChild(UI.createEmptyState(msg, '👀'));
      return;
    }

    const headers = ['#', 'Company Name', 'Actions'];
    const rows = currentWatchlist.map(function (company, index) {
      // Remove button
      var removeBtn = document.createElement('button');
      removeBtn.className = 'btn btn--danger btn--sm';
      removeBtn.textContent = 'Remove';
      removeBtn.addEventListener('click', function () {
        handleRemoveCompany(company, removeBtn);
      });

      return [
        String(index + 1),
        company,
        removeBtn,
      ];
    });

    watchlistContainer.innerHTML = '';
    watchlistContainer.appendChild(UI.createDataTable(headers, rows));
  }

  /**
   * Update the status text showing count.
   */
  function updateStatus() {
    var count = currentWatchlist.length;
    watchlistStatus.textContent = count + ' / ' + MAX_COMPANIES + ' companies tracked';
  }

  /**
   * Validate and add a company.
   */
  async function handleAddCompany() {
    var name = inputCompanyName.value.trim();

    // Client-side validation
    if (!name) {
      UI.showToast('Please enter a company name', 'error');
      return;
    }

    if (name.length > MAX_NAME_LENGTH) {
      UI.showToast('Company name must be 100 characters or less', 'error');
      return;
    }

    if (currentWatchlist.length >= MAX_COMPANIES) {
      UI.showToast('Watchlist is full (max ' + MAX_COMPANIES + ' companies)', 'error');
      return;
    }

    // Check for duplicates (case-insensitive)
    var isDuplicate = currentWatchlist.some(function (c) {
      return c.toLowerCase() === name.toLowerCase();
    });
    if (isDuplicate) {
      UI.showToast('Company already in watchlist', 'info');
      return;
    }

    btnAddCompany.disabled = true;
    btnAddCompany.textContent = 'Adding...';

    var result = await API.addToWatchlist(name);

    btnAddCompany.disabled = false;
    btnAddCompany.textContent = 'Add Company';

    if (result.ok) {
      inputCompanyName.value = '';
      UI.showToast(name + ' added to watchlist', 'success');
      loadWatchlist();
    } else {
      UI.showToast(result.error || 'Failed to add company', 'error');
    }
  }

  /**
   * Handle removing a company from the watchlist.
   */
  async function handleRemoveCompany(company, btn) {
    btn.disabled = true;
    btn.textContent = 'Removing...';

    var result = await API.removeFromWatchlist(company);

    if (result.ok) {
      UI.showToast(company + ' removed from watchlist', 'success');
      loadWatchlist();
    } else {
      btn.disabled = false;
      btn.textContent = 'Remove';
      UI.showToast(result.error || 'Failed to remove company', 'error');
    }
  }

  // Event listeners
  btnAddCompany.addEventListener('click', handleAddCompany);

  inputCompanyName.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') {
      handleAddCompany();
    }
  });

  // Initialize
  function init() {
    loadWatchlist();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
