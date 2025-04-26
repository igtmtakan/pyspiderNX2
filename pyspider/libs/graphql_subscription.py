#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-28 13:00:00

import json
import logging
import asyncio
import threading
from typing import Dict, List, Any, Optional, Union, Callable, Awaitable
from urllib.parse import urlparse, urlunparse

import websockets
from gql import Client, gql
from gql.transport.websockets import WebsocketsTransport
from graphql import GraphQLError

logger = logging.getLogger('graphql_subscription')

class GraphQLSubscription:
    """
    GraphQL subscription client for real-time data
    """
    
    def __init__(self, endpoint: str = None, headers: Dict[str, str] = None, 
                 connection_params: Dict[str, Any] = None, timeout: int = 30):
        """
        Initialize the subscription client
        
        Args:
            endpoint: GraphQL endpoint URL (can be HTTP or WebSocket)
            headers: HTTP headers for the connection
            connection_params: Connection parameters for the WebSocket
            timeout: Connection timeout in seconds
        """
        self.endpoint = endpoint
        self.headers = headers or {}
        self.connection_params = connection_params or {}
        self.timeout = timeout
        self._client = None
        self._transport = None
        self._subscriptions = {}
        self._next_subscription_id = 1
        self._running = False
        self._loop = None
        self._thread = None
    
    def _convert_to_ws_url(self, url: str) -> str:
        """
        Convert HTTP URL to WebSocket URL
        
        Args:
            url: HTTP URL
            
        Returns:
            WebSocket URL
        """
        parsed = urlparse(url)
        scheme = 'wss' if parsed.scheme == 'https' else 'ws'
        return urlunparse((scheme, parsed.netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))
    
    async def connect(self):
        """Connect to the GraphQL endpoint"""
        if not self.endpoint:
            raise ValueError("Endpoint URL is required")
        
        # Convert HTTP URL to WebSocket URL if needed
        ws_url = self.endpoint
        if ws_url.startswith('http'):
            ws_url = self._convert_to_ws_url(ws_url)
        
        try:
            # Create WebSocket transport
            self._transport = WebsocketsTransport(
                url=ws_url,
                headers=self.headers,
                init_payload=self.connection_params,
                connect_timeout=self.timeout
            )
            
            # Create client
            self._client = Client(
                transport=self._transport,
                fetch_schema_from_transport=False
            )
            
            # Connect to the endpoint
            await self._transport.connect()
            logger.info(f"Connected to GraphQL endpoint: {ws_url}")
            return True
        except Exception as e:
            logger.error(f"Error connecting to GraphQL endpoint: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the GraphQL endpoint"""
        try:
            if self._transport:
                await self._transport.close()
                self._transport = None
            
            self._client = None
            logger.info("Disconnected from GraphQL endpoint")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting from GraphQL endpoint: {e}")
            return False
    
    async def subscribe(self, query: str, variables: Dict[str, Any] = None, 
                       callback: Callable[[Dict[str, Any]], Awaitable[None]] = None) -> int:
        """
        Subscribe to a GraphQL subscription
        
        Args:
            query: GraphQL subscription query
            variables: Variables for the query
            callback: Callback function to handle received data
            
        Returns:
            Subscription ID
        """
        if not self._client:
            if not await self.connect():
                raise ConnectionError("Failed to connect to GraphQL endpoint")
        
        try:
            # Parse the query
            parsed_query = gql(query)
            
            # Generate subscription ID
            subscription_id = self._next_subscription_id
            self._next_subscription_id += 1
            
            # Create subscription
            self._subscriptions[subscription_id] = {
                'query': parsed_query,
                'variables': variables,
                'callback': callback,
                'active': True,
                'task': None
            }
            
            # Start subscription task
            if callback:
                task = asyncio.create_task(self._subscription_task(subscription_id))
                self._subscriptions[subscription_id]['task'] = task
            
            logger.info(f"Subscription {subscription_id} created")
            return subscription_id
        except GraphQLError as e:
            logger.error(f"GraphQL error in subscription: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating subscription: {e}")
            raise
    
    async def unsubscribe(self, subscription_id: int) -> bool:
        """
        Unsubscribe from a GraphQL subscription
        
        Args:
            subscription_id: Subscription ID
            
        Returns:
            True if successful, False otherwise
        """
        if subscription_id not in self._subscriptions:
            logger.warning(f"Subscription {subscription_id} not found")
            return False
        
        try:
            # Mark subscription as inactive
            self._subscriptions[subscription_id]['active'] = False
            
            # Cancel task if running
            task = self._subscriptions[subscription_id].get('task')
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Remove subscription
            del self._subscriptions[subscription_id]
            
            logger.info(f"Subscription {subscription_id} cancelled")
            return True
        except Exception as e:
            logger.error(f"Error unsubscribing from subscription {subscription_id}: {e}")
            return False
    
    async def _subscription_task(self, subscription_id: int):
        """
        Task to handle subscription data
        
        Args:
            subscription_id: Subscription ID
        """
        if subscription_id not in self._subscriptions:
            return
        
        subscription = self._subscriptions[subscription_id]
        query = subscription['query']
        variables = subscription['variables']
        callback = subscription['callback']
        
        try:
            # Execute subscription
            async for result in self._client.subscribe(query, variable_values=variables):
                if not subscription['active']:
                    break
                
                # Call callback with result
                if callback:
                    await callback(result)
        except asyncio.CancelledError:
            logger.info(f"Subscription {subscription_id} task cancelled")
        except Exception as e:
            logger.error(f"Error in subscription {subscription_id}: {e}")
            
            # Mark subscription as inactive
            subscription['active'] = False
    
    def start_background_loop(self):
        """Start a background event loop for subscriptions"""
        if self._running:
            return
        
        def run_loop():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()
        
        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()
        self._running = True
        logger.info("Background event loop started")
    
    def stop_background_loop(self):
        """Stop the background event loop"""
        if not self._running:
            return
        
        # Stop all subscriptions
        if self._loop:
            for subscription_id in list(self._subscriptions.keys()):
                asyncio.run_coroutine_threadsafe(self.unsubscribe(subscription_id), self._loop)
            
            # Disconnect
            asyncio.run_coroutine_threadsafe(self.disconnect(), self._loop)
            
            # Stop loop
            self._loop.call_soon_threadsafe(self._loop.stop)
        
        # Wait for thread to finish
        if self._thread:
            self._thread.join(timeout=5)
        
        self._running = False
        self._loop = None
        self._thread = None
        logger.info("Background event loop stopped")
    
    def subscribe_in_background(self, query: str, variables: Dict[str, Any] = None, 
                              callback: Callable[[Dict[str, Any]], None] = None) -> int:
        """
        Subscribe to a GraphQL subscription in the background loop
        
        Args:
            query: GraphQL subscription query
            variables: Variables for the query
            callback: Callback function to handle received data
            
        Returns:
            Subscription ID
        """
        if not self._running:
            self.start_background_loop()
        
        # Create async callback wrapper
        async def async_callback(data):
            if callback:
                callback(data)
        
        # Run subscribe in the background loop
        future = asyncio.run_coroutine_threadsafe(
            self.subscribe(query, variables, async_callback), 
            self._loop
        )
        
        # Get subscription ID
        return future.result(timeout=self.timeout)
    
    def unsubscribe_in_background(self, subscription_id: int) -> bool:
        """
        Unsubscribe from a GraphQL subscription in the background loop
        
        Args:
            subscription_id: Subscription ID
            
        Returns:
            True if successful, False otherwise
        """
        if not self._running:
            return False
        
        # Run unsubscribe in the background loop
        future = asyncio.run_coroutine_threadsafe(
            self.unsubscribe(subscription_id), 
            self._loop
        )
        
        # Get result
        return future.result(timeout=self.timeout)
    
    async def execute_query(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query
        
        Args:
            query: GraphQL query
            variables: Variables for the query
            
        Returns:
            Query result
        """
        if not self._client:
            if not await self.connect():
                raise ConnectionError("Failed to connect to GraphQL endpoint")
        
        try:
            # Parse the query
            parsed_query = gql(query)
            
            # Execute query
            result = await self._client.execute_async(parsed_query, variable_values=variables)
            return result
        except GraphQLError as e:
            logger.error(f"GraphQL error in query: {e}")
            raise
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def execute_query_in_background(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query in the background loop
        
        Args:
            query: GraphQL query
            variables: Variables for the query
            
        Returns:
            Query result
        """
        if not self._running:
            self.start_background_loop()
        
        # Run query in the background loop
        future = asyncio.run_coroutine_threadsafe(
            self.execute_query(query, variables), 
            self._loop
        )
        
        # Get result
        return future.result(timeout=self.timeout)
