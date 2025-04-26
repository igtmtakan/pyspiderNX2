#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-27 12:00:00

import re
import logging
import json
import datetime
from typing import List, Dict, Union, Optional, Any, Tuple, Callable, Dict

logger = logging.getLogger('selector_pipeline')

class SelectorPipeline:
    r"""
    A pipeline for processing selectors and transforming their results.
    
    The SelectorPipeline class provides a way to:
    1. Chain multiple selectors together
    2. Apply transformations to selector results
    3. Handle errors and provide fallbacks
    
    Example:
        >>> pipeline = SelectorPipeline()
        >>> result = pipeline.process([
        ...     {'type': 'css', 'selector': 'h1', 'attr': 'text'},
        ...     {'type': 'xpath', 'selector': '//p[\\W]', 'attr': 'text'}
        ... ])
    """
    def __init__(self):
        self.transformers = {}
        self.error_handler = SelectorErrorHandler()

    def _get_default_transformers(self) -> Dict[str, Callable]:
        """
        Get default transformer functions

        Returns:
            Dict of transformer functions
        """
        return {
            'strip': lambda x: x.strip() if isinstance(x, str) else x,
            'lower': lambda x: x.lower() if isinstance(x, str) else x,
            'upper': lambda x: x.upper() if isinstance(x, str) else x,
            'title': lambda x: x.title() if isinstance(x, str) else x,
            'capitalize': lambda x: x.capitalize() if isinstance(x, str) else x,
            'int': lambda x: int(x) if x and (isinstance(x, str) and x.strip().isdigit() or isinstance(x, (int, float))) else 0,
            'float': lambda x: float(x) if x and (isinstance(x, str) and re.match(r'^-?\d+(\.\d+)?$', x.strip()) or isinstance(x, (int, float))) else 0.0,
            'bool': lambda x: bool(x) if x is not None else False,
            'str': lambda x: str(x) if x is not None else '',
            'list': lambda x: list(x) if hasattr(x, '__iter__') and not isinstance(x, (str, dict)) else [x] if x is not None else [],
            'dict': lambda x: dict(x) if isinstance(x, dict) else {},
            'json': lambda x: json.loads(x) if isinstance(x, str) else x,
            'join': lambda x, sep=' ': sep.join(x) if isinstance(x, list) else x,
            'split': lambda x, sep=' ': x.split(sep) if isinstance(x, str) else x,
            'replace': lambda x, old, new: x.replace(old, new) if isinstance(x, str) else x,
            'regex_replace': lambda x, pattern, repl: re.sub(pattern, repl, x) if isinstance(x, str) else x,
            'regex_extract': lambda x, pattern, group=0: re.search(pattern, x).group(group) if isinstance(x, str) and re.search(pattern, x) else None,
            'length': lambda x: len(x) if hasattr(x, '__len__') else 0,
            'slice': lambda x, start, end=None: x[start:end] if hasattr(x, '__getitem__') else x,
            'first': lambda x: x[0] if hasattr(x, '__getitem__') and len(x) > 0 else None,
            'last': lambda x: x[-1] if hasattr(x, '__getitem__') and len(x) > 0 else None,
            'nth': lambda x, n: x[n] if hasattr(x, '__getitem__') and len(x) > n else None,
            'filter': lambda x, func: list(filter(func, x)) if hasattr(x, '__iter__') else x,
            'map': lambda x, func: list(map(func, x)) if hasattr(x, '__iter__') else x,
            'sort': lambda x, key=None, reverse=False: sorted(x, key=key, reverse=reverse) if hasattr(x, '__iter__') else x,
            'unique': lambda x: list(set(x)) if hasattr(x, '__iter__') else x,
            'flatten': lambda x: [item for sublist in x for item in sublist] if hasattr(x, '__iter__') and all(hasattr(i, '__iter__') for i in x) else x,
            'zip': lambda x, y: list(zip(x, y)) if hasattr(x, '__iter__') and hasattr(y, '__iter__') else x,
            'dict_from_list': lambda x, key, value: {i[key]: i[value] for i in x} if isinstance(x, list) else x,
            'get': lambda x, key, default=None: x.get(key, default) if isinstance(x, dict) else default,
            'keys': lambda x: list(x.keys()) if isinstance(x, dict) else x,
            'values': lambda x: list(x.values()) if isinstance(x, dict) else x,
            'items': lambda x: list(x.items()) if isinstance(x, dict) else x,
            'update': lambda x, y: x.update(y) or x if isinstance(x, dict) and isinstance(y, dict) else x,
            'merge': lambda x, y: {**x, **y} if isinstance(x, dict) and isinstance(y, dict) else x,
            'contains': lambda x, y: y in x if hasattr(x, '__contains__') else False,
            'starts_with': lambda x, y: x.startswith(y) if isinstance(x, str) else False,
            'ends_with': lambda x, y: x.endswith(y) if isinstance(x, str) else False,
            'format_date': lambda x, fmt='%Y-%m-%d': datetime.datetime.strptime(x, fmt).date() if isinstance(x, str) else x,
            'format_datetime': lambda x, fmt='%Y-%m-%d %H:%M:%S': datetime.datetime.strptime(x, fmt) if isinstance(x, str) else x,
            'date_to_string': lambda x, fmt='%Y-%m-%d': x.strftime(fmt) if isinstance(x, (datetime.date, datetime.datetime)) else x,
            'now': lambda: datetime.datetime.now(),
            'today': lambda: datetime.date.today(),
            'timestamp': lambda x: x.timestamp() if isinstance(x, datetime.datetime) else x,
            'from_timestamp': lambda x: datetime.datetime.fromtimestamp(x) if isinstance(x, (int, float)) else x,
            'default': lambda x, default: x if x is not None else default,
            'if_none': lambda x, default: default if x is None else x,
            'if_empty': lambda x, default: default if not x else x,
            'if_true': lambda x, value: value if x else None,
            'if_false': lambda x, value: value if not x else None,
            'if_equals': lambda x, y, value: value if x == y else None,
            'if_not_equals': lambda x, y, value: value if x != y else None,
            'if_contains': lambda x, y, value: value if y in x else None,
            'if_not_contains': lambda x, y, value: value if y not in x else None,
            'if_matches': lambda x, pattern, value: value if re.search(pattern, x) else None,
            'if_not_matches': lambda x, pattern, value: value if not re.search(pattern, x) else None,
        }

    def register_transformer(self, name: str, func: Callable):
        """
        Register a custom transformer function

        Args:
            name: Transformer name
            func: Transformer function
        """
        self._transformers[name] = func

    def register_transformers(self, transformers: Dict[str, Callable]):
        """
        Register multiple custom transformer functions

        Args:
            transformers: Dictionary of transformer functions
        """
        for name, func in transformers.items():
            self.register_transformer(name, func)

    def load_transformer_module(self, module_path: str) -> bool:
        """
        Load transformer functions from a Python module

        Args:
            module_path: Path to the module

        Returns:
            True if successful, False otherwise
        """
        try:
            import importlib.util
            import inspect

            # Load module from path
            spec = importlib.util.spec_from_file_location("custom_transformers", module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find all functions in the module
            transformers = {}
            for name, obj in inspect.getmembers(module):
                if inspect.isfunction(obj) and not name.startswith('_'):
                    transformers[name] = obj

            # Register transformers
            self.register_transformers(transformers)

            logger.info(f"Loaded {len(transformers)} transformers from {module_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading transformer module: {e}")
            return False

    def transform(self, value: Any, transformer: str, *args, **kwargs) -> Any:
        """
        Apply a transformer to a value

        Args:
            value: Value to transform
            transformer: Transformer name
            *args: Positional arguments for the transformer
            **kwargs: Keyword arguments for the transformer

        Returns:
            Transformed value
        """
        if transformer not in self._transformers:
            logger.warning(f"Unknown transformer: {transformer}")
            return value

        try:
            return self._transformers[transformer](value, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error applying transformer '{transformer}': {e}")
            return value

    def apply_transformers(self, value: Any, transformers: List[Dict]) -> Any:
        """
        Apply a list of transformers to a value

        Args:
            value: Value to transform
            transformers: List of transformer configurations
                [
                    {'name': 'strip'},
                    {'name': 'lower'},
                    {'name': 'replace', 'args': [' ', '-']},
                    {'name': 'regex_replace', 'kwargs': {'pattern': r'\W+', 'repl': '-'}}
                ]

        Returns:
            Transformed value
        """
        result = value

        for transformer in transformers:
            name = transformer.get('name')
            if not name:
                continue

            args = transformer.get('args', [])
            kwargs = transformer.get('kwargs', {})

            result = self.transform(result, name, *args, **kwargs)

        return result

    def extract(self, selectors: List[Dict], transformers: List[Dict] = None, combiner: str = 'first') -> Any:
        """
        Extract data using multiple selectors and apply transformers

        Args:
            selectors: List of selector configurations
                [
                    {'type': 'css', 'selector': 'h1', 'attr': 'text'},
                    {'type': 'xpath', 'selector': '//h1/text()'},
                    {'type': 'regex', 'pattern': '<h1>(.*?)</h1>'}
                ]
            transformers: List of transformer configurations
            combiner: How to combine multiple results (first, all, join)

        Returns:
            Extracted and transformed data
        """
        if not self.response:
            logger.error("Response not initialized")
            return None

        # Extract data using selectors
        results = []

        for selector in selectors:
            selector_type = selector.get('type', 'css')

            result = None

            if selector_type == 'css':
                result = self.response.css(
                    selector.get('selector', ''),
                    selector.get('attr'),
                    None
                )
            elif selector_type == 'xpath':
                result = self.response.xpath(
                    selector.get('selector', ''),
                    None
                )
            elif selector_type == 'regex':
                result = self.response.regex(
                    selector.get('pattern', ''),
                    selector.get('text'),
                    selector.get('group', 0),
                    None
                )
            elif selector_type == 'css4':
                result = self.response.css4(
                    selector.get('selector', ''),
                    selector.get('attr'),
                    None
                )
            elif selector_type == 'jsonpath':
                result = self.response.jsonpath(
                    selector.get('path', ''),
                    None
                )
            elif selector_type == 'jmespath':
                result = self.response.jmespath(
                    selector.get('path', ''),
                    None
                )
            elif selector_type == 'graphql':
                if hasattr(self.response, 'graphql'):
                    result = self.response.graphql(
                        selector.get('query', ''),
                        selector.get('variables'),
                        selector.get('path'),
                        None
                    )
            elif selector_type == 'xquery':
                if hasattr(self.response, 'xquery'):
                    result = self.response.xquery(
                        selector.get('query', ''),
                        selector.get('namespaces'),
                        None
                    )
            else:
                logger.warning(f"Unknown selector type: {selector_type}")
                continue

            if result is not None:
                results.append(result)

        # Combine results
        combined_result = None

        if combiner == 'first':
            combined_result = results[0] if results else None
        elif combiner == 'all':
            combined_result = results
        elif combiner == 'join':
            separator = ' '
            combined_result = separator.join([str(r) for r in results if r is not None])
        else:
            logger.warning(f"Unknown combiner: {combiner}")
            combined_result = results[0] if results else None

        # Apply transformers
        if transformers and combined_result is not None:
            combined_result = self.apply_transformers(combined_result, transformers)

        return combined_result

    def extract_multiple(self, config: Dict) -> Dict:
        """
        Extract multiple fields using a configuration

        Args:
            config: Extraction configuration
                {
                    'fields': {
                        'title': {
                            'selectors': [
                                {'type': 'css', 'selector': 'h1', 'attr': 'text'},
                                {'type': 'xpath', 'selector': '//h1/text()'}
                            ],
                            'transformers': [
                                {'name': 'strip'},
                                {'name': 'default', 'args': ['No Title']}
                            ],
                            'combiner': 'first'
                        },
                        'links': {
                            'selectors': [
                                {'type': 'css', 'selector': 'a', 'attr': 'href'}
                            ],
                            'transformers': [
                                {'name': 'unique'}
                            ],
                            'combiner': 'all'
                        }
                    }
                }

        Returns:
            Dictionary with extracted fields
        """
        if not self.response:
            logger.error("Response not initialized")
            return {}

        result = {}
        fields = config.get('fields', {})

        for field_name, field_config in fields.items():
            selectors = field_config.get('selectors', [])
            transformers = field_config.get('transformers', [])
            combiner = field_config.get('combiner', 'first')

            field_value = self.extract(selectors, transformers, combiner)
            result[field_name] = field_value

        return result

    def extract_with_fallbacks(self, selectors: List[Dict], transformers: List[Dict] = None) -> Any:
        """
        Extract data using multiple selectors with fallbacks

        Args:
            selectors: List of selector configurations
            transformers: List of transformer configurations

        Returns:
            Extracted and transformed data
        """
        if not self.response:
            logger.error("Response not initialized")
            return None

        # Try each selector until one succeeds
        result = None

        for selector in selectors:
            selector_type = selector.get('type', 'css')

            if selector_type == 'css':
                result = self.response.css(
                    selector.get('selector', ''),
                    selector.get('attr'),
                    None
                )
            elif selector_type == 'xpath':
                result = self.response.xpath(
                    selector.get('selector', ''),
                    None
                )
            elif selector_type == 'regex':
                result = self.response.regex(
                    selector.get('pattern', ''),
                    selector.get('text'),
                    selector.get('group', 0),
                    None
                )
            elif selector_type == 'css4':
                result = self.response.css4(
                    selector.get('selector', ''),
                    selector.get('attr'),
                    None
                )
            elif selector_type == 'jsonpath':
                result = self.response.jsonpath(
                    selector.get('path', ''),
                    None
                )
            elif selector_type == 'jmespath':
                result = self.response.jmespath(
                    selector.get('path', ''),
                    None
                )
            elif selector_type == 'graphql':
                if hasattr(self.response, 'graphql'):
                    result = self.response.graphql(
                        selector.get('query', ''),
                        selector.get('variables'),
                        selector.get('path'),
                        None
                    )
            elif selector_type == 'xquery':
                if hasattr(self.response, 'xquery'):
                    result = self.response.xquery(
                        selector.get('query', ''),
                        selector.get('namespaces'),
                        None
                    )
            else:
                logger.warning(f"Unknown selector type: {selector_type}")
                continue

            if result is not None:
                break

        # Apply transformers
        if transformers and result is not None:
            result = self.apply_transformers(result, transformers)

        return result

    def extract_table(self, config: Dict) -> List[Dict]:
        """
        Extract a table using a configuration

        Args:
            config: Table extraction configuration
                {
                    'table_selector': {'type': 'css', 'selector': 'table'},
                    'row_selector': {'type': 'css', 'selector': 'tr'},
                    'header_selector': {'type': 'css', 'selector': 'th'},
                    'cell_selector': {'type': 'css', 'selector': 'td'},
                    'header_transformers': [
                        {'name': 'strip'},
                        {'name': 'lower'}
                    ],
                    'cell_transformers': [
                        {'name': 'strip'}
                    ],
                    'skip_rows': 1,
                    'skip_empty': true
                }

        Returns:
            List of dictionaries with table data
        """
        if not self.response:
            logger.error("Response not initialized")
            return []

        # Extract table
        table_selector = config.get('table_selector', {'type': 'css', 'selector': 'table'})
        row_selector = config.get('row_selector', {'type': 'css', 'selector': 'tr'})
        header_selector = config.get('header_selector', {'type': 'css', 'selector': 'th'})
        cell_selector = config.get('cell_selector', {'type': 'css', 'selector': 'td'})

        header_transformers = config.get('header_transformers', [])
        cell_transformers = config.get('cell_transformers', [])

        skip_rows = config.get('skip_rows', 0)
        skip_empty = config.get('skip_empty', True)

        # Extract table element
        table = None
        table_type = table_selector.get('type', 'css')

        if table_type == 'css':
            table = self.response.css(table_selector.get('selector', 'table'), 'html', None)
        elif table_type == 'xpath':
            table = self.response.xpath(table_selector.get('selector', '//table'), None)
        elif table_type == 'css4':
            table = self.response.css4(table_selector.get('selector', 'table'), 'html', None)

        if not table:
            logger.warning("Table not found")
            return []

        # Create a new response object with the table HTML
        from pyspider.libs.response import Response
        table_response = Response(content=table)

        # Extract rows
        rows = []
        row_type = row_selector.get('type', 'css')

        if row_type == 'css':
            rows = table_response.csss(row_selector.get('selector', 'tr'), 'html', [])
        elif row_type == 'xpath':
            rows = table_response.xpaths(row_selector.get('selector', '//tr'), [])
        elif row_type == 'css4':
            rows = table_response.css4s(row_selector.get('selector', 'tr'), 'html', [])

        if not rows:
            logger.warning("No rows found in table")
            return []

        # Extract headers
        headers = []
        header_row = rows[0] if rows else None

        if header_row:
            header_response = Response(content=header_row)
            header_type = header_selector.get('type', 'css')

            if header_type == 'css':
                headers = header_response.csss(header_selector.get('selector', 'th'), 'text', [])
            elif header_type == 'xpath':
                headers = header_response.xpaths(header_selector.get('selector', '//th/text()'), [])
            elif header_type == 'css4':
                headers = header_response.css4s(header_selector.get('selector', 'th'), 'text', [])

            # Apply header transformers
            if header_transformers:
                for i, header in enumerate(headers):
                    headers[i] = self.apply_transformers(header, header_transformers)

        if not headers:
            logger.warning("No headers found in table")
            return []

        # Extract data rows
        result = []

        for i, row in enumerate(rows):
            if i < skip_rows:
                continue

            row_response = Response(content=row)
            cells = []
            cell_type = cell_selector.get('type', 'css')

            if cell_type == 'css':
                cells = row_response.csss(cell_selector.get('selector', 'td'), 'text', [])
            elif cell_type == 'xpath':
                cells = row_response.xpaths(cell_selector.get('selector', '//td/text()'), [])
            elif cell_type == 'css4':
                cells = row_response.css4s(cell_selector.get('selector', 'td'), 'text', [])

            # Apply cell transformers
            if cell_transformers:
                for j, cell in enumerate(cells):
                    cells[j] = self.apply_transformers(cell, cell_transformers)

            # Create row data
            row_data = {}
            for j, cell in enumerate(cells):
                if j < len(headers):
                    row_data[headers[j]] = cell
                else:
                    row_data[f'column_{j}'] = cell

            # Skip empty rows
            if skip_empty and not any(row_data.values()):
                continue

            result.append(row_data)

        return result

    def extract_list(self, config: Dict) -> List[Dict]:
        """
        Extract a list using a configuration

        Args:
            config: List extraction configuration
                {
                    'list_selector': {'type': 'css', 'selector': 'ul'},
                    'item_selector': {'type': 'css', 'selector': 'li'},
                    'fields': {
                        'text': {
                            'selectors': [
                                {'type': 'css', 'selector': '', 'attr': 'text'}
                            ],
                            'transformers': [
                                {'name': 'strip'}
                            ]
                        },
                        'link': {
                            'selectors': [
                                {'type': 'css', 'selector': 'a', 'attr': 'href'}
                            ]
                        }
                    },
                    'skip_empty': true
                }

        Returns:
            List of dictionaries with extracted data
        """

    def create_pipeline(self, steps: List[Dict]) -> Callable[[Any], Any]:
        """
        Create a data transformation pipeline

        Args:
            steps: List of pipeline steps
                [
                    {
                        'type': 'selector',
                        'selectors': [
                            {'type': 'css', 'selector': 'h1', 'attr': 'text'}
                        ]
                    },
                    {
                        'type': 'transform',
                        'transformers': [
                            {'name': 'strip'},
                            {'name': 'upper'}
                        ]
                    },
                    {
                        'type': 'condition',
                        'condition': {
                            'type': 'not_empty'
                        },
                        'then': [
                            {'name': 'prefix', 'args': ['Title: ']}
                        ],
                        'else': [
                            {'name': 'default', 'args': ['No Title']}
                        ]
                    }
                ]

        Returns:
            Pipeline function that takes input data and returns transformed data
        """
        def pipeline(data: Any) -> Any:
            result = data

            for step in steps:
                step_type = step.get('type')

                if step_type == 'selector':
                    # Extract data using selectors
                    selectors = step.get('selectors', [])
                    combiner = step.get('combiner', 'first')
                    result = self.extract(selectors, [], combiner)

                elif step_type == 'transform':
                    # Apply transformers
                    transformers = step.get('transformers', [])
                    result = self.apply_transformers(result, transformers)

                elif step_type == 'condition':
                    # Apply conditional transformation
                    condition = step.get('condition', {})
                    condition_type = condition.get('type')
                    condition_value = condition.get('value')

                    condition_met = False

                    if condition_type == 'equals':
                        condition_met = result == condition_value
                    elif condition_type == 'not_equals':
                        condition_met = result != condition_value
                    elif condition_type == 'contains':
                        condition_met = condition_value in result if hasattr(result, '__contains__') else False
                    elif condition_type == 'not_contains':
                        condition_met = condition_value not in result if hasattr(result, '__contains__') else True
                    elif condition_type == 'empty':
                        condition_met = not result
                    elif condition_type == 'not_empty':
                        condition_met = bool(result)
                    elif condition_type == 'greater_than':
                        condition_met = result > condition_value if result is not None else False
                    elif condition_type == 'less_than':
                        condition_met = result < condition_value if result is not None else False
                    elif condition_type == 'matches':
                        condition_met = bool(re.search(condition_value, result)) if isinstance(result, str) else False
                    elif condition_type == 'custom':
                        # Custom condition function
                        condition_func = condition.get('function')
                        if condition_func in self._transformers:
                            condition_met = self._transformers[condition_func](result)
                        else:
                            logger.warning(f"Unknown condition function: {condition_func}")

                    # Apply transformers based on condition
                    if condition_met:
                        then_transformers = step.get('then', [])
                        result = self.apply_transformers(result, then_transformers)
                    else:
                        else_transformers = step.get('else', [])
                        result = self.apply_transformers(result, else_transformers)

                elif step_type == 'parallel':
                    # Process data in parallel branches and combine results
                    branches = step.get('branches', [])
                    branch_results = []

                    for branch in branches:
                        branch_pipeline = self.create_pipeline(branch)
                        branch_result = branch_pipeline(result)
                        branch_results.append(branch_result)

                    # Combine results based on combiner type
                    combiner = step.get('combiner', 'list')
                    if combiner == 'list':
                        result = branch_results
                    elif combiner == 'dict':
                        keys = step.get('keys', [])
                        if len(keys) == len(branch_results):
                            result = dict(zip(keys, branch_results))
                        else:
                            result = {f"branch_{i}": res for i, res in enumerate(branch_results)}
                    elif combiner == 'join':
                        separator = step.get('separator', ' ')
                        result = separator.join([str(res) for res in branch_results if res is not None])

                elif step_type == 'loop':
                    # Process a list of items with a sub-pipeline
                    if isinstance(result, list):
                        sub_steps = step.get('steps', [])
                        sub_pipeline = self.create_pipeline(sub_steps)

                        # Process each item
                        processed_items = []
                        for item in result:
                            processed_item = sub_pipeline(item)
                            processed_items.append(processed_item)

                        result = processed_items

                else:
                    logger.warning(f"Unknown pipeline step type: {step_type}")

            return result

        return pipeline

    def execute_pipeline(self, pipeline_config: Dict, input_data: Any = None) -> Any:
        """
        Execute a data transformation pipeline

        Args:
            pipeline_config: Pipeline configuration
                {
                    'steps': [
                        {'type': 'selector', 'selectors': [...]},
                        {'type': 'transform', 'transformers': [...]},
                        ...
                    ]
                }
            input_data: Input data for the pipeline

        Returns:
            Transformed data
        """
        steps = pipeline_config.get('steps', [])
        pipeline = self.create_pipeline(steps)
        return pipeline(input_data)

    def extract_list(self, config: Dict) -> List[Dict]:
        """
        Extract a list using a configuration

        Args:
            config: List extraction configuration
                {
                    'list_selector': {'type': 'css', 'selector': 'ul'},
                    'item_selector': {'type': 'css', 'selector': 'li'},
                    'fields': {
                        'text': {
                            'selectors': [
                                {'type': 'css', 'selector': '', 'attr': 'text'}
                            ],
                            'transformers': [
                                {'name': 'strip'}
                            ]
                        },
                        'link': {
                            'selectors': [
                                {'type': 'css', 'selector': 'a', 'attr': 'href'}
                            ]
                        }
                    },
                    'skip_empty': true
                }

        Returns:
            List of dictionaries with extracted data
        """
        if not self.response:
            logger.error("Response not initialized")
            return []

        # Extract list
        list_selector = config.get('list_selector', {'type': 'css', 'selector': 'ul'})
        item_selector = config.get('item_selector', {'type': 'css', 'selector': 'li'})
        fields = config.get('fields', {})
        skip_empty = config.get('skip_empty', True)

        # Extract list element
        list_html = None
        list_type = list_selector.get('type', 'css')

        if list_type == 'css':
            list_html = self.response.css(list_selector.get('selector', 'ul'), 'html', None)
        elif list_type == 'xpath':
            list_html = self.response.xpath(list_selector.get('selector', '//ul'), None)
        elif list_type == 'css4':
            list_html = self.response.css4(list_selector.get('selector', 'ul'), 'html', None)

        if not list_html:
            logger.warning("List not found")
            return []

        # Create a new response object with the list HTML
        from pyspider.libs.response import Response
        list_response = Response(content=list_html)

        # Extract items
        items = []
        item_type = item_selector.get('type', 'css')

        if item_type == 'css':
            items = list_response.csss(item_selector.get('selector', 'li'), 'html', [])
        elif item_type == 'xpath':
            items = list_response.xpaths(item_selector.get('selector', '//li'), [])
        elif item_type == 'css4':
            items = list_response.css4s(item_selector.get('selector', 'li'), 'html', [])

        if not items:
            logger.warning("No items found in list")
            return []

        # Extract data from items
        result = []

        for item_html in items:
            item_response = Response(content=item_html)
            item_pipeline = SelectorPipeline(item_response)

            item_data = {}
            for field_name, field_config in fields.items():
                selectors = field_config.get('selectors', [])
                transformers = field_config.get('transformers', [])
                combiner = field_config.get('combiner', 'first')

                field_value = item_pipeline.extract(selectors, transformers, combiner)
                item_data[field_name] = field_value

            # Skip empty items
            if skip_empty and not any(item_data.values()):
                continue

            result.append(item_data)

        return result

class SelectorErrorHandler:
    r"""
    Handles errors that occur during selector processing.
    
    Provides methods for:
    1. Validating selectors
    2. Handling selector errors
    3. Providing error messages and suggestions
    
    Example:
        >>> handler = SelectorErrorHandler()
        >>> is_valid = handler.validate_selector({
        ...     'type': 'xpath',
        ...     'selector': '//div[\\W]'  # Contains non-word character class
        ... })
    """
    def __init__(self):
        self.errors = []
        self.suggestions = []
