/**
 * JobCopilot — Jobs Page with Universal Smart Search
 * Uses /jobs/smart-search for weighted, synonym-expanded search.
 * Falls back to /jobs for initial load (all jobs).
 */

(function () {
  'use strict';

  const API = window.JobCopilotAPI;
  const UI = window.JobCopilotUI;

  // DOM
  const searchInput = document.getElementById('search-input');
  const searchBtn = document.getElementById('search-btn');
  const facetsContainer = document.getElementById('facets-container');
  const searchMeta = document.getElementById('search-meta');
  const resultsContainer = document.getElementById('results-container');
  const exportCsvBtn = document.getElementById('btn-export-csv');
  const exportXlsxBtn = document.getElementById('btn-export-xlsx');

  let currentQuery = '';
  let currentPage = 1;
  const pageSize = 50;

  /**
   * Perform smart search and render results.
   */
  async function doSearch(query, page) {
    currentQuery = query;
    currentPage = page || 1;

    showLoading();

    let result;
    if (!query || !query.trim()) {
      // No query — show all jobs
      result = await API.getJobs({ page: currentPage, page_size: pageSize });
      if (result.ok) {
        renderJobsTable(result.data.jobs || []);
        searchMeta.style.display = '';
        searchMeta.textContent = result.data.total + ' total jobs';
        facetsContainer.style.display = 'none';
      } else {
        showError();
      }
      return;
    }

    // Smart search
    result = await API.request('/jobs/smart-search?q=' + encodeURIComponent(query) + '&page=' + currentPage + '&page_size=' + pageSize);

    if (!result.ok) {
      showError();
      return;
    }

    const data = result.data;

    // Meta
    searchMeta.style.display = '';
    searchMeta.textContent = data.total + ' results for "' + data.query + '"' +
      (data.expanded_terms && data.expanded_terms.length > 1 ? ' (also searched: ' + data.expanded_terms.slice(1).join(', ') + ')' : '');

    // Facets
    if (data.facets && data.total > 0) {
      renderFacets(data.facets);
    } else {
      facetsContainer.style.display = 'none';
    }

    // Results
    if (data.results && data.results.length > 0) {
      renderSmartResults(data.results);
    } else if (data.suggestions && data.suggestions.length > 0) {
      renderSuggestions(data.suggestions);
    } else {
      renderEmpty();
    }
  }

  function showLoading() {
    resultsContainer.innerHTML = '';
    for (var i = 0; i < 5; i++) {
      var sk = document.createElement('div');
      sk.className = 'skeleton skeleton--row';
      resultsContainer.appendChild(sk);
    }
    facetsContainer.style.display = 'none';
    searchMeta.style.display = 'none';
  }

  function showError() {
    resultsContainer.innerHTML = '';
    var el = document.createElement('div');
    el.className = 'empty-state';
    el.innerHTML = '<div class="empty-state__icon">⚠️</div><p class="empty-state__message">Failed to load jobs</p>';
    resultsContainer.appendChild(el);
  }

  function renderEmpty() {
    resultsContainer.innerHTML = '';
    var el = document.createElement('div');
    el.className = 'empty-state';
    el.innerHTML = '<div class="empty-state__icon">📭</div><p class="empty-state__message">No jobs found</p>';
    resultsContainer.appendChild(el);
  }

  function renderSuggestions(suggestions) {
    resultsContainer.innerHTML = '';
    var el = document.createElement('div');
    el.className = 'empty-state';
    var links = suggestions.map(function (s) {
      return '<a class="suggestion-link" style="color: var(--accent-blue); cursor: pointer; margin: 0 4px;">' + escapeHtml(s) + '</a>';
    }).join(' · ');
    el.innerHTML = '<div class="empty-state__icon">🔍</div>' +
      '<p class="empty-state__message">No exact matches found</p>' +
      '<p style="color: var(--text-secondary); font-size: var(--font-size-sm);">Try: ' + links + '</p>';
    resultsContainer.appendChild(el);

    // Add click handlers to suggestions
    el.querySelectorAll('.suggestion-link').forEach(function (link) {
      link.addEventListener('click', function () {
        searchInput.value = link.textContent;
        doSearch(link.textContent, 1);
      });
    });
  }

  function renderSmartResults(results) {
    resultsContainer.innerHTML = '';
    var headers = ['Score', 'Title', 'Company', 'Location', 'Date', 'Link'];
    var rows = results.map(function (job) {
      var link = document.createElement('a');
      link.href = job.job_url || '#';
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.className = 'btn btn--primary btn--sm';
      link.textContent = 'View ↗';

      var scoreBadge = document.createElement('span');
      scoreBadge.style.cssText = 'background: var(--accent-blue); color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 600;';
      scoreBadge.textContent = job.search_score;

      return [scoreBadge, job.title || '—', job.company || '—', job.location || '—', job.date_posted || '—', link];
    });

    resultsContainer.appendChild(UI.createDataTable(headers, rows));
  }

  function renderJobsTable(jobs) {
    resultsContainer.innerHTML = '';
    if (!jobs || jobs.length === 0) {
      renderEmpty();
      return;
    }
    var headers = ['Title', 'Company', 'Location', 'Source', 'Date', 'Link'];
    var rows = jobs.map(function (job) {
      var link = document.createElement('a');
      link.href = job.job_url || '#';
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.className = 'btn btn--primary btn--sm';
      link.textContent = 'View ↗';
      return [job.title || '—', job.company || '—', job.location || '—', job.source_platform || '—', job.date_posted || '—', link];
    });
    resultsContainer.appendChild(UI.createDataTable(headers, rows));
  }

  function renderFacets(facets) {
    facetsContainer.innerHTML = '';
    facetsContainer.style.display = '';

    var groups = [
      { title: 'Companies', items: facets.top_companies },
      { title: 'Locations', items: facets.top_locations },
      { title: 'Collections', items: facets.top_collections },
    ];

    groups.forEach(function (group) {
      if (!group.items || group.items.length === 0) return;

      var div = document.createElement('div');
      div.className = 'facet-group';
      div.innerHTML = '<div class="facet-group__title">' + group.title + '</div>';

      group.items.slice(0, 5).forEach(function (item) {
        var el = document.createElement('div');
        el.className = 'facet-item';
        el.innerHTML = escapeHtml(item.name) + ' <span class="facet-item__count">(' + item.count + ')</span>';
        el.addEventListener('click', function () {
          searchInput.value = item.name;
          doSearch(item.name, 1);
        });
        div.appendChild(el);
      });

      facetsContainer.appendChild(div);
    });
  }

  function escapeHtml(str) {
    if (!str) return '';
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  // Event listeners
  searchBtn.addEventListener('click', function () {
    doSearch(searchInput.value, 1);
  });

  searchInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') {
      doSearch(searchInput.value, 1);
    }
  });

  // Example links
  document.querySelectorAll('.example-link').forEach(function (link) {
    link.addEventListener('click', function () {
      var q = link.getAttribute('data-q');
      searchInput.value = q;
      doSearch(q, 1);
    });
  });

  // Export buttons
  exportCsvBtn.addEventListener('click', async function () {
    var result = await API.exportJobsCsv({});
    if (result.ok) {
      var url = URL.createObjectURL(result.blob);
      var a = document.createElement('a');
      a.href = url;
      a.download = 'jobs.csv';
      a.click();
      URL.revokeObjectURL(url);
    }
  });

  exportXlsxBtn.addEventListener('click', async function () {
    var result = await API.exportJobsXlsx({});
    if (result.ok) {
      var url = URL.createObjectURL(result.blob);
      var a = document.createElement('a');
      a.href = url;
      a.download = 'jobs.xlsx';
      a.click();
      URL.revokeObjectURL(url);
    }
  });

  // Initial load — show all jobs
  doSearch('', 1);
})();
