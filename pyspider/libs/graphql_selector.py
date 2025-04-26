#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-27 10:00:00

import json
import logging
from typing import List, Dict, Union, Optional, Any, Tuple, Callable

import requests
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from graphql import parse, print_ast, GraphQLError

from pyspider.libs.graphql_subscription import GraphQLSubscription

logger = logging.getLogger('graphql_selector')

class GraphQLSelector:
    """
    GraphQL selector for querying GraphQL APIs
    """

    def __init__(self, response=None, endpoint=None, headers=None, json_data=None):
        """
        Initialize the selector with response or endpoint

        Args:
            response: PySpider response object
            endpoint: GraphQL API endpoint URL
            headers: HTTP headers for the request
            json_data: JSON data from a GraphQL response
        """
        self.response = response
        self._endpoint = endpoint
        self._headers = headers or {}
        self._json_data = json_data
        self._client = None
        self._schema = None
        self._introspection_data = None
        self._subscription = None

        if response:
            # Try to extract endpoint from response URL
            self._endpoint = response.url

            # Try to extract headers from response
            if hasattr(response, 'headers') and response.headers:
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' in content_type or 'application/graphql' in content_type:
                    self._headers['Content-Type'] = content_type

            # Try to parse JSON data from response
            try:
                self._json_data = response.json
            except Exception as e:
                logger.error(f"Error parsing JSON from response: {e}")
                self._json_data = None

    @property
    def client(self):
        """Get GraphQL client"""
        if not self._client and self._endpoint:
            try:
                transport = RequestsHTTPTransport(
                    url=self._endpoint,
                    headers=self._headers,
                    verify=True,
                    retries=3,
                )
                self._client = Client(transport=transport, fetch_schema_from_transport=False)
            except Exception as e:
                logger.error(f"Error initializing GraphQL client: {e}")
        return self._client

    def execute(self, query: str, variables: Dict = None) -> Dict:
        """
        Execute a GraphQL query

        Args:
            query: GraphQL query string
            variables: Variables for the query

        Returns:
            Query result as dict
        """
        if not self.client:
            logger.error("GraphQL client not initialized")
            return {}

        try:
            # Parse and validate the query
            parsed_query = gql(query)

            # Execute the query
            result = self.client.execute(parsed_query, variable_values=variables)
            return result
        except GraphQLError as e:
            logger.error(f"GraphQL query error: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error executing GraphQL query: {e}")
            return {}

    def query(self, query: str, variables: Dict = None, path: str = None, default: Any = None) -> Any:
        """
        Execute a GraphQL query and extract data from the result

        Args:
            query: GraphQL query string
            variables: Variables for the query
            path: JMESPath expression to extract data from the result
            default: Default value if query fails or path not found

        Returns:
            Query result or extracted data
        """
        result = self.execute(query, variables)

        if not result:
            return default

        if path:
            try:
                from pyspider.libs.json_selector import JsonSelector
                json_selector = JsonSelector(json_data=result)
                return json_selector.jmespath(path, default)
            except Exception as e:
                logger.error(f"Error extracting data from GraphQL result: {e}")
                return default

        return result

    def extract_from_response(self, path: str = None, default: Any = None) -> Any:
        """
        Extract data from the response JSON

        Args:
            path: JMESPath expression to extract data
            default: Default value if path not found

        Returns:
            Extracted data
        """
        if not self._json_data:
            return default

        if path:
            try:
                from pyspider.libs.json_selector import JsonSelector
                json_selector = JsonSelector(json_data=self._json_data)
                return json_selector.jmespath(path, default)
            except Exception as e:
                logger.error(f"Error extracting data from GraphQL response: {e}")
                return default

        return self._json_data

    def introspect(self) -> Dict:
        """
        Perform GraphQL introspection query to get schema information

        Returns:
            Introspection data
        """
        if self._introspection_data:
            return self._introspection_data

        if not self.client:
            logger.error("GraphQL client not initialized")
            return {}

        introspection_query = """
        query IntrospectionQuery {
          __schema {
            queryType { name }
            mutationType { name }
            subscriptionType { name }
            types {
              ...FullType
            }
            directives {
              name
              description
              locations
              args {
                ...InputValue
              }
            }
          }
        }

        fragment FullType on __Type {
          kind
          name
          description
          fields(includeDeprecated: true) {
            name
            description
            args {
              ...InputValue
            }
            type {
              ...TypeRef
            }
            isDeprecated
            deprecationReason
          }
          inputFields {
            ...InputValue
          }
          interfaces {
            ...TypeRef
          }
          enumValues(includeDeprecated: true) {
            name
            description
            isDeprecated
            deprecationReason
          }
          possibleTypes {
            ...TypeRef
          }
        }

        fragment InputValue on __InputValue {
          name
          description
          type { ...TypeRef }
          defaultValue
        }

        fragment TypeRef on __Type {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
                ofType {
                  kind
                  name
                  ofType {
                    kind
                    name
                    ofType {
                      kind
                      name
                      ofType {
                        kind
                        name
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """

        try:
            self._introspection_data = self.execute(introspection_query)
            return self._introspection_data
        except Exception as e:
            logger.error(f"Error performing GraphQL introspection: {e}")
            return {}

    def get_type_info(self, type_name: str) -> Dict:
        """
        Get information about a specific type from the schema

        Args:
            type_name: Name of the type

        Returns:
            Type information
        """
        if not self._introspection_data:
            self.introspect()

        if not self._introspection_data:
            return {}

        try:
            types = self._introspection_data.get('__schema', {}).get('types', [])
            for type_info in types:
                if type_info.get('name') == type_name:
                    return type_info
            return {}
        except Exception as e:
            logger.error(f"Error getting type information: {e}")
            return {}

    def get_query_fields(self) -> List[str]:
        """
        Get available query fields from the schema

        Returns:
            List of query field names
        """
        if not self._introspection_data:
            self.introspect()

        if not self._introspection_data:
            return []

        try:
            query_type_name = self._introspection_data.get('__schema', {}).get('queryType', {}).get('name')
            if not query_type_name:
                return []

            query_type = self.get_type_info(query_type_name)
            if not query_type:
                return []

            fields = query_type.get('fields', [])
            return [field.get('name') for field in fields if field.get('name')]
        except Exception as e:
            logger.error(f"Error getting query fields: {e}")
            return []

    def format_query(self, query: str) -> str:
        """
        Format a GraphQL query string

        Args:
            query: GraphQL query string

        Returns:
            Formatted query string
        """
        try:
            ast = parse(query)
            return print_ast(ast)
        except Exception as e:
            logger.error(f"Error formatting GraphQL query: {e}")
            return query

    def build_query(self, operation_type: str, operation_name: str, fields: List[str], variables: Dict = None) -> str:
        """
        Build a GraphQL query string

        Args:
            operation_type: Operation type (query, mutation, subscription)
            operation_name: Operation name
            fields: Fields to include in the query
            variables: Variables for the query

        Returns:
            GraphQL query string
        """
        operation_type = operation_type.lower()
        if operation_type not in ('query', 'mutation', 'subscription'):
            logger.error(f"Invalid operation type: {operation_type}")
            return ""

        # Build variables declaration
        variables_decl = ""
        if variables:
            vars_list = []
            for name, var_type in variables.items():
                vars_list.append(f"${name}: {var_type}")
            if vars_list:
                variables_decl = f"({', '.join(vars_list)})"

        # Build fields string
        fields_str = "\n  ".join(fields)

        # Build query
        query = f"{operation_type} {operation_name}{variables_decl} {{\n  {fields_str}\n}}"

        return self.format_query(query)

    def suggest_query(self, entity_name: str, depth: int = 2) -> str:
        """
        Suggest a GraphQL query based on schema information

        Args:
            entity_name: Name of the entity to query
            depth: Maximum depth of nested fields

        Returns:
            Suggested GraphQL query string
        """
        if not self._introspection_data:
            self.introspect()

        if not self._introspection_data:
            return ""

        try:
            # Find the query field for the entity
            query_fields = self.get_query_fields()
            matching_fields = [field for field in query_fields if field.lower() == entity_name.lower()]

            if not matching_fields:
                # Try to find a similar field
                matching_fields = [field for field in query_fields if entity_name.lower() in field.lower()]

            if not matching_fields:
                logger.warning(f"No matching query field found for entity: {entity_name}")
                return ""

            entity_field = matching_fields[0]

            # Get the return type of the field
            query_type_name = self._introspection_data.get('__schema', {}).get('queryType', {}).get('name')
            query_type = self.get_type_info(query_type_name)

            if not query_type:
                return ""

            field_info = None
            for field in query_type.get('fields', []):
                if field.get('name') == entity_field:
                    field_info = field
                    break

            if not field_info:
                return ""

            # Get the return type
            return_type = field_info.get('type', {})
            while return_type.get('kind') in ('NON_NULL', 'LIST'):
                return_type = return_type.get('ofType', {})

            return_type_name = return_type.get('name')
            if not return_type_name:
                return ""

            # Get the fields of the return type
            return_type_info = self.get_type_info(return_type_name)
            if not return_type_info:
                return ""

            # Build the query
            fields = self._build_fields(return_type_info, depth, 1)

            # Check if the field has arguments
            args = field_info.get('args', [])
            variables_dict = {}
            args_str = ""

            if args:
                args_list = []
                for arg in args:
                    arg_name = arg.get('name')
                    arg_type = self._get_type_string(arg.get('type', {}))
                    if arg_name and arg_type:
                        variables_dict[arg_name] = arg_type
                        args_list.append(f"{arg_name}: ${arg_name}")

                if args_list:
                    args_str = f"({', '.join(args_list)})"

            query = f"query Get{entity_field.capitalize()}"
            if variables_dict:
                vars_list = [f"${name}: {var_type}" for name, var_type in variables_dict.items()]
                query += f"({', '.join(vars_list)})"

            query += f" {{\n  {entity_field}{args_str} {{\n{fields}\n  }}\n}}"

            return self.format_query(query)
        except Exception as e:
            logger.error(f"Error suggesting GraphQL query: {e}")
            return ""

    def _build_fields(self, type_info: Dict, max_depth: int, current_depth: int) -> str:
        """
        Build fields string for a type

        Args:
            type_info: Type information
            max_depth: Maximum depth of nested fields
            current_depth: Current depth

        Returns:
            Fields string
        """
        if current_depth > max_depth:
            return ""

        fields = type_info.get('fields', [])
        if not fields:
            return ""

        result = []
        indent = "  " * (current_depth + 1)

        for field in fields:
            field_name = field.get('name')
            if not field_name or field_name.startswith('__'):
                continue

            field_type = field.get('type', {})
            while field_type.get('kind') in ('NON_NULL', 'LIST'):
                field_type = field_type.get('ofType', {})

            if field_type.get('kind') == 'SCALAR':
                result.append(f"{indent}{field_name}")
            elif field_type.get('kind') in ('OBJECT', 'INTERFACE', 'UNION'):
                field_type_name = field_type.get('name')
                if field_type_name:
                    field_type_info = self.get_type_info(field_type_name)
                    if field_type_info:
                        nested_fields = self._build_fields(field_type_info, max_depth, current_depth + 1)
                        if nested_fields:
                            result.append(f"{indent}{field_name} {{\n{nested_fields}\n{indent}}}")
                        else:
                            result.append(f"{indent}{field_name}")
            else:
                result.append(f"{indent}{field_name}")

        return "\n".join(result)

    def _get_type_string(self, type_info: Dict) -> str:
        """
        Get string representation of a type

        Args:
            type_info: Type information

        Returns:
            Type string
        """
        if not type_info:
            return ""

        kind = type_info.get('kind')
        name = type_info.get('name')
        of_type = type_info.get('ofType')

        if kind == 'NON_NULL':
            return f"{self._get_type_string(of_type)}!"
        elif kind == 'LIST':
            return f"[{self._get_type_string(of_type)}]"
        elif name:
            return name
        else:
            return ""

    def get_subscription(self) -> GraphQLSubscription:
        """
        Get GraphQL subscription client

        Returns:
            GraphQLSubscription object
        """
        if not self._subscription and self._endpoint:
            self._subscription = GraphQLSubscription(
                endpoint=self._endpoint,
                headers=self._headers
            )
        return self._subscription

    def subscribe(self, query: str, variables: Dict[str, Any] = None,
                 callback: Callable[[Dict[str, Any]], None] = None) -> int:
        """
        Subscribe to a GraphQL subscription

        Args:
            query: GraphQL subscription query
            variables: Variables for the query
            callback: Callback function to handle received data

        Returns:
            Subscription ID
        """
        subscription = self.get_subscription()
        if not subscription:
            logger.error("GraphQL subscription client not initialized")
            return -1

        return subscription.subscribe_in_background(query, variables, callback)

    def unsubscribe(self, subscription_id: int) -> bool:
        """
        Unsubscribe from a GraphQL subscription

        Args:
            subscription_id: Subscription ID

        Returns:
            True if successful, False otherwise
        """
        subscription = self.get_subscription()
        if not subscription:
            logger.error("GraphQL subscription client not initialized")
            return False

        return subscription.unsubscribe_in_background(subscription_id)
