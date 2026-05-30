/**
 * JobCopilot — Reusable UI Components
 * Dark mode glassmorphism design system
 */

// ============================================
// Fresh Badge — Based on date_posted recency
// ============================================

/**
 * Creates a fresh badge based on how recently a job was posted.
 * 🟢 Posted Today | 🟡 Posted This Week | ⚪ Older
 * @param {string} datePosted - Date string in YYYY-MM-DD format
 * @returns {HTMLElement} Badge element
 */
function createFreshBadge(datePosted) {
  const badge = document.createElement('span');
  badge.classList.add('badge');

  if (!datePosted) {
    badge.classList.add('badge--gray');
    badge.textContent = '⚪ Unknown';
    return badge;
  }

  const posted = new Date(datePosted + 'T00:00:00');
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const diffMs = today.getTime() - posted.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays <= 0) {
    badge.classList.add('badge--green');
    badge.textContent = '🟢 Posted Today';
  } else if (diffDays <= 7) {
    badge.classList.add('badge--yellow');
    badge.textContent = '🟡 Posted This Week';
  } else {
    badge.classList.add('badge--gray');
    badge.textContent = '⚪ Older';
  }

  return badge;
}

// ============================================
// Metric Card
// ============================================

/**
 * Creates a metric card for dashboard stats.
 * @param {string} title - Metric label (e.g., "Total Jobs")
 * @param {string|number} value - Metric value
 * @param {string} icon - Emoji or icon character
 * @returns {HTMLElement} Card element
 */
function createMetricCard(title, value, icon) {
  const card = document.createElement('div');
  card.classList.add('card', 'metric-card');

  card.innerHTML = `
    <div class="metric-card__icon">${icon}</div>
    <div class="metric-card__value">${value}</div>
    <div class="metric-card__title">${title}</div>
  `;

  return card;
}

// ============================================
// Source Platform Badge
// ============================================

/**
 * Creates a source platform badge with color coding.
 * @param {Object} job - Job object with source_platform and/or source fields
 * @returns {HTMLElement} Badge element
 */
function createSourceBadge(job) {
  var platform = (job.source_platform || job.source || '').toLowerCase();

  var colorMap = {
    linkedin: 'blue',
    indeed: 'purple',
    naukri: 'red',
    google: 'green',
    workday: 'orange',
    greenhouse: 'teal',
    lever: 'indigo',
    ashby: 'pink',
    successfactors: 'amber',
  };

  var color = colorMap[platform] || 'gray';
  var label = platform.charAt(0).toUpperCase() + platform.slice(1);

  var badge = document.createElement('span');
  badge.className = 'badge badge--pill badge--' + color;
  badge.textContent = label;

  return badge;
}

// ============================================
// Job Card
// ============================================

/**
 * Creates a job card with title, company, meta info, and actions.
 * @param {Object} job - Job object from API
 * @param {string} job.title - Job title
 * @param {string} job.company - Company name
 * @param {string} job.location - Job location
 * @param {string} job.source - Job source (linkedin, indeed, etc.)
 * @param {string} job.job_url - URL to apply
 * @param {string} job.date_posted - Date in YYYY-MM-DD format
 * @param {string} [job.job_type] - Job type
 * @returns {HTMLElement} Job card element
 */
function createJobCard(job) {
  const card = document.createElement('div');
  card.classList.add('card', 'job-card');

  const freshBadge = createFreshBadge(job.date_posted);

  card.innerHTML = `
    <div class="job-card__header">
      <div>
        <div class="job-card__title">${escapeHtml(job.title)}</div>
        <div class="job-card__company">${escapeHtml(job.company)}</div>
      </div>
    </div>
    <div class="job-card__meta">
      <span>${escapeHtml(job.location || 'Remote')}</span>
      ${job.job_type ? `<span>${escapeHtml(job.job_type)}</span>` : ''}
      ${job.date_posted ? `<span>${job.date_posted}</span>` : ''}
    </div>
    <div class="job-card__actions">
      <a href="${escapeHtml(job.job_url)}" target="_blank" rel="noopener noreferrer" class="btn btn--primary btn--sm">Apply ↗</a>
      <button class="btn btn--secondary btn--sm" data-action="save" data-job-url="${escapeHtml(job.job_url)}">Save</button>
    </div>
  `;

  // Insert source badge into the meta section
  const meta = card.querySelector('.job-card__meta');
  const sourceBadge = createSourceBadge(job);
  meta.insertBefore(sourceBadge, meta.firstChild);

  // Insert fresh badge into the header
  const header = card.querySelector('.job-card__header');
  header.appendChild(freshBadge);

  return card;
}

