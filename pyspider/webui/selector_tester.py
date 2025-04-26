#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-27 14:00:00

import json
import logging
import traceback
from flask import render_template, request, jsonify

from pyspider.libs.response import Response
from pyspider.libs.advanced_selector import AdvancedSelector
from pyspider.libs.json_selector import JsonSelector
from pyspider.libs.css4_selector import CSS4Selector
from pyspider.libs.graphql_selector import GraphQLSelector
from pyspider.libs.xquery_selector import XQuerySelector
from pyspider.libs.selector_pipeline import SelectorPipeline
from pyspider.libs.selector_error_handler import SelectorErrorHandler, SelectorError

from .app import app

logger = logging.getLogger('selector_tester')

@app.route('/selector_tester')
def selector_tester():
    """Selector tester page"""
    return render_template('selector_tester.html')

@app.route('/api/test_selector', methods=['POST'])
def test_selector():
    """Test a selector on content"""
    try:
        data = request.json
        selector_type = data.get('selector_type', 'css')
        selector = data.get('selector', '')
        attribute = data.get('attribute')
        url = data.get('url', '')
        transformers = data.get('transformers', [])

        # Get content from session or fetch from URL
        content = None
        content_type = None

        if url:
            # Fetch content from URL
            import requests
            try:
                response = requests.get(url, timeout=10)
                content = response.text
                content_type = 'html' if 'html' in response.headers.get('Content-Type', '').lower() else 'json'
            except Exception as e:
                return jsonify({
                    'error': f"Error fetching URL: {str(e)}",
                    'result': None
                })
        else:
            # Use content from session
            content = request.cookies.get('content')
            content_type = request.cookies.get('content_type', 'html')

        if not content:
            return jsonify({
                'error': "No content available. Please load a URL first.",
                'result': None
            })

        # Create response object
        response_obj = Response(content=content, url=url)

        # Create error handler
        error_handler = SelectorErrorHandler(response_obj)

        # Test selector
        result = None
        error = None
        suggestions = []
        fixed_selector = None
        fixed_selector_type = None
        matched_elements = []

        try:
            # Apply selector based on type
            if selector_type == 'css':
                if attribute:
                    result = response_obj.css(selector, attribute)
                else:
                    result = response_obj.css(selector)
            elif selector_type == 'xpath':
                result = response_obj.xpath(selector)
            elif selector_type == 'css4':
                if attribute:
                    result = response_obj.css4(selector, attribute)
                else:
                    result = response_obj.css4(selector)
            elif selector_type == 'regex':
                result = response_obj.regex(selector)
            elif selector_type == 'jsonpath':
                result = response_obj.jsonpath(selector)
            elif selector_type == 'jmespath':
                result = response_obj.jmespath(selector)
            elif selector_type == 'graphql':
                graphql_selector = GraphQLSelector(response=response_obj)
                result = graphql_selector.query(selector)
            elif selector_type == 'xquery':
                xquery_selector = XQuerySelector(response=response_obj)
                result = xquery_selector.xquery(selector)
            else:
                return jsonify({
                    'error': f"Unknown selector type: {selector_type}",
                    'result': None
                })

            # Apply transformers
            if transformers and result is not None:
                pipeline = SelectorPipeline(response_obj)

                # Convert transformers format
                transformed_transformers = []
                for transformer in transformers:
                    name = transformer.get('name')
                    params = transformer.get('params', {})

                    args = []
                    kwargs = {}

                    # Convert params to args and kwargs
                    for param_name, param_value in params.items():
                        if param_name.startswith('param'):
                            args.append(param_value)
                        else:
                            kwargs[param_name] = param_value

                    transformed_transformers.append({
                        'name': name,
                        'args': args,
                        'kwargs': kwargs
                    })

                result = pipeline.apply_transformers(result, transformed_transformers)
        except Exception as e:
            # Handle error
            selector_error = error_handler.handle_error(e, selector, selector_type)
            error = str(selector_error)
            suggestions = selector_error.suggestions

            # Get auto-fixed selector
            fixed_selector, fixed_selector_type = error_handler.auto_fix_selector(selector, selector_type)

            # Log error
            logger.error(f"Error testing selector: {error}")
            logger.error(traceback.format_exc())

        # Return result
        return jsonify({
            'result': result,
            'content': content,
            'content_type': content_type,
            'error': error,
            'suggestions': suggestions,
            'fixed_selector': fixed_selector if fixed_selector != selector else None,
            'fixed_selector_type': fixed_selector_type if fixed_selector_type != selector_type else None,
            'matched_elements': matched_elements
        })
    except Exception as e:
        logger.error(f"Error in test_selector: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': f"Internal server error: {str(e)}",
            'result': None
        })

@app.route('/api/load_url', methods=['POST'])
def load_url():
    """Load content from a URL"""
    try:
        data = request.json
        url = data.get('url', '')

        if not url:
            return jsonify({
                'error': "URL is required",
                'content': None,
                'content_type': None
            })

        # Fetch content from URL
        import requests
        try:
            response = requests.get(url, timeout=10)
            content = response.text

            # Determine content type
            content_type = 'html'
            if 'application/json' in response.headers.get('Content-Type', '').lower():
                content_type = 'json'
                # Try to parse JSON
                try:
                    json_content = json.loads(content)
                    content = json.dumps(json_content, indent=2)
                except:
                    pass

            # Store content in session
            resp = jsonify({
                'content': content,
                'content_type': content_type,
                'error': None
            })
            resp.set_cookie('content', content)
            resp.set_cookie('content_type', content_type)
            return resp
        except Exception as e:
            return jsonify({
                'error': f"Error fetching URL: {str(e)}",
                'content': None,
                'content_type': None
            })
    except Exception as e:
        logger.error(f"Error in load_url: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': f"Internal server error: {str(e)}",
            'content': None,
            'content_type': None
        })
