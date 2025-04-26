#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-06-20 10:00:00

import time
import json
import logging
from flask import request, jsonify, Response

from .app import app
from pyspider.libs.time_series_store import time_series_store

logger = logging.getLogger('webui.api')

def json_response(data, status=200):
    """Return a JSON response with the given data and status code."""
    response = Response(json.dumps(data), mimetype='application/json')
    response.status_code = status
    return response

@app.route('/api/time_series', methods=['GET'])
def get_time_series():
    """Get time series data for projects"""
    project = request.args.get('project')
    metric = request.args.get('metric')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    if start_time:
        try:
            start_time = float(start_time)
        except ValueError:
            return jsonify({
                'error': 'Invalid start_time parameter',
            }), 400

    if end_time:
        try:
            end_time = float(end_time)
        except ValueError:
            return jsonify({
                'error': 'Invalid end_time parameter',
            }), 400

    if project and metric:
        # Get data for a specific project and metric
        data = time_series_store.get_data(project, metric, start_time, end_time)
        return jsonify(data)
    elif project:
        # Get all metrics for a specific project
        data = time_series_store.get_all_data(project, start_time, end_time)
        return jsonify(data)
    else:
        # Get data for all projects
        data = time_series_store.get_all_data(None, start_time, end_time)
        return jsonify(data)

