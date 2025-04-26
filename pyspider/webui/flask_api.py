#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-06-20 10:00:00

import time
import logging
from flask import Blueprint, request, jsonify

from pyspider.libs.time_series_store import time_series_store

logger = logging.getLogger('webui.api')

def create_app():
    """Create Flask API Blueprint"""
    api = Blueprint('api', __name__)

    @api.route('/time_series', methods=['GET'])
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

    @api.route('/time_series/metrics', methods=['GET'])
    def get_available_metrics():
        """Get available metrics for time series data"""
        # Get all data
        all_data = time_series_store.get_all_data()
        
        # Extract unique metrics
        metrics = set()
        for project_data in all_data.values():
            metrics.update(project_data.keys())
        
        return jsonify(list(metrics))
    
    return api
