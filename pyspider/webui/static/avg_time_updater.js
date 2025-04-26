/**
 * AVG TIME Updater
 *
 * This script handles updating the AVG TIME column in the projects table.
 * It works independently of Vue.js and DataTables to ensure reliable updates.
 */

// Function to update AVG TIME for all projects
function updateAvgTime() {
  console.log('Updating AVG TIME for all projects (direct approach)');

  // Get the latest time data from the specialized API endpoint
  $.get("/api/avg_time", function(data) {
    console.log('AVG TIME data received:', data);

    // Loop through all projects in the data
    for (let projectName in data) {
      const timeData = data[projectName];
      if (!timeData) {
        console.log('No time data for project:', projectName);
        continue;
      }

      // Get time values
      const fetchTime = timeData.fetch_time || 0;
      const processTime = timeData.process_time || 0;
      const totalTime = timeData.total_time || (fetchTime + processTime);
      const remainingTime = timeData.remaining_time || 0;
      const taskCounts = timeData.task_counts || { total: 0, success: 0, failed: 0, pending: 0 };

      console.log('Time data for', projectName, ':', {
        fetchTime, processTime, totalTime, remainingTime, taskCounts
      });

      // Find all cells with the project name (both original and DataTables generated)
      updateProjectRow(projectName, totalTime, remainingTime, taskCounts);
    }
  });
}

// Function to update a specific project row
function updateProjectRow(projectName, totalTime, remainingTime, taskCounts) {
  // Format the time values in seconds
  const totalTimeSeconds = totalTime.toFixed(3);

  // Format remaining time in seconds
  let remainingTimeText = '';
  if (remainingTime > 0) {
    // Always display in seconds
    remainingTimeText = `残り ${remainingTime.toFixed(0)}秒`;
  }

  // Combine time text
  const timeText = remainingTimeText ?
    `${totalTimeSeconds}s (${remainingTimeText})` :
    `${totalTimeSeconds}s`;

  // Calculate progress percentage (1 second = 100%)
  const progressPercent = Math.min(totalTime * 100, 100);

  console.log(`Updating ${projectName} with time ${timeText} (${progressPercent}%)`);

  // Find all rows with this project name
  const rows = document.querySelectorAll(`tr[data-name="${projectName}"]`);
  console.log(`Found ${rows.length} rows for project ${projectName}`);

  // Update each row
  rows.forEach(function(row) {
    // Find the time cell
    const timeCell = row.querySelector('.project-time-new');
    if (!timeCell) {
      console.log('Time cell not found for project row:', projectName);
      return;
    }

    // Update data-value attribute
    timeCell.setAttribute('data-value', totalTime);

    // Update text content
    const timeValueElement = timeCell.querySelector('.avg-time-value');
    if (timeValueElement) {
      timeValueElement.textContent = timeText;

      // Change color based on task status
      if (taskCounts.pending === 0 && (taskCounts.total > 0 && taskCounts.success > 0)) {
        // All tasks completed successfully (green)
        timeValueElement.classList.add('text-success');
        timeValueElement.classList.remove('text-warning', 'text-danger');
      } else if (taskCounts.pending > 0) {
        // Tasks still pending (default color)
        timeValueElement.classList.remove('text-success', 'text-warning', 'text-danger');
      } else if (taskCounts.failed > 0) {
        // Some tasks failed (red)
        timeValueElement.classList.add('text-danger');
        timeValueElement.classList.remove('text-success', 'text-warning');
      }
    }

    // Update progress bar width and color
    const progressBar = timeCell.querySelector('.progress-time');
    if (progressBar) {
      progressBar.style.width = progressPercent + '%';

      // Change progress bar color based on task status
      if (taskCounts.pending === 0 && (taskCounts.total > 0 && taskCounts.success > 0)) {
        // All tasks completed successfully (green)
        progressBar.classList.add('progress-bar-success');
        progressBar.classList.remove('progress-bar-info', 'progress-bar-warning', 'progress-bar-danger');
      } else if (taskCounts.pending > 0) {
        // Tasks still pending (blue - default)
        progressBar.classList.add('progress-bar-info');
        progressBar.classList.remove('progress-bar-success', 'progress-bar-warning', 'progress-bar-danger');
      } else if (taskCounts.failed > 0) {
        // Some tasks failed (red)
        progressBar.classList.add('progress-bar-danger');
        progressBar.classList.remove('progress-bar-success', 'progress-bar-info', 'progress-bar-warning');
      }
    }

    console.log('Updated AVG TIME for', projectName);
  });
}

// Set up periodic updates (every 5 seconds)
$(document).ready(function() {
  console.log('AVG TIME updater initialized');

  // Initial update
  setTimeout(updateAvgTime, 1000);

  // Periodic updates
  setInterval(updateAvgTime, 5000);

  // Update when DataTables redraws
  $(document).on('draw.dt', function() {
    console.log('DataTables draw event detected, updating AVG TIME');
    setTimeout(updateAvgTime, 100);
  });
});
