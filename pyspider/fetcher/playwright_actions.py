#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-28 10:00:00

import json
import time
import logging
from typing import Dict, List, Any, Optional, Union, Tuple

logger = logging.getLogger('playwright_actions')

class PlaywrightActions:
    """
    Class for simulating user actions with Playwright
    """
    
    def __init__(self, page=None):
        """
        Initialize with a Playwright page
        
        Args:
            page: Playwright page object
        """
        self.page = page
        self._recorded_actions = []
        self._current_action_index = 0
    
    async def perform_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform a single action
        
        Args:
            action: Action configuration
                {
                    'type': 'click',
                    'selector': '#submit-button',
                    'options': {'force': true}
                }
                
        Returns:
            Result of the action
        """
        if not self.page:
            return {'success': False, 'error': 'Page not initialized'}
        
        action_type = action.get('type')
        result = {'type': action_type, 'success': False}
        
        try:
            if action_type == 'click':
                await self._perform_click(action, result)
            elif action_type == 'fill':
                await self._perform_fill(action, result)
            elif action_type == 'select':
                await self._perform_select(action, result)
            elif action_type == 'check':
                await self._perform_check(action, result)
            elif action_type == 'uncheck':
                await self._perform_uncheck(action, result)
            elif action_type == 'hover':
                await self._perform_hover(action, result)
            elif action_type == 'press':
                await self._perform_press(action, result)
            elif action_type == 'scroll':
                await self._perform_scroll(action, result)
            elif action_type == 'screenshot':
                await self._perform_screenshot(action, result)
            elif action_type == 'wait_for_selector':
                await self._perform_wait_for_selector(action, result)
            elif action_type == 'wait_for_navigation':
                await self._perform_wait_for_navigation(action, result)
            elif action_type == 'wait_for_load_state':
                await self._perform_wait_for_load_state(action, result)
            elif action_type == 'wait_for_timeout':
                await self._perform_wait_for_timeout(action, result)
            elif action_type == 'evaluate':
                await self._perform_evaluate(action, result)
            elif action_type == 'goto':
                await self._perform_goto(action, result)
            elif action_type == 'reload':
                await self._perform_reload(action, result)
            elif action_type == 'back':
                await self._perform_back(action, result)
            elif action_type == 'forward':
                await self._perform_forward(action, result)
            else:
                result['error'] = f"Unknown action type: {action_type}"
                return result
            
            result['success'] = True
            return result
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error performing action {action_type}: {e}")
            return result
    
    async def perform_actions(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Perform a sequence of actions
        
        Args:
            actions: List of action configurations
                
        Returns:
            List of action results
        """
        results = []
        
        for action in actions:
            result = await self.perform_action(action)
            results.append(result)
            
            # Stop on error unless continue_on_error is True
            if not result['success'] and not action.get('continue_on_error', False):
                break
        
        return results
    
    async def _perform_click(self, action: Dict[str, Any], result: Dict[str, Any]):
        """Perform click action"""
        selector = action.get('selector')
        if not selector:
            result['error'] = "Selector is required for click action"
            return
        
        options = action.get('options', {})
        await self.page.click(selector, **options)
        result['selector'] = selector
    
    async def _perform_fill(self, action: Dict[str, Any], result: Dict[str, Any]):
        """Perform fill action"""
        selector = action.get('selector')
        value = action.get('value', '')
        
        if not selector:
            result['error'] = "Selector is required for fill action"
            return
        
        options = action.get('options', {})
        await self.page.fill(selector, value, **options)
        result['selector'] = selector
        result['value'] = value
    
    async def _perform_select(self, action: Dict[str, Any], result: Dict[str, Any]):
        """Perform select action"""
        selector = action.get('selector')
        value = action.get('value')
        
        if not selector:
            result['error'] = "Selector is required for select action"
            return
        
        if not value:
            result['error'] = "Value is required for select action"
            return
        
        options = action.get('options', {})
        
        # Handle different value types
        if isinstance(value, list):
            await self.page.select_option(selector, value=value, **options)
        else:
            await self.page.select_option(selector, value=[value], **options)
        
        result['selector'] = selector
        result['value'] = value
    
    async def _perform_check(self, action: Dict[str, Any], result: Dict[str, Any]):
        """Perform check action"""
        selector = action.get('selector')
        if not selector:
            result['error'] = "Selector is required for check action"
            return
        
        options = action.get('options', {})
        await self.page.check(selector, **options)
        result['selector'] = selector
    
    async def _perform_uncheck(self, action: Dict[str, Any], result: Dict[str, Any]):
        """Perform uncheck action"""
        selector = action.get('selector')
        if not selector:
            result['error'] = "Selector is required for uncheck action"
            return
        
        options = action.get('options', {})
        await self.page.uncheck(selector, **options)
        result['selector'] = selector
    
    async def _perform_hover(self, action: Dict[str, Any], result: Dict[str, Any]):
        """Perform hover action"""
        selector = action.get('selector')
        if not selector:
            result['error'] = "Selector is required for hover action"
            return
        
        options = action.get('options', {})
        await self.page.hover(selector, **options)
        result['selector'] = selector
    
    async def _perform_press(self, action: Dict[str, Any], result: Dict[str, Any]):
        """Perform press action"""
        selector = action.get('selector')
        key = action.get('key')
        
        if not selector:
            result['error'] = "Selector is required for press action"
            return
        
        if not key:
            result['error'] = "Key is required for press action"
            return
        
        options = action.get('options', {})
        await self.page.press(selector, key, **options)
        result['selector'] = selector
        result['key'] = key
    
    async def _perform_scroll(self, action: Dict[str, Any], result: Dict[str, Any]):
        """Perform scroll action"""
        selector = action.get('selector')
        
        if selector:
            # Scroll element into view
            options = action.get('options', {})
            await self.page.scroll_into_view_if_needed(selector, **options)
            result['selector'] = selector
        else:
            # Scroll window
            x = action.get('x', 0)
            y = action.get('y', 0)
            
            await self.page.evaluate(f"window.scrollTo({x}, {y})")
            result['x'] = x
            result['y'] = y
    
    async def _perform_screenshot(self, action: Dict[str, Any], result: Dict[str, Any]):
        """Perform screenshot action"""
        path = action.get('path')
        selector = action.get('selector')
        
        options = action.get('options', {})
        
        if selector:
            # Screenshot of element
            screenshot = await self.page.locator(selector).screenshot(path=path, **options)
            result['selector'] = selector
        else:
            # Screenshot of page
            screenshot = await self.page.screenshot(path=path, **options)
        
        if path:
            result['path'] = path
        else:
            # Return base64 encoded screenshot
            import base64
            result['data'] = base64.b64encode(screenshot).decode('utf-8')
    
    async def _perform_wait_for_selector(self, action: Dict[str, Any], result: Dict[str, Any]):
        """Perform wait for selector action"""
        selector = action.get('selector')
        if not selector:
            result['error'] = "Selector is required for wait_for_selector action"
            return
        
        options = action.get('options', {})
        await self.page.wait_for_selector(selector, **options)
        result['selector'] = selector
    
    async def _perform_wait_for_navigation(self, action: Dict[str, Any], result: Dict[str, Any]):
        """Perform wait for navigation action"""
        options = action.get('options', {})
        await self.page.wait_for_navigation(**options)
    
    async def _perform_wait_for_load_state(self, action: Dict[str, Any], result: Dict[str, Any]):
        """Perform wait for load state action"""
        state = action.get('state', 'load')
        options = action.get('options', {})
        await self.page.wait_for_load_state(state, **options)
        result['state'] = state
    
    async def _perform_wait_for_timeout(self, action: Dict[str, Any], result: Dict[str, Any]):
        """Perform wait for timeout action"""
        timeout = action.get('timeout', 1000)
        await self.page.wait_for_timeout(timeout)
        result['timeout'] = timeout
    
    async def _perform_evaluate(self, action: Dict[str, Any], result: Dict[str, Any]):
        """Perform evaluate action"""
        expression = action.get('expression')
        if not expression:
            result['error'] = "Expression is required for evaluate action"
            return
        
        arg = action.get('arg')
        
        if arg is not None:
            eval_result = await self.page.evaluate(expression, arg)
        else:
            eval_result = await self.page.evaluate(expression)
        
        result['expression'] = expression
        result['eval_result'] = eval_result
    
    async def _perform_goto(self, action: Dict[str, Any], result: Dict[str, Any]):
        """Perform goto action"""
        url = action.get('url')
        if not url:
            result['error'] = "URL is required for goto action"
            return
        
        options = action.get('options', {})
        response = await self.page.goto(url, **options)
        result['url'] = url
        
        if response:
            result['status'] = response.status
    
    async def _perform_reload(self, action: Dict[str, Any], result: Dict[str, Any]):
        """Perform reload action"""
        options = action.get('options', {})
        response = await self.page.reload(**options)
        
        if response:
            result['status'] = response.status
    
    async def _perform_back(self, action: Dict[str, Any], result: Dict[str, Any]):
        """Perform back action"""
        options = action.get('options', {})
        response = await self.page.go_back(**options)
        
        if response:
            result['status'] = response.status
    
    async def _perform_forward(self, action: Dict[str, Any], result: Dict[str, Any]):
        """Perform forward action"""
        options = action.get('options', {})
        response = await self.page.go_forward(**options)
        
        if response:
            result['status'] = response.status
    
    async def start_recording(self):
        """Start recording user actions"""
        self._recorded_actions = []
        
        # Add event listeners to record actions
        await self.page.evaluate("""() => {
            window.__recordedActions = [];
            
            // Record clicks
            document.addEventListener('click', (event) => {
                const target = event.target;
                const selector = getSelector(target);
                if (selector) {
                    window.__recordedActions.push({
                        type: 'click',
                        selector: selector,
                        timestamp: Date.now()
                    });
                }
            }, true);
            
            // Record inputs
            document.addEventListener('change', (event) => {
                const target = event.target;
                const selector = getSelector(target);
                if (selector) {
                    if (target.tagName === 'INPUT') {
                        if (target.type === 'checkbox' || target.type === 'radio') {
                            window.__recordedActions.push({
                                type: target.checked ? 'check' : 'uncheck',
                                selector: selector,
                                timestamp: Date.now()
                            });
                        } else {
                            window.__recordedActions.push({
                                type: 'fill',
                                selector: selector,
                                value: target.value,
                                timestamp: Date.now()
                            });
                        }
                    } else if (target.tagName === 'SELECT') {
                        const values = Array.from(target.selectedOptions).map(option => option.value);
                        window.__recordedActions.push({
                            type: 'select',
                            selector: selector,
                            value: values.length === 1 ? values[0] : values,
                            timestamp: Date.now()
                        });
                    } else if (target.tagName === 'TEXTAREA') {
                        window.__recordedActions.push({
                            type: 'fill',
                            selector: selector,
                            value: target.value,
                            timestamp: Date.now()
                        });
                    }
                }
            }, true);
            
            // Helper function to get a unique selector for an element
            function getSelector(element) {
                // Try ID
                if (element.id) {
                    return '#' + element.id;
                }
                
                // Try data-testid
                if (element.dataset.testid) {
                    return `[data-testid="${element.dataset.testid}"]`;
                }
                
                // Try classes
                if (element.className && typeof element.className === 'string') {
                    const classes = element.className.trim().split(/\\s+/);
                    if (classes.length > 0) {
                        const selector = '.' + classes.join('.');
                        // Check if this selector is unique
                        if (document.querySelectorAll(selector).length === 1) {
                            return selector;
                        }
                    }
                }
                
                // Try tag name with nth-child
                const parent = element.parentNode;
                if (parent) {
                    const children = Array.from(parent.children);
                    const index = children.indexOf(element);
                    if (index !== -1) {
                        const tagName = element.tagName.toLowerCase();
                        return `${getSelector(parent)} > ${tagName}:nth-child(${index + 1})`;
                    }
                }
                
                // Fallback to a complex selector
                const tagName = element.tagName.toLowerCase();
                return tagName;
            }
        }""")
    
    async def stop_recording(self) -> List[Dict[str, Any]]:
        """
        Stop recording user actions and return the recorded actions
        
        Returns:
            List of recorded actions
        """
        # Get recorded actions from the page
        recorded_actions = await self.page.evaluate("window.__recordedActions || []")
        self._recorded_actions = recorded_actions
        
        # Clear recorded actions in the page
        await self.page.evaluate("window.__recordedActions = []")
        
        return self._recorded_actions
    
    async def replay_recorded_actions(self, delay: int = 500) -> List[Dict[str, Any]]:
        """
        Replay recorded actions
        
        Args:
            delay: Delay between actions in milliseconds
            
        Returns:
            List of action results
        """
        results = []
        
        for action in self._recorded_actions:
            # Wait for delay
            await self.page.wait_for_timeout(delay)
            
            # Perform action
            result = await self.perform_action(action)
            results.append(result)
            
            # Stop on error
            if not result['success']:
                break
        
        return results
    
    def save_recorded_actions(self, path: str) -> bool:
        """
        Save recorded actions to a file
        
        Args:
            path: Path to save the actions
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(path, 'w') as f:
                json.dump(self._recorded_actions, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving recorded actions: {e}")
            return False
    
    def load_recorded_actions(self, path: str) -> bool:
        """
        Load recorded actions from a file
        
        Args:
            path: Path to load the actions from
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(path, 'r') as f:
                self._recorded_actions = json.load(f)
            return True
        except Exception as e:
            logger.error(f"Error loading recorded actions: {e}")
            return False
