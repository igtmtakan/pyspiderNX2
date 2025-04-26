# Advanced Selectors in PySpider

PySpider now includes advanced selector features that make it easier to extract data from web pages and JSON responses. These features include:

1. **JSONPath Selectors**: Extract data from JSON using JSONPath expressions
2. **JMESPath Selectors**: Extract data from JSON using JMESPath expressions
3. **CSS4 Selectors**: Use advanced CSS selectors with pseudo-classes and more

## 1. JSONPath Selectors

JSONPath is a query language for JSON, similar to XPath for XML. It allows you to extract data from JSON structures using path expressions.

### Basic Usage

```python
# Using the response object directly
first_title = response.jsonpath('$[0].title')
all_titles = response.jsonpaths('$[*].title')

# Using the advanced selector
first_title = response.advanced.jsonpath_first('$[0].title')
all_titles = response.advanced.jsonpath('$[*].title')
```

### Filtering

You can filter JSON data using JSONPath expressions:

```python
# Get titles of posts by user 1
filtered_posts = response.jsonpaths('$[?(@.userId==1)].title')
```

### Common JSONPath Syntax

| Syntax | Description |
|--------|-------------|
| `$` | Root object/element |
| `@` | Current object/element |
| `.` | Child operator |
| `..` | Recursive descent |
| `*` | Wildcard for all objects/elements |
| `[n]` | Array index |
| `[start:end:step]` | Array slice |
| `[?(<expression>)]` | Filter expression |
| `(<expression>)` | Script expression |

## 2. JMESPath Selectors

JMESPath is a query language for JSON that is used by AWS CLI and other tools. It provides a more concise syntax for querying JSON data.

### Basic Usage

```python
# Using the response object directly
first_title = response.jmespath('[0].title')

# Using the advanced selector
first_title = response.advanced.jmespath('[0].title')
```

### Filtering

You can filter JSON data using JMESPath expressions:

```python
# Get titles of posts by user 1
filtered_posts = response.jmespath("[?userId==`1`].title")
```

### Projections

You can project specific fields from JSON data:

```python
# Get all titles
titles = response.jmespath('[*].title')

# Get user IDs and titles
user_titles = response.jmespath('[*].{user: userId, title: title}')
```

### Common JMESPath Syntax

| Syntax | Description |
|--------|-------------|
| `foo.bar` | Dot notation for nested elements |
| `foo[0]` | Array index |
| `[*]` | List wildcard |
| `[?expression]` | Filter expression |
| `{key1: value1, key2: value2}` | Multiselect hash |
| `[key1, key2]` | Multiselect list |
| `@` | Current node |
| `||` | Or expression |

## 3. CSS4 Selectors

CSS4 selectors provide advanced CSS selection capabilities, including pseudo-classes and complex selectors.

### Basic Usage

```python
# Using the response object directly
first_p = response.css4('p:first-of-type')
all_ps = response.css4s('p:not(:first-child)')

# Using the advanced selector
first_p = response.advanced.css4_first('p:first-of-type')
all_ps = response.advanced.css4('p:not(:first-child)')
```

### Pseudo-Classes

CSS4 supports a wide range of pseudo-classes:

```python
# First element of its type
first_element = response.css4('p:first-of-type')

# Last element of its type
last_element = response.css4('p:last-of-type')

# Nth element
nth_element = response.css4('p:nth-child(2)')

# Elements not matching a selector
not_elements = response.css4('p:not(.special)')
```

### Attribute Selectors

CSS4 supports advanced attribute selectors:

```python
# Elements with an attribute
elements_with_attr = response.css4s('a[rel]')

# Elements with attribute equal to value
elements_with_value = response.css4s('a[rel="nofollow"]')

# Elements with attribute containing value
elements_containing = response.css4s('a[href*="example"]')

# Elements with attribute starting with value
elements_starting = response.css4s('a[href^="https"]')

# Elements with attribute ending with value
elements_ending = response.css4s('a[href$=".pdf"]')
```

### Combinators

CSS4 supports various combinators:

```python
# Direct children
direct_children = response.css4s('div > p')

# Descendants
descendants = response.css4s('div p')

# Adjacent siblings
adjacent = response.css4s('h1 + p')

# General siblings
siblings = response.css4s('h1 ~ p')
```

## 4. Combined Selectors

You can combine different selector types to extract data more flexibly:

```python
# Try multiple selectors in order until one succeeds
title = response.advanced.select([
    {'type': 'css4', 'selector': 'h1:first-child', 'attr': 'text'},
    {'type': 'css', 'selector': 'h1', 'attr': 'text'},
    {'type': 'xpath', 'selector': '//h1/text()'},
    {'type': 'regex', 'pattern': '<h1>(.*?)</h1>'},
    {'type': 'jsonpath', 'path': '$.title'},
    {'type': 'jmespath', 'path': 'title'}
])
```

## 5. Advanced JSON Processing

The JSON selector provides additional methods for processing JSON data:

```python
# Extract keys from a JSON object
keys = response.advanced.json_selector.extract_keys('$[0]')

# Extract values for a specific key
all_ids = response.advanced.json_selector.extract_values('id')

# Flatten nested JSON
flattened = response.advanced.json_selector.flatten('$[0:2]')

# Convert to JSON string
json_string = response.advanced.json_selector.to_json_string(indent=2)
```

## Sample Project

A sample project demonstrating these features is available in `pyspider/sample_projects/advanced_selectors.py`.

## Installation

To use these advanced selector features, you need to install additional dependencies:

```bash
pip install -r requirements-selectors.txt
```
