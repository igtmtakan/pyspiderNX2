// Fix for Run and Save buttons
$(document).ready(function() {
  // Fix Run button
  $('#run-task-btn').off('click').on('click', function() {
    console.log('Run button clicked');
    if (window.Debugger && typeof window.Debugger.run === 'function') {
      window.Debugger.run();
    } else {
      console.error('Debugger.run is not available');
    }
  });

  // Fix Save button
  $('#save-task-btn').off('click').on('click', function() {
    console.log('Save button clicked');
    if (window.Debugger && typeof window.Debugger.save === 'function') {
      window.Debugger.save();
    } else {
      // Fallback implementation
      var script = window.Debugger.python_editor.getDoc().getValue();
      $('#right-area .overlay').show();
      $.ajax({
        type: "POST",
        url: location.pathname+'/save',
        data: {
          script: script
        },
        success: function(data) {
          console.log(data);
          window.Debugger.python_log('');
          window.Debugger.python_log("saved!");
          window.Debugger.not_saved = false;
          $('#right-area .overlay').hide();
        },
        error: function(xhr, textStatus, errorThrown) {
          console.log(xhr, textStatus, errorThrown);
          window.Debugger.python_log("save error!\n"+xhr.responseText);
          $('#right-area .overlay').hide();
        }
      });
    }
  });

  // Override newtask_template
  window.Debugger.newtask_template = '<div class="newtask" data-task="__task__"><span class="task-callback">__callback__</span> &gt; <span class="task-url">__url__</span><div class="task-run btn btn-sm btn-outline-success"><i class="bi bi-play-fill"></i> Run</div><div class="task-more btn btn-sm btn-outline-secondary"> <i class="bi bi-three-dots"></i> </div></div>';

  // Override bind_follows
  var originalBindFollows = window.Debugger.bind_follows;
  window.Debugger.bind_follows = function() {
    if (originalBindFollows) {
      originalBindFollows.call(window.Debugger);
    }

    $('.newtask .task-run').off('click').on('click', function(event) {
      event.preventDefault();
      event.stopPropagation();
      let task_id = $(this).parents('.newtask').data("task");
      let task = window.newtasks[task_id];
      window.Debugger.task_editor.setValue(JSON.stringify(task, null, '  '));
      window.Debugger.task_updated(task);
      window.Debugger.run();
    });

    $('.newtask .task-more').off('click').on('click', function(event) {
      event.preventDefault();
      event.stopPropagation();
      let $newtask = $(this).parents('.newtask');
      if ($newtask.next().hasClass("task-show")) {
        $newtask.next().remove();
        return;
      }
      let task = $newtask.after('<div class="task-show"><pre class="cm-s-default"></pre></div>').data("task");
      task = JSON.stringify(window.newtasks[task], null, '  ');
      CodeMirror.runMode(task, 'application/json', $newtask.next().find('pre')[0]);
    });
  };
});