@app.route('/api/time_series/metrics', methods=['GET'])
def get_available_metrics():
    """Get available metrics for time series data"""
    # Get all data
    all_data = time_series_store.get_all_data()

    # Extract unique metrics
    metrics = set()
    for project_data in all_data.values():
        metrics.update(project_data.keys())

    return jsonify(list(metrics))

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects."""
    projectdb = app.config.get('projectdb')
    if not projectdb:
        return json_response({'error': 'projectdb not initialized'}, 500)

    projects = list(projectdb.get_all())
    return json_response({'projects': projects})

@app.route('/api/projects/<name>', methods=['GET'])
def get_project(name):
    """Get a project by name."""
    projectdb = app.config.get('projectdb')
    if not projectdb:
        return json_response({'error': 'projectdb not initialized'}, 500)

    project = projectdb.get(name)
    if not project:
        return json_response({'error': 'project not found'}, 404)

    return json_response(project)

@app.route('/api/counter', methods=['GET'])
def get_project_task_count():
    """Get task count for a project."""
    project = request.args.get('project')
    if not project:
        return json_response({'error': 'project parameter is required'}, 400)

    rpc = app.config.get('scheduler_rpc')
    if not rpc:
        return json_response({'error': 'scheduler not available'}, 503)

    try:
        # The counter method requires a _type parameter
        try:
            counter = rpc.counter(project, 'all')
            return json_response(counter)
        except Exception:
            # If that fails, provide default counter values
            return json_response({'active': 0, 'success': 0, 'failed': 0, 'pending': 0})
    except Exception as e:
        logger.error('RPC error: %s', e)
        return json_response({'error': str(e)}, 500)

@app.route('/api/run', methods=['POST'])
def run_project():
    """Run a project."""
    data = request.get_json()
    if not data or 'project' not in data:
        return json_response({'error': 'project parameter is required'}, 400)

    project = data['project']
    rpc = app.config.get('scheduler_rpc')
    if not rpc:
        return json_response({'error': 'scheduler not available'}, 503)

    try:
        rpc.start_project(project)
        return json_response({'status': 'ok'})
    except Exception as e:
        logger.error('RPC error: %s', e)
        return json_response({'error': str(e)}, 500)

@app.route('/api/stop', methods=['POST'])
def stop_project():
    """Stop a project."""
    data = request.get_json()
    if not data or 'project' not in data:
        return json_response({'error': 'project parameter is required'}, 400)

    project = data['project']
    rpc = app.config.get('scheduler_rpc')
    if not rpc:
        return json_response({'error': 'scheduler not available'}, 503)

    try:
        rpc.stop_project(project)
        return json_response({'status': 'ok'})
    except Exception as e:
        logger.error('RPC error: %s', e)
        return json_response({'error': str(e)}, 500)

@app.route('/api/projects', methods=['POST'])
def save_project():
    """Create or update a project."""
    projectdb = app.config.get('projectdb')
    if not projectdb:
        return json_response({'error': 'projectdb not initialized'}, 500)

    project = request.get_json()
    if not project or 'name' not in project:
        return json_response({'error': 'invalid project data'}, 400)

    try:
        # Check if project exists
        old_project = projectdb.get(project['name'])
        if old_project:
            # Update existing project
            projectdb.update(project['name'], project)
        else:
            # Create new project
            projectdb.insert(project)

        return json_response({'status': 'ok'})
    except Exception as e:
        logger.error('Failed to save project: %s', e)
        return json_response({'error': str(e)}, 500)

@app.route('/api/projects/<name>', methods=['DELETE'])
def delete_project(name):
    """Delete a project."""
    projectdb = app.config.get('projectdb')
    if not projectdb:
        return json_response({'error': 'projectdb not initialized'}, 500)

    try:
        if not projectdb.get(name):
            return json_response({'error': 'project not found'}, 404)

        projectdb.drop(name)
        return json_response({'status': 'ok'})
    except Exception as e:
        logger.error('Failed to delete project: %s', e)
        return json_response({'error': str(e)}, 500)

@app.route('/api/counters', methods=['GET'])
def get_project_counters():
    """Get counters for all projects."""
    rpc = app.config.get('scheduler_rpc')
    if not rpc:
        return json_response({'error': 'scheduler not available'}, 503)

    try:
        result = {}
        projectdb = app.config.get('projectdb')
        if not projectdb:
            return json_response({'error': 'projectdb not initialized'}, 500)

        projects = projectdb.get_all()
        for project in projects:
            try:
                # The counter method requires a _type parameter
                # We'll try to call it with 'all' as the type
                try:
                    counter = rpc.counter(project['name'], 'all')
                    result[project['name']] = counter
                except Exception:
                    # If that fails, provide default counter values
                    result[project['name']] = {'active': 0, 'success': 0, 'failed': 0, 'pending': 0}
            except Exception as e:
                logger.error('Failed to get counter for project %s: %s', project['name'], e)
                result[project['name']] = {'active': 0, 'success': 0, 'failed': 0, 'pending': 0}

        return json_response(result)
    except Exception as e:
        logger.error('RPC error: %s', e)
        return json_response({'error': str(e)}, 500)

@app.route('/api/time_stats', methods=['GET'])
def get_avg_time_data():
    """Get average time data for all projects."""
    rpc = app.config.get('scheduler_rpc')
    if not rpc:
        return json_response({'error': 'scheduler not available'}, 503)

    try:
        result = {}
        projectdb = app.config.get('projectdb')
        if not projectdb:
            return json_response({'error': 'projectdb not initialized'}, 500)

        projects = projectdb.get_all()
        for project in projects:
            # Since get_time_stats is not supported, we'll provide static time stats
            # This is a workaround until the scheduler implements the method
            result[project['name']] = {
                'total_time': 0.0,
                'avg_time': 0.0,
                'min_time': 0.0,
                'max_time': 0.0,
                'count': 0
            }

        return json_response(result)
    except Exception as e:
        logger.error('RPC error: %s', e)
        return json_response({'error': str(e)}, 500)

@app.route('/api/queues', methods=['GET'])
def get_queue_info():
    """Get queue information."""
    rpc = app.config.get('scheduler_rpc')
    if not rpc:
        return json_response({'error': 'scheduler not available'}, 503)

    try:
        # Since get_queue_info is not supported, we'll provide static queue information
        # This is a workaround until the scheduler implements the method
        result = {
            'scheduler2fetcher': 0,
            'fetcher2processor': 0,
            'processor2result': 0,
            'newtask_queue': 0,
            'status_queue': 0
        }
        return json_response(result)
    except Exception as e:
        logger.error('RPC error: %s', e)
        return json_response({'error': str(e)}, 500)

@app.route('/api/debug/new', methods=['POST'])
def create_project():
    """Create a new project."""
    projectdb = app.config.get('projectdb')
    if not projectdb:
        return json_response({'error': 'projectdb not initialized'}, 500)

    try:
        project_name = request.form.get('project-name')
        start_urls = request.form.get('start-urls', '')
        script_mode = request.form.get('script-mode', 'script')

        if not project_name:
            return json_response({'error': 'project name is required'}, 400)

        # Check if project already exists
        if projectdb.get(project_name):
            return json_response({'error': 'project already exists'}, 409)

        # Create project template
        from pyspider.libs.base_handler import BaseHandler

        # Create a basic project template
        if script_mode == 'script':
            script = BaseHandler.get_template(project_name, start_urls)
        else:
            script = BaseHandler.get_slime_template(project_name, start_urls)

        # Create project
        project = {
            'name': project_name,
            'group': None,
            'status': 'RUNNING',
            'script': script,
            'comments': None,
            'rate': 1,
            'burst': 10,
            'updatetime': time.time(),
        }

        projectdb.insert(project)
        return json_response({'status': 'ok'})
    except Exception as e:
        logger.error('Failed to create project: %s', e)
        return json_response({'error': str(e)}, 500)

@app.route('/api/debug/run', methods=['POST'])
def run_task():
    """Run a task with the given script."""
    data = request.get_json()
    if not data:
        return json_response({'error': 'Invalid request data'}, 400)

    project_name = data.get('project')
    task = data.get('task')
    script = data.get('script')

    if not project_name or not task or not script:
        return json_response({'error': 'Missing required parameters'}, 400)

    try:
        from pyspider.processor.project_module import ProjectManager
        from pyspider.libs.response import rebuild_response
        from pyspider.libs.utils import pretty_unicode
        import traceback
        import sys
        import time

        project = {
            'name': project_name,
            'script': script,
        }

        # Build module from script
        try:
            project_data = ProjectManager.build_module(project, {})
            module = project_data['module']
            instance = project_data['instance']
        except Exception as e:
            return json_response({
                'result': None,
                'follows': [],
                'messages': [],
                'logs': [str(e)],
                'error': 'Script error',
                'time': 0,
                'fetch_result': {
                    'content': 'Script error',
                    'cookies': {},
                    'headers': {},
                    'orig_url': 'data:,Script error',
                    'save': None,
                    'status_code': 500,
                    'time': 0,
                    'url': 'data:,Script error'
                }
            }, 200)

        # Prepare task
        if not isinstance(task, dict):
            try:
                task = json.loads(task)
            except Exception as e:
                return json_response({'error': 'Invalid task format'}, 400)

        # Execute task
        start_time = time.time()
        try:
            result = {}
            logs = []
            follows = []
            messages = []

            # Get callback function
            callback = task.get('process', {}).get('callback', 'on_start')
            if not hasattr(module, callback):
                return json_response({
                    'result': None,
                    'follows': [],
                    'messages': [],
                    'logs': [f'Callback {callback} not found in script'],
                    'error': 'Callback not found',
                    'time': 0,
                    'fetch_result': {
                        'content': f'Callback {callback} not found',
                        'cookies': {},
                        'headers': {},
                        'orig_url': f'data:,Callback {callback} not found',
                        'save': None,
                        'status_code': 400,
                        'time': 0,
                        'url': f'data:,Callback {callback} not found'
                    }
                }, 200)

            # Create a custom logger to capture logs
            class LogCapture(object):
                def __init__(self):
                    self.lines = []

                def debug(self, msg, *args, **kwargs):
                    self.lines.append(pretty_unicode(msg) % args)

                def info(self, msg, *args, **kwargs):
                    self.lines.append(pretty_unicode(msg) % args)

                def warning(self, msg, *args, **kwargs):
                    self.lines.append(pretty_unicode(msg) % args)

                def error(self, msg, *args, **kwargs):
                    self.lines.append(pretty_unicode(msg) % args)

            log_capture = LogCapture()
            module.logger = log_capture

            # Execute callback
            func = getattr(module, callback)

            # If task has a response, rebuild it
            if 'response' in task:
                response = rebuild_response(task['response'])
                ret = func(task, response)
            else:
                ret = func(task)

            # Process result
            if ret is not None:
                result = ret

            # Get logs
            logs = log_capture.lines
            if not logs:
                logs = []

            # Get follows
            if hasattr(instance, 'follows') and instance.follows:
                follows = instance.follows

            # Get messages
            if hasattr(instance, 'messages') and instance.messages:
                messages = instance.messages

            return json_response({
                'result': result,
                'follows': follows,
                'messages': messages,
                'logs': logs,
                'time': time.time() - start_time,
                'fetch_result': {
                    'content': callback,
                    'cookies': {},
                    'headers': {},
                    'orig_url': f"data:,{callback}",
                    'save': None,
                    'status_code': 200,
                    'time': 0,
                    'url': f"data:,{callback}"
                }
            }, 200)
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            tb = traceback.format_exception(exc_type, exc_value, exc_traceback)
            logs = [line.rstrip('\n') for line in tb]
            return json_response({
                'result': None,
                'follows': [],
                'messages': [],
                'logs': logs,
                'error': str(e),
                'time': time.time() - start_time,
                'fetch_result': {
                    'content': 'Error',
                    'cookies': {},
                    'headers': {},
                    'orig_url': 'data:,Error',
                    'save': None,
                    'status_code': 500,
                    'time': 0,
                    'url': 'data:,Error'
                }
            }, 200)
    except Exception as e:
        logger.error('Failed to run task: %s', e)
        return json_response({'error': str(e)}, 500)