// ============================================
// Data Table
// ============================================

/**
 * Creates a data table with headers and rows.
 * @param {string[]} headers - Column header labels
 * @param {Array<Array<string|HTMLElement>>} rows - 2D array of cell content
 * @returns {HTMLElement} Table container element
 */
function createDataTable(headers, rows) {
  const container = document.createElement('div');
  container.classList.add('table-container');

  const table = document.createElement('table');
  table.classList.add('data-table');

  // Build thead
  const thead = document.createElement('thead');
  const headerRow = document.createElement('tr');
  headers.forEach(h => {
    const th = document.createElement('th');
    th.textContent = h;
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);

  // Build tbody
  const tbody = document.createElement('tbody');
  if (rows.length === 0) {
    const emptyRow = document.createElement('tr');
    const emptyCell = document.createElement('td');
    emptyCell.colSpan = headers.length;
    emptyCell.classList.add('text-center', 'text-secondary');
    emptyCell.style.padding = 'var(--space-xl)';
    emptyCell.textContent = 'No data available';
    emptyRow.appendChild(emptyCell);
    tbody.appendChild(emptyRow);
  } else {
    rows.forEach(row => {
      const tr = document.createElement('tr');
      row.forEach(cell => {
        const td = document.createElement('td');
        if (cell instanceof HTMLElement) {
          td.appendChild(cell);
        } else {
          td.textContent = cell;
        }
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
  }
  table.appendChild(tbody);
  container.appendChild(table);

  return container;
}

// ============================================
// Skeleton Loaders
// ============================================

/**
 * Creates a skeleton loader placeholder.
 * @param {'card'|'table'|'list'|'metric'} type - Type of skeleton
 * @param {number} [count=1] - Number of skeleton items
 * @returns {HTMLElement} Skeleton container
 */
function createSkeletonLoader(type, count = 1) {
  const container = document.createElement('div');

  for (let i = 0; i < count; i++) {
    switch (type) {
      case 'card':
        container.innerHTML += `
          <div class="card" style="margin-bottom: var(--space-md);">
            <div class="skeleton skeleton--title"></div>
            <div class="skeleton skeleton--text"></div>
            <div class="skeleton skeleton--text-short"></div>
          </div>
        `;
        break;

      case 'table':
        container.innerHTML += `
          <div class="skeleton skeleton--row"></div>
        `;
        break;

      case 'list':
        container.innerHTML += `
          <div style="padding: var(--space-sm) 0;">
            <div class="skeleton skeleton--text"></div>
          </div>
        `;
        break;

      case 'metric':
        container.innerHTML += `
          <div class="skeleton skeleton--metric"></div>
        `;
        break;

      default:
        container.innerHTML += `
          <div class="skeleton skeleton--card"></div>
        `;
    }
  }

  return container;
}

// ============================================
// Pagination Controls
// ============================================

/**
 * Creates pagination controls.
 * @param {number} currentPage - Current active page (1-indexed)
 * @param {number} totalPages - Total number of pages
 * @param {function} onPageChange - Callback when page changes, receives page number
 * @returns {HTMLElement} Pagination element
 */
function createPagination(currentPage, totalPages, onPageChange) {
  const container = document.createElement('div');
  container.classList.add('pagination');

  if (totalPages <= 1) return container;

  // Previous button
  const prevBtn = document.createElement('button');
  prevBtn.classList.add('pagination__btn');
  prevBtn.textContent = '‹';
  prevBtn.disabled = currentPage <= 1;
  prevBtn.setAttribute('aria-label', 'Previous page');
  prevBtn.addEventListener('click', () => onPageChange(currentPage - 1));
  container.appendChild(prevBtn);

  // Page numbers — show max 7 buttons with ellipsis
  const pages = getPaginationRange(currentPage, totalPages);
  pages.forEach(page => {
    if (page === '...') {
      const ellipsis = document.createElement('span');
      ellipsis.classList.add('pagination__info');
      ellipsis.textContent = '…';
      container.appendChild(ellipsis);
    } else {
      const btn = document.createElement('button');
      btn.classList.add('pagination__btn');
      if (page === currentPage) {
        btn.classList.add('pagination__btn--active');
        btn.setAttribute('aria-current', 'page');
      }
      btn.textContent = page;
      btn.addEventListener('click', () => onPageChange(page));
      container.appendChild(btn);
    }
  });

  // Next button
  const nextBtn = document.createElement('button');
  nextBtn.classList.add('pagination__btn');
  nextBtn.textContent = '›';
  nextBtn.disabled = currentPage >= totalPages;
  nextBtn.setAttribute('aria-label', 'Next page');
  nextBtn.addEventListener('click', () => onPageChange(currentPage + 1));
  container.appendChild(nextBtn);

  return container;
}

/**
 * Calculates which page numbers to display.
 * @param {number} current - Current page
 * @param {number} total - Total pages
 * @returns {Array<number|string>} Array of page numbers and '...' ellipsis
 */
function getPaginationRange(current, total) {
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1);
  }

  if (current <= 3) {
    return [1, 2, 3, 4, 5, '...', total];
  }

  if (current >= total - 2) {
    return [1, '...', total - 4, total - 3, total - 2, total - 1, total];
  }

  return [1, '...', current - 1, current, current + 1, '...', total];
}

// ============================================
// Toast Notifications
// ============================================

let toastContainer = null;

/**
 * Ensures the toast container exists in the DOM.
 */
function ensureToastContainer() {
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.classList.add('toast-container');
    toastContainer.setAttribute('aria-live', 'polite');
    toastContainer.setAttribute('aria-atomic', 'true');
    document.body.appendChild(toastContainer);
  }
}

/**
 * Shows a toast notification.
 * @param {string} message - Toast message text
 * @param {'success'|'error'|'info'} [type='info'] - Toast type
 * @param {number} [duration=3000] - Auto-dismiss duration in ms
 */
function showToast(message, type = 'info', duration = 3000) {
  ensureToastContainer();

  const icons = {
    success: '✓',
    error: '✕',
    info: 'ℹ'
  };

  const toast = document.createElement('div');
  toast.classList.add('toast', `toast--${type}`);
  toast.setAttribute('role', 'alert');
  toast.innerHTML = `
    <span class="toast__icon">${icons[type] || icons.info}</span>
    <span class="toast__message">${escapeHtml(message)}</span>
  `;

  toastContainer.appendChild(toast);

  // Auto-dismiss
  setTimeout(() => {
    toast.classList.add('toast--exit');
    toast.addEventListener('animationend', () => {
      toast.remove();
    });
  }, duration);
}

// ============================================
// Empty State
// ============================================

/**
 * Creates an empty state placeholder.
 * @param {string} message - Message to display
 * @param {string} [icon='📭'] - Emoji icon
 * @returns {HTMLElement} Empty state element
 */
function createEmptyState(message, icon = '📭') {
  const container = document.createElement('div');
  container.classList.add('empty-state');
  container.innerHTML = `
    <div class="empty-state__icon">${icon}</div>
    <p class="empty-state__message">${escapeHtml(message)}</p>
  `;
  return container;
}

// ============================================
// Utility Functions
// ============================================

/**
 * Escapes HTML special characters to prevent XSS.
 * @param {string} str - Raw string
 * @returns {string} Escaped string
 */
function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// ============================================
// Exports (for ES module usage or global scope)
// ============================================

// Attach to window for non-module usage
if (typeof window !== 'undefined') {
  window.JobCopilotUI = {
    createMetricCard,
    createJobCard,
    createDataTable,
    createSkeletonLoader,
    createFreshBadge,
    createSourceBadge,
    createPagination,
    showToast,
    createEmptyState,
    escapeHtml
  };
}
