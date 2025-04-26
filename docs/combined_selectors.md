# Combined Selectors in PySpider

PySpider now includes powerful combined selector features that make it easier to extract and transform data from web pages and APIs. These features include:

1. **GraphQL Queries**: Extract data from GraphQL APIs
2. **XQuery Support**: Advanced XML querying with XQuery
3. **Selector Pipeline**: Combine and transform selector results
4. **Error Handling**: Improved error handling with suggestions

## 1. GraphQL Queries

GraphQL is a query language for APIs that allows clients to request exactly the data they need. PySpider now supports GraphQL queries through the `GraphQLSelector` class.

### Basic Usage

```python
# Using the response object directly
result = response.graphql("""
query {
  countries {
    name
    code
  }
}
""")

# Extract data from a specific path
countries = response.graphql("""
query {
  countries {
    name
    code
  }
}
""", path='countries')

# Using variables
result = response.graphql("""
query GetCountry($code: ID!) {
  country(code: $code) {
    name
    capital
  }
}
""", variables={'code': 'US'})
```

### Schema Introspection

You can introspect a GraphQL API to discover its schema:

```python
# Get schema information
schema = response.graphql_selector.introspect()

# Get available query fields
query_fields = response.graphql_selector.get_query_fields()

# Get information about a specific type
type_info = response.graphql_selector.get_type_info('Country')

# Suggest a query based on schema
suggested_query = response.graphql_selector.suggest_query('country')
```

## 2. XQuery Support

XQuery is a powerful query language for XML documents. PySpider now supports XQuery through the `XQuerySelector` class.

### Basic Usage

```python
# Using the response object directly
result = response.xquery('//book/title/text()')

# With namespaces
result = response.xquery('//ns:book/ns:title/text()', {'ns': 'http://example.com/ns'})

# Extract values
value = response.xquery_selector.extract_value('//book/title')
values = response.xquery_selector.extract_values('//book/title')

# Extract attributes
attr = response.xquery_selector.extract_attribute('//book', 'id')
attrs = response.xquery_selector.extract_attributes('//book', 'id')

# Extract XML
xml = response.xquery_selector.extract_xml('//book')
xmls = response.xquery_selector.extract_xmls('//book')
```

## 3. Selector Pipeline

The `SelectorPipeline` class allows you to combine multiple selectors and apply transformations to the results.

### Basic Usage

```python
# Extract with multiple selectors
title = response.pipeline([
    {'type': 'css', 'selector': 'h1', 'attr': 'text'},
    {'type': 'xpath', 'selector': '//h1/text()'},
    {'type': 'regex', 'pattern': '<h1>(.*?)</h1>'}
])

# Extract with transformers
title_transformed = response.pipeline([
    {'type': 'css', 'selector': 'h1', 'attr': 'text'}
], [
    {'name': 'strip'},
    {'name': 'upper'}
])

# Extract with fallbacks
description = response.extract_with_fallbacks([
    {'type': 'css', 'selector': 'meta[name="description"]', 'attr': 'content'},
    {'type': 'css', 'selector': 'p', 'attr': 'text'}
])
```

### Multiple Field Extraction

```python
data = response.extract_multiple({
    'fields': {
        'title': {
            'selectors': [
                {'type': 'css', 'selector': 'h1', 'attr': 'text'}
            ],
            'transformers': [
                {'name': 'strip'}
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
})
```

### Advanced Table Extraction

```python
table_data = response.extract_table_advanced({
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
    'skip_empty': True
})
```

### Advanced List Extraction

```python
list_data = response.extract_list_advanced({
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
    'skip_empty': True
})
```

## 4. Transformers

The selector pipeline supports a wide range of transformers to process and transform extracted data.

### String Transformers

- `strip`: Remove leading and trailing whitespace
- `lower`: Convert to lowercase
- `upper`: Convert to uppercase
- `title`: Convert to title case
- `capitalize`: Capitalize the first character
- `replace`: Replace a substring with another
- `regex_replace`: Replace using a regular expression
- `regex_extract`: Extract using a regular expression
- `split`: Split a string into a list
- `join`: Join a list into a string

### Type Conversion

- `int`: Convert to integer
- `float`: Convert to float
- `bool`: Convert to boolean
- `str`: Convert to string
- `list`: Convert to list
- `dict`: Convert to dictionary
- `json`: Parse JSON string

### Collection Operations

- `length`: Get the length of a collection
- `slice`: Get a slice of a collection
- `first`: Get the first item
- `last`: Get the last item
- `nth`: Get the nth item
- `filter`: Filter items using a function
- `map`: Apply a function to each item
- `sort`: Sort items
- `unique`: Get unique items
- `flatten`: Flatten nested lists

### Dictionary Operations

- `get`: Get a value from a dictionary
- `keys`: Get dictionary keys
- `values`: Get dictionary values
- `items`: Get dictionary items
- `update`: Update a dictionary
- `merge`: Merge dictionaries
- `dict_from_list`: Create a dictionary from a list

### Conditional Transformers

- `default`: Set a default value
- `if_none`: Replace if None
- `if_empty`: Replace if empty
- `if_true`: Return a value if condition is true
- `if_false`: Return a value if condition is false
- `if_equals`: Return a value if equal
- `if_not_equals`: Return a value if not equal
- `if_contains`: Return a value if contains
- `if_not_contains`: Return a value if not contains
- `if_matches`: Return a value if matches regex
- `if_not_matches`: Return a value if not matches regex

### Date and Time

- `format_date`: Parse a date string
- `format_datetime`: Parse a datetime string
- `date_to_string`: Format a date object
- `now`: Get current datetime
- `today`: Get current date
- `timestamp`: Convert to timestamp
- `from_timestamp`: Convert from timestamp

## 5. Error Handling

The `SelectorErrorHandler` class provides improved error handling for selectors, including detailed error messages, suggestions for fixing errors, and automatic error correction.

### Basic Usage

```python
try:
    result = response.css('h1.title')
except Exception as e:
    error = response.selector_error_handler.handle_error(e, 'h1.title', 'css')
    print(f"Error: {error}")
    print(f"Suggestions: {error.suggestions}")
    
    # Get auto-fixed selector
    fixed_selector, fixed_selector_type = response.selector_error_handler.auto_fix_selector('h1.title', 'css')
    print(f"Fixed selector: {fixed_selector}")
```

### Error Types

- `SelectorSyntaxError`: Error in selector syntax
- `SelectorNotFoundError`: No elements found for selector
- `SelectorTypeError`: Invalid selector type
- `SelectorAttributeError`: Error accessing attribute

## 6. WebUI Selector Tester

PySpider now includes a web-based selector tester that allows you to test selectors on web pages and see the results in real-time.

### Features

- Test different selector types (CSS, XPath, CSS4, RegEx, JSONPath, JMESPath, GraphQL, XQuery)
- Apply transformers to the results
- See detailed error messages and suggestions
- Save and load selectors
- View the HTML or JSON content

### Usage

1. Open the selector tester at `/selector_tester`
2. Enter a URL and click "Load URL"
3. Choose a selector type and enter a selector
4. Optionally add transformers
5. Click "Test Selector" to see the results

## Sample Project

A sample project demonstrating these features is available in `pyspider/sample_projects/combined_selectors.py`.

## Installation

To use these advanced selector features, you need to install additional dependencies:

```bash
pip install -r requirements-advanced-selectors.txt
```
