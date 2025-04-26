// Vue.js 3 version of index.js
// Author: Augment Agent
// Created on 2024-04-18

// Main Vue application
document.addEventListener('DOMContentLoaded', function() {
  console.log('DOM Content Loaded');

  // Vue.js 3 global object check
  if (typeof window.Vue === 'undefined') {
    console.error('Vue is not defined. Make sure Vue.js 3 is loaded correctly.');
    return;
  }
  console.log('Vue version:', window.Vue.version);

  // Create Vue app
  const app = window.Vue.createApp({
    data() {
      // Initialize projects with default values
      const projects = window.projects || [];

      // Ensure all projects have the required properties
      projects.forEach(project => {
        // Initialize time property if not exists
        if (!project.time) {
          project.time = { fetch_time: 0, process_time: 0 };
        }

        // Initialize progress property if not exists
        if (!project.progress) {
          project.progress = {
            '5m': { pending: 0, success: 0, retry: 0, failed: 0, task: 0, title: '' },
            '1h': { pending: 0, success: 0, retry: 0, failed: 0, task: 0, title: '' },
            '1d': { pending: 0, success: 0, retry: 0, failed: 0, task: 0, title: '' },
            'all': { pending: 0, success: 0, retry: 0, failed: 0, task: 0, title: '' }
          };
        }
      });

      return {
        projects: projects
      };
    },

    mounted() {
      // Initialize editable fields
      this.initEditable();

      // Sortable.js has been removed

      // Start counter updates
      this.updateCounter();

      // Setup project creation form
      this.setupProjectForm();

      // Bind run button click events using jQuery
      this.bindRunButtons();
    },
    methods: {
      project_run(project, event) {
        console.log('Run button clicked for project:', project.name);
        console.log('Event:', event);
        console.log('Project status:', project.status);

        // Ensure we have the correct button element
        var $this = $(event.target);
        if (!$this.hasClass('project-run')) {
          $this = $this.closest('.project-run');
        }
        console.log('Button element:', $this[0]);

        $this.addClass('btn-warning');

        // Note: Status check is now done on the server side

        console.log('Sending AJAX request for project:', project.name);

        // Use AJAX to send the request
        $.ajax({
          type: 'POST',
          url: '/run',
          data: {
            project: project.name,
            webdav_mode: 'false'
          },
          success: function(data) {
            console.log('Run request successful:', data);
            $this.removeClass('btn-warning').addClass('btn-success');
            setTimeout(function() {
              $this.removeClass('btn-success');
            }, 1000);

            // Redirect to the result page
            window.location.href = '/run_result?project=' + encodeURIComponent(project.name) + '&result=true';
          },
          error: function(xhr, status, error) {
            console.error('Run request failed:', status, error);
            $this.removeClass('btn-warning').addClass('btn-danger');
            setTimeout(function() {
              $this.removeClass('btn-danger');
            }, 1000);

            // Redirect to the result page with error
            window.location.href = '/run_result?project=' + encodeURIComponent(project.name) + '&result=false&error=' + encodeURIComponent(error || 'Unknown error');
          }
        });
      },

      initEditable() {
        // Initialize x-editable for project fields
        $.fn.editable.defaults.mode = 'popup';

        $(".project-group>span").editable({
          name: "group",
          pk: function() {
            return $(this).parents("tr").data("name");
          },
          emptytext: "[group]",
          placement: "right",
          url: "/update",
          params: function(params) {
            // Convert params to the format expected by the server
            return {
              pk: params.pk,
              name: params.name,
              value: params.value
            };
          },
          success: function(response, newValue) {
            try {
              const projectName = $(this).parents("tr").data("name");
              if (app && app.projects && app.projects[projectName]) {
                app.projects[projectName].group = newValue;
              }
              $(this).attr("style", "");

              // Ensure the spinner is hidden
              $(this).closest('.editable-container').find('.editableform-loading').hide();
              $(this).closest('.editable-container').find('.editable-submit').removeClass('disabled');
              $(this).closest('.editable-container').find('.editable-cancel').removeClass('disabled');
            } catch (e) {
              console.error('Error in group update success callback:', e);
            }
          },
          error: function(response, newValue) {
            console.error('Group update error:', response);
            // Handle error and ensure the spinner is hidden
            $(this).closest('.editable-container').find('.editableform-loading').hide();
            $(this).closest('.editable-container').find('.editable-submit').removeClass('disabled');
            $(this).closest('.editable-container').find('.editable-cancel').removeClass('disabled');
            return 'Error updating group. Please try again.';
          }
        });

        $(".project-status>span").editable({
          type: "select",
          name: "status",
          source: [
            {value: "TODO", text: "TODO"},
            {value: "STOP", text: "STOP"},
            {value: "CHECKING", text: "CHECKING"},
            {value: "DEBUG", text: "DEBUG"},
            {value: "RUNNING", text: "RUNNING"}
          ],
          pk: function() {
            return $(this).parents("tr").data("name");
          },
          emptytext: "[status]",
          placement: "right",
          url: "/update",
          params: function(params) {
            // Convert params to the format expected by the server
            return {
              pk: params.pk,
              name: params.name,
              value: params.value
            };
          },
          success: function(response, newValue) {
            try {
              const projectName = $(this).parents("tr").data("name");
              if (app && app.projects && app.projects[projectName]) {
                app.projects[projectName].status = newValue;
              }
              $(this)
                .removeClass("status-" + $(this).attr("data-value"))
                .addClass("status-" + newValue)
                .attr("data-value", newValue)
                .attr("style", "");

              // Ensure the spinner is hidden
              $(this).closest('.editable-container').find('.editableform-loading').hide();
              $(this).closest('.editable-container').find('.editable-submit').removeClass('disabled');
              $(this).closest('.editable-container').find('.editable-cancel').removeClass('disabled');
            } catch (e) {
              console.error('Error in status update success callback:', e);
            }
          },
          error: function(response, newValue) {
            console.error('Status update error:', response);
            // Handle error and ensure the spinner is hidden
            $(this).closest('.editable-container').find('.editableform-loading').hide();
            $(this).closest('.editable-container').find('.editable-submit').removeClass('disabled');
            $(this).closest('.editable-container').find('.editable-cancel').removeClass('disabled');
            return 'Error updating status. Please try again.';
          }
        });

        $(".project-rate>span").editable({
          name: "rate",
          pk: function() {
            return $(this).parents("tr").data("name");
          },
          validate: function(value) {
            var parts = value.split("/");
            if (parts.length != 2) {
              return "format error: rate/burst";
            }
            if (!$.isNumeric(parts[0]) || !$.isNumeric(parts[1])) {
              return "format error: rate/burst";
            }
          },
          highlight: false,
          emptytext: "0/0",
          placement: "right",
          url: "/update",
          params: function(params) {
            // Convert params to the format expected by the server
            return {
              pk: params.pk,
              name: params.name,
              value: params.value
            };
          },
          success: function(response, newValue) {
            try {
              const projectName = $(this).parents("tr").data("name");
              if (app && app.projects && app.projects[projectName]) {
                const parts = newValue.split("/");
                app.projects[projectName].rate = parseFloat(parts[0]);
                app.projects[projectName].burst = parseFloat(parts[1]);
              }
              $(this).attr("style", "");

              // Ensure the spinner is hidden
              $(this).closest('.editable-container').find('.editableform-loading').hide();
              $(this).closest('.editable-container').find('.editable-submit').removeClass('disabled');
              $(this).closest('.editable-container').find('.editable-cancel').removeClass('disabled');
            } catch (e) {
              console.error('Error in rate update success callback:', e);
            }
          },
          error: function(response, newValue) {
            console.error('Rate update error:', response);
            // Handle error and ensure the spinner is hidden
            $(this).closest('.editable-container').find('.editableform-loading').hide();
            $(this).closest('.editable-container').find('.editable-submit').removeClass('disabled');
            $(this).closest('.editable-container').find('.editable-cancel').removeClass('disabled');
            return 'Error updating rate. Please try again.';
          }
        });
      },

      // initSortable method has been removed

      updateCounter() {
        const updateCounters = () => {
          // Update project counters
          $.get("/counter", (data) => {
            console.log('Counter data received:', data);

            // Direct DOM manipulation for progress bars
            for (let project in data) {
              const counter = data[project];
              console.log('Project:', project, 'Counter:', counter);

              // Find the project row by data-id or data-name
              console.log('Looking for project row with data-id or data-name:', project);
              console.log('All project rows:', $('.project').length);
              $('.project').each(function() {
                console.log('Project row:', $(this).attr('data-id') || $(this).attr('data-name'), $(this));
              });
              let $projectRow = $(`.project[data-id="${project}"]`);
              if ($projectRow.length === 0) {
                $projectRow = $(`.project[data-name="${project}"]`);
              }
              console.log('Found project row:', $projectRow.length, $projectRow[0]);
              if ($projectRow.length === 0) {
                console.log('Project row not found in DOM:', project);
                continue;
              }

              // Update progress bars for each type
              const types = "5m,1h,1d,all".split(",");
              for (let i = 0; i < types.length; i++) {
                const type = types[i];
                if (!counter[type]) {
                  console.log('No counter data for type:', type);
                  continue;
                }

                // Find the progress cell
                const $progressCell = $projectRow.find(`.progress-${type}`);
                console.log('Progress cell for', type, ':', $progressCell.length, $progressCell[0]);
                if ($progressCell.length === 0) {
                  console.log('Progress cell not found for type:', type);
                  continue;
                }

                // Get counter data
                const pending = counter[type].pending || 0;
                const success = counter[type].success || 0;
                const retry = counter[type].retry || 0;
                const failed = counter[type].failed || 0;
                const task = counter[type].task || (pending + success + retry + failed);
                const title = counter[type].title || `pending: ${pending}, success: ${success}, retry: ${retry}, failed: ${failed}`;

                console.log('Counter data for', project, type, ':', {
                  pending, success, retry, failed, task, title
                });

                // Update data attributes
                $progressCell.attr('data-value', task);
                $progressCell.attr('title', title);

                // Update progress text
                $progressCell.find('.progress-text').html(`${type}${task > 0 ? ': ' + task : ''}`);

                // Calculate percentages
                const pendingPercent = task > 0 ? (pending / task * 100) : 0;
                const successPercent = task > 0 ? (success / task * 100) : 0;
                const retryPercent = task > 0 ? (retry / task * 100) : 0;
                const failedPercent = task > 0 ? (failed / task * 100) : 0;

                console.log('Calculated percentages for', project, type, ':', {
                  pending: pendingPercent + '%',
                  success: successPercent + '%',
                  retry: retryPercent + '%',
                  failed: failedPercent + '%'
                });

                // Update progress bars
                $progressCell.find('.progress-pending').css('width', pendingPercent + '%');
                $progressCell.find('.progress-success').css('width', successPercent + '%');
                $progressCell.find('.progress-retry').css('width', retryPercent + '%');
                $progressCell.find('.progress-failed').css('width', failedPercent + '%');

                console.log('Updated progress bars for', project, type);
              }

              // Avg time is updated separately in updateAvgTime method
            }
          });

          // Update avg time
          this.updateAvgTime();

          // Update queue information
          $.get("/queues", (data) => {
            for (let key in data) {
              $(".queue_value[title=\"" + key + "\"]").text(data[key]);
            }
          });

          // Schedule the next update
          setTimeout(updateCounters, 2000);
        };

        // Start the update loop
        updateCounters();
      },

      setupProjectForm() {
        // Project creation form validation
        $(".project-create").on('click', function() {
          $("#create-project-modal").find(".has-error").removeClass("has-error");
          $("#create-project-modal").find(".help-block").hide();
        });

        $("#create-project-modal form").on('submit', function(ev) {
          var project_name = $(this).find("input[name=project-name]");
          if (project_name.val().search(/[^\w]/) != -1) {
            project_name.parents(".form-group").addClass("has-error");
            project_name.next(".help-block").show();
            ev.preventDefault();
            return false;
          }
          return true;
        });
      },

      bindRunButtons() {
        // No longer needed as we're using direct form submission
        // This method is kept for compatibility
        console.log('bindRunButtons: Using direct form submission instead of jQuery binding');
      },

      updateAvgTime() {
        console.log('Updating avg time for all projects');

        // Loop through all projects
        for (let projectName in this.projects) {
          const project = this.projects[projectName];
          if (!project.time) {
            console.log('No time data for project:', projectName);
            continue;
          }

          // Find the project row
          const $projectRow = $(`.project[data-name="${projectName}"]`);
          if ($projectRow.length === 0) {
            console.log('Project row not found for avg time update:', projectName);
            continue;
          }

          // Find the time cell
          const $timeCell = $projectRow.find('.project-time');
          if ($timeCell.length === 0) {
            console.log('Time cell not found for project:', projectName);
            continue;
          }

          // Get time data
          const fetchTime = project.time.fetch_time || 0;
          const processTime = project.time.process_time || 0;
          const totalTime = fetchTime + processTime;

          console.log('Time data for', projectName, ':', {
            fetchTime, processTime, totalTime
          });

          // Update data-value attribute
          $timeCell.attr('data-value', totalTime);

          // Update text content directly
          // Format: fetch_time+process_time (in milliseconds)
          const fetchTimeMs = (fetchTime * 1000).toFixed(1);
          const processTimeMs = (processTime * 1000).toFixed(2);
          const timeText = `${fetchTimeMs}+${processTimeMs}`;
          console.log('Setting time text to:', timeText);
          $timeCell.find('.avg-time-value').text(timeText);

          console.log('Updated avg time for', projectName);
        }
      }
    }
  });

  // Mount the app to the body element to include header and section
  app.mount('body');
});
