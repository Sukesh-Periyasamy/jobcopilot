/**
 * JobCopilot Analytics Page
 * Fetches analytics data and renders Chart.js charts.
 */

(function () {
  'use strict';

  // --- Chart color palette (matches dark mode design system) ---
  const CHART_COLORS = [
    'rgba(59, 130, 246, 0.8)',   // blue
    'rgba(34, 197, 94, 0.8)',    // green
    'rgba(168, 85, 247, 0.8)',   // purple
    'rgba(234, 179, 8, 0.8)',    // yellow
    'rgba(239, 68, 68, 0.8)',    // red
    'rgba(20, 184, 166, 0.8)',   // teal
    'rgba(249, 115, 22, 0.8)',   // orange
    'rgba(236, 72, 153, 0.8)',   // pink
    'rgba(99, 102, 241, 0.8)',   // indigo
    'rgba(245, 158, 11, 0.8)',   // amber
    'rgba(139, 92, 246, 0.8)',   // violet
    'rgba(6, 182, 212, 0.8)',    // cyan
    'rgba(132, 204, 22, 0.8)',   // lime
    'rgba(244, 63, 94, 0.8)',    // rose
    'rgba(14, 165, 233, 0.8)',   // sky
    'rgba(217, 70, 239, 0.8)',   // fuchsia
    'rgba(251, 146, 60, 0.8)',   // orange-light
    'rgba(74, 222, 128, 0.8)',   // green-light
    'rgba(96, 165, 250, 0.8)',   // blue-light
    'rgba(192, 132, 252, 0.8)',  // purple-light
  ];

  const CHART_BORDERS = CHART_COLORS.map(c => c.replace('0.8)', '1)'));

  // --- Chart.js global defaults for dark mode ---
  Chart.defaults.color = '#a1a1a1';
  Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.08)';
  Chart.defaults.plugins.legend.labels.color = '#a1a1a1';
  Chart.defaults.plugins.legend.labels.padding = 16;

  // --- DOM references ---
  const loadingState = document.getElementById('loading-state');
  const errorState = document.getElementById('error-state');
  const chartsContent = document.getElementById('charts-content');
  const retryBtn = document.getElementById('retry-btn');

  // --- State management ---
  let chartInstances = [];

  /**
   * Show a specific UI state (loading, error, or charts).
   */
  function showState(state) {
    loadingState.style.display = state === 'loading' ? '' : 'none';
    errorState.style.display = state === 'error' ? '' : 'none';
    chartsContent.style.display = state === 'charts' ? '' : 'none';
  }

  /**
   * Destroy all existing chart instances to prevent memory leaks.
   */
  function destroyCharts() {
    chartInstances.forEach(chart => chart.destroy());
    chartInstances = [];
  }

  /**
   * Create a horizontal bar chart.
   */
  function createBarChart(canvasId, labels, data, label) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    const chart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: label,
          data: data,
          backgroundColor: CHART_COLORS.slice(0, data.length),
          borderColor: CHART_BORDERS.slice(0, data.length),
          borderWidth: 1,
          borderRadius: 4,
        }],
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
        },
        scales: {
          x: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#a1a1a1' },
          },
          y: {
            grid: { display: false },
            ticks: { color: '#ededed', font: { size: 11 } },
          },
        },
      },
    });
    chartInstances.push(chart);
  }

  /**
   * Create a doughnut chart.
   */
  function createDoughnutChart(canvasId, labels, data) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    const chart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: data,
          backgroundColor: [
            'rgba(59, 130, 246, 0.8)',
            'rgba(168, 85, 247, 0.8)',
          ],
          borderColor: [
            'rgba(59, 130, 246, 1)',
            'rgba(168, 85, 247, 1)',
          ],
          borderWidth: 1,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: '#ededed', padding: 16 },
          },
        },
        cutout: '60%',
      },
    });
    chartInstances.push(chart);
  }

  /**
   * Render all charts from analytics data.
   */
  function renderCharts(data) {
    destroyCharts();

    // Jobs by Source (bar chart)
    if (data.jobs_per_source && data.jobs_per_source.length > 0) {
      const labels = data.jobs_per_source.map(item => item.source || 'Unknown');
      const counts = data.jobs_per_source.map(item => item.count);
      createBarChart('chart-source', labels, counts, 'Jobs');
    }

    // Jobs by ATS Platform (bar chart)
    if (data.jobs_per_platform && data.jobs_per_platform.length > 0) {
      const labels = data.jobs_per_platform.map(item => item.platform || 'Unknown');
      const counts = data.jobs_per_platform.map(item => item.count);
      createBarChart('chart-platform', labels, counts, 'Jobs');
    }

    // Jobs by Location (bar chart)
    if (data.jobs_per_location && data.jobs_per_location.length > 0) {
      const labels = data.jobs_per_location.map(item => item.location || 'Unknown');
      const counts = data.jobs_per_location.map(item => item.count);
      createBarChart('chart-location', labels, counts, 'Jobs');
    }

    // Jobs by Company (bar chart)
    if (data.jobs_per_company && data.jobs_per_company.length > 0) {
      const labels = data.jobs_per_company.map(item => item.company || 'Unknown');
      const counts = data.jobs_per_company.map(item => item.count);
      createBarChart('chart-company', labels, counts, 'Jobs');
    }

    // Internships vs Full-Time (doughnut chart)
    if (data.internship_vs_fulltime) {
      const labels = ['Internships', 'Full-Time'];
      const counts = [
        data.internship_vs_fulltime.internship_count || 0,
        data.internship_vs_fulltime.fulltime_count || 0,
      ];
      createDoughnutChart('chart-internship', labels, counts);
    }

    // Research vs Industry (doughnut chart)
    if (data.research_vs_industry) {
      const labels = ['Research', 'Industry'];
      const counts = [
        data.research_vs_industry.research_count || 0,
        data.research_vs_industry.industry_count || 0,
      ];
      createDoughnutChart('chart-research', labels, counts);
    }

    // Jobs by Collection (bar chart)
    if (data.jobs_per_collection && data.jobs_per_collection.length > 0) {
      const labels = data.jobs_per_collection.map(item => item.name || 'Unknown');
      const counts = data.jobs_per_collection.map(item => item.job_count);
      createBarChart('chart-collection', labels, counts, 'Jobs');
    }
  }

  /**
   * Fetch analytics data from the API and render charts.
   */
  async function loadAnalytics() {
    showState('loading');

    const result = await window.JobCopilotAPI.getAnalytics();

    if (!result.ok) {
      showState('error');
      return;
    }

    renderCharts(result.data);
    showState('charts');
  }

  // --- Event listeners ---
  retryBtn.addEventListener('click', loadAnalytics);

  // --- Initialize on page load ---
  loadAnalytics();
})();
