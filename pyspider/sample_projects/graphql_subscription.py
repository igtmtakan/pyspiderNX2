#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-28 14:00:00

"""
Sample project demonstrating GraphQL subscription features
"""

import time
import json
from pyspider.libs.base_handler import *

class Handler(BaseHandler):
    crawl_config = {
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
    }
    
    # Store subscription data
    subscription_data = {}
    subscription_ids = {}
    
    @every(minutes=24 * 60)
    def on_start(self):
        # GraphQL API with subscription support
        self.crawl('https://countries.trevorblades.com/', callback=self.graphql_page)
        
        # Real-time cryptocurrency price API
        self.crawl('https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3', callback=self.crypto_price_page)
        
        # GitHub GraphQL API (requires authentication)
        # self.crawl('https://api.github.com/graphql', 
        #           headers={'Authorization': 'Bearer YOUR_GITHUB_TOKEN'},
        #           callback=self.github_page)
    
    def handle_subscription_data(self, data):
        """Handle data received from subscription"""
        self.logger.info(f"Received subscription data: {json.dumps(data, indent=2)}")
        
        # Store data for later use
        subscription_key = data.get('id', 'unknown')
        self.subscription_data[subscription_key] = data
    
    @config(age=10 * 24 * 60 * 60)
    def graphql_page(self, response):
        """Process GraphQL API with basic query and subscription"""
        # 1. Basic GraphQL Query
        query = """
        query {
          countries {
            name
            code
            capital
            currency
          }
        }
        """
        
        countries = response.graphql(query, path='countries')
        self.logger.info(f"Countries (first 3): {countries[:3] if countries else []}")
        
        # 2. GraphQL Subscription (simulated since this API doesn't support subscriptions)
        # In a real subscription-enabled API, you would use:
        # subscription_id = response.graphql_subscribe(
        #     """
        #     subscription {
        #       countryUpdated {
        #         name
        #         code
        #         capital
        #       }
        #     }
        #     """,
        #     callback=self.handle_subscription_data
        # )
        # self.subscription_ids['countries'] = subscription_id
        
        # For demonstration, we'll just return the query results
        return {
            'countries_count': len(countries) if countries else 0,
            'countries': countries[:5] if countries else []
        }
    
    @config(age=10 * 24 * 60 * 60)
    def crypto_price_page(self, response):
        """Process cryptocurrency price data with subscription"""
        # 1. Basic GraphQL Query for token data
        query = """
        query {
          tokens(first: 5, orderBy: volumeUSD, orderDirection: desc) {
            id
            symbol
            name
            decimals
            volume
            volumeUSD
            priceUSD
          }
        }
        """
        
        tokens = response.graphql(query, path='tokens')
        self.logger.info(f"Top tokens: {tokens}")
        
        # 2. GraphQL Subscription for price updates
        # Note: This is a simulated example. The actual API might have different subscription format.
        subscription_query = """
        subscription {
          tokenPriceUpdated {
            id
            symbol
            priceUSD
            timestamp
          }
        }
        """
        
        # In a real application, you would use:
        # subscription_id = response.graphql_subscribe(
        #     subscription_query,
        #     callback=self.handle_subscription_data
        # )
        # self.subscription_ids['crypto_prices'] = subscription_id
        
        # For demonstration, we'll just return the query results
        return {
            'tokens': tokens,
            'subscription_active': False  # Would be True in a real application
        }
    
    @config(age=10 * 24 * 60 * 60)
    def github_page(self, response):
        """Process GitHub GraphQL API with subscription"""
        # 1. Basic GraphQL Query for repository data
        query = """
        query {
          viewer {
            login
            repositories(first: 5, orderBy: {field: UPDATED_AT, direction: DESC}) {
              nodes {
                name
                description
                url
                stargazerCount
                updatedAt
              }
            }
          }
        }
        """
        
        data = response.graphql(query)
        self.logger.info(f"GitHub data: {data}")
        
        # 2. GraphQL Subscription for repository updates
        # Note: GitHub doesn't support GraphQL subscriptions yet, this is for demonstration
        subscription_query = """
        subscription {
          repositoryUpdated {
            repository {
              name
              description
              url
              updatedAt
            }
            actor {
              login
            }
            action
          }
        }
        """
        
        # In a real subscription-enabled API, you would use:
        # subscription_id = response.graphql_subscribe(
        #     subscription_query,
        #     callback=self.handle_subscription_data
        # )
        # self.subscription_ids['github'] = subscription_id
        
        # For demonstration, we'll just return the query results
        return {
            'github_data': data,
            'subscription_active': False  # Would be True in a real application
        }
    
    def on_exit(self, response):
        """Clean up subscriptions when the crawler exits"""
        for name, subscription_id in self.subscription_ids.items():
            self.logger.info(f"Unsubscribing from {name} (ID: {subscription_id})")
            # In a real application, you would use:
            # response.graphql_unsubscribe(subscription_id)
        
        self.subscription_ids = {}
