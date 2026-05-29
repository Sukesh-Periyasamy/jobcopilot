/**
 * JobCopilot API Abstraction Layer
 * Handles all communication with the FastAPI backend on Render.
 */

const API_BASE = 'https://jobcopilot.onrender.com';

/**
 * Internal helper: performs a fetch request and returns a structured response.
 * @param {string} endpoint - API path (e.g. '/jobs')
 * @param {object} options - fetch options (method, headers, body)
 * @returns {Promise<{ok: boolean, data?: any, error?: string, status?: number}>}
 */
async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const defaultHeaders = { 'Content-Type': 'application/json' };

  const config = {
    headers: { ...defaultHeaders, ...options.headers },
    ...options,
  };

  // Remove headers from spread to avoid duplication
  if (options.headers) {
    config.headers = { ...defaultHeaders, ...options.headers };
  }

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch {
        errorData = { detail: response.statusText };
      }
      return {
        ok: false,
        status: response.status,
        error: errorData.detail || errorData.message || `Request failed with status ${response.status}`,
      };
    }

    const data = await response.json();
    return { ok: true, data };
  } catch (err) {
    return {
      ok: false,
      status: 0,
      error: err.message || 'Network error: unable to reach the server',
    };
  }
}

/**
 * GET /health — Check backend health status.
 */
async function getHealth() {
  return request('/health');
}

/**
 * GET /jobs — Fetch paginated jobs with optional filters.
 * @param {object} params - Query parameters (page, page_size, source, location, company, keyword, job_type, date_from, date_to, search_term)
 */
async function getJobs(params = {}) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, value);
    }
  }
  const queryString = query.toString();
  const endpoint = queryString ? `/jobs?${queryString}` : '/jobs';
  return request(endpoint);
}

/**
 * GET /jobs/recent — Fetch the 10 most recently posted jobs.
 */
async function getRecentJobs() {
  return request('/jobs/recent');
}

/**
 * GET /jobs/search — Full-text search across title and description.
 * @param {string} q - Search query
 * @param {object} params - Optional pagination params (page, page_size)
 */
async function searchJobs(q, params = {}) {
  const query = new URLSearchParams({ q, ...params });
  return request(`/jobs/search?${query.toString()}`);
}

/**
 * GET /jobs/company/{name} — Fetch jobs from a specific company.
 * @param {string} name - Company name
 */
async function getJobsByCompany(name) {
  return request(`/jobs/company/${encodeURIComponent(name)}`);
}

/**
 * GET /stats — Fetch dashboard summary metrics.
 */
async function getStats() {
  return request('/stats');
}

/**
 * GET /watchlist — Fetch all watchlist companies.
 */
async function getWatchlist() {
  return request('/watchlist');
}

/**
 * POST /watchlist — Add a company to the watchlist.
 * @param {string} companyName - Company name to add
 */
async function addToWatchlist(companyName) {
  return request('/watchlist', {
    method: 'POST',
    body: JSON.stringify({ company_name: companyName }),
  });
}

/**
 * DELETE /watchlist/{company} — Remove a company from the watchlist.
 * @param {string} company - Company name to remove
 */
async function removeFromWatchlist(company) {
  return request(`/watchlist/${encodeURIComponent(company)}`, {
    method: 'DELETE',
  });
}

/**
 * POST /save-job — Save a job to the saved_jobs collection.
 * @param {object} jobData - { job_url, title, company, location, source, date_posted }
 */
async function saveJob(jobData) {
  return request('/save-job', {
    method: 'POST',
    body: JSON.stringify(jobData),
  });
}

/**
 * DELETE /save-job/{job_url} — Remove a job from saved jobs.
 * @param {string} jobUrl - URL of the job to remove
 */
async function removeSavedJob(jobUrl) {
  return request(`/save-job/${encodeURIComponent(jobUrl)}`, {
    method: 'DELETE',
  });
}

/**
 * GET /saved-jobs — Fetch all saved jobs.
 */
async function getSavedJobs() {
  return request('/saved-jobs');
}

/**
 * POST /apply-job — Mark a job as applied.
 * @param {object} jobData - { job_url, title, company, location, status }
 */
async function applyJob(jobData) {
  return request('/apply-job', {
    method: 'POST',
    body: JSON.stringify(jobData),
  });
}

/**
 * PATCH /apply-job/{job_url} — Update application status.
 * @param {string} jobUrl - URL of the applied job
 * @param {string} status - New status value
 */
async function updateApplicationStatus(jobUrl, status) {
  return request(`/apply-job/${encodeURIComponent(jobUrl)}`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
}

/**
 * GET /applied-jobs — Fetch all applied jobs.
 */
async function getAppliedJobs() {
  return request('/applied-jobs');
}

// Attach to window for non-module usage (GitHub Pages, no build step)
if (typeof window !== 'undefined') {
  window.JobCopilotAPI = {
    getHealth,
    getJobs,
    getRecentJobs,
    searchJobs,
    getJobsByCompany,
    getStats,
    getWatchlist,
    addToWatchlist,
    removeFromWatchlist,
    saveJob,
    removeSavedJob,
    getSavedJobs,
    applyJob,
    updateApplicationStatus,
    getAppliedJobs,
  };
}
