#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-28 16:00:00

"""
Custom transformer functions for SelectorPipeline
"""

import re
import json
import html
import base64
import hashlib
import urllib.parse
from datetime import datetime, timedelta

# String transformers

def slugify(text):
    """Convert text to slug format (lowercase, hyphens instead of spaces, alphanumeric only)"""
    if not isinstance(text, str):
        return text
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace spaces with hyphens
    text = re.sub(r'\s+', '-', text)
    
    # Remove non-alphanumeric characters
    text = re.sub(r'[^a-z0-9-]', '', text)
    
    # Remove duplicate hyphens
    text = re.sub(r'-+', '-', text)
    
    # Remove leading and trailing hyphens
    text = text.strip('-')
    
    return text

def truncate(text, length=100, suffix='...'):
    """Truncate text to a specified length"""
    if not isinstance(text, str):
        return text
    
    if len(text) <= length:
        return text
    
    return text[:length].rsplit(' ', 1)[0] + suffix

def extract_numbers(text):
    """Extract all numbers from text"""
    if not isinstance(text, str):
        return text
    
    return [float(x) if '.' in x else int(x) for x in re.findall(r'\d+(?:\.\d+)?', text)]

def extract_first_number(text):
    """Extract first number from text"""
    if not isinstance(text, str):
        return text
    
    numbers = extract_numbers(text)
    return numbers[0] if numbers else None

def extract_emails(text):
    """Extract all email addresses from text"""
    if not isinstance(text, str):
        return text
    
    return re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)

def extract_urls(text):
    """Extract all URLs from text"""
    if not isinstance(text, str):
        return text
    
    return re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?:/[-\w%!$&\'()*+,;=:@/~]+)*(?:\?[-\w%!$&\'()*+,;=:@/~]*)?(?:#[-\w%!$&\'()*+,;=:@/~]*)?', text)

def html_to_text(html_content):
    """Convert HTML to plain text"""
    if not isinstance(html_content, str):
        return html_content
    
    # Remove script and style tags
    html_content = re.sub(r'<script.*?>.*?</script>', '', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<style.*?>.*?</style>', '', html_content, flags=re.DOTALL)
    
    # Replace <br> with newlines
    html_content = re.sub(r'<br\s*/?>|<p\s*/?>', '\n', html_content)
    
    # Remove all other tags
    html_content = re.sub(r'<[^>]*>', '', html_content)
    
    # Decode HTML entities
    html_content = html.unescape(html_content)
    
    # Remove extra whitespace
    html_content = re.sub(r'\s+', ' ', html_content).strip()
    
    return html_content

def normalize_whitespace(text):
    """Normalize whitespace in text (replace multiple whitespace with single space)"""
    if not isinstance(text, str):
        return text
    
    return re.sub(r'\s+', ' ', text).strip()

# Encoding/decoding transformers

def base64_encode(data):
    """Encode data as base64"""
    if isinstance(data, str):
        return base64.b64encode(data.encode('utf-8')).decode('utf-8')
    elif isinstance(data, bytes):
        return base64.b64encode(data).decode('utf-8')
    else:
        return data

def base64_decode(data):
    """Decode base64 data"""
    if not isinstance(data, str):
        return data
    
    try:
        return base64.b64decode(data).decode('utf-8')
    except:
        return data

def url_encode(text):
    """URL encode text"""
    if not isinstance(text, str):
        return text
    
    return urllib.parse.quote(text)

def url_decode(text):
    """URL decode text"""
    if not isinstance(text, str):
        return text
    
    return urllib.parse.unquote(text)

# Hash transformers

def md5(text):
    """Calculate MD5 hash of text"""
    if not isinstance(text, str):
        return text
    
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def sha1(text):
    """Calculate SHA1 hash of text"""
    if not isinstance(text, str):
        return text
    
    return hashlib.sha1(text.encode('utf-8')).hexdigest()

def sha256(text):
    """Calculate SHA256 hash of text"""
    if not isinstance(text, str):
        return text
    
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

# Date transformers

def parse_relative_date(text):
    """Parse relative date (e.g. '2 days ago', 'yesterday')"""
    if not isinstance(text, str):
        return text
    
    text = text.lower()
    now = datetime.now()
    
    if 'today' in text:
        return now.date()
    elif 'yesterday' in text:
        return (now - timedelta(days=1)).date()
    
    # Match patterns like "2 days ago", "3 weeks ago", etc.
    match = re.search(r'(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago', text)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        
        if unit == 'second':
            return now - timedelta(seconds=amount)
        elif unit == 'minute':
            return now - timedelta(minutes=amount)
        elif unit == 'hour':
            return now - timedelta(hours=amount)
        elif unit == 'day':
            return now - timedelta(days=amount)
        elif unit == 'week':
            return now - timedelta(weeks=amount)
        elif unit == 'month':
            return now - timedelta(days=amount*30)  # Approximate
        elif unit == 'year':
            return now - timedelta(days=amount*365)  # Approximate
    
    return text

def format_iso_date(date_obj):
    """Format date as ISO 8601 string"""
    if isinstance(date_obj, datetime):
        return date_obj.isoformat()
    elif isinstance(date_obj, str):
        try:
            return datetime.fromisoformat(date_obj).isoformat()
        except:
            return date_obj
    else:
        return date_obj

def humanize_date(date_obj):
    """Format date in human-readable format"""
    if not isinstance(date_obj, (datetime, str)):
        return date_obj
    
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.fromisoformat(date_obj)
        except:
            return date_obj
    
    now = datetime.now()
    diff = now - date_obj
    
    if diff.days < 0:
        return date_obj.strftime('%Y-%m-%d %H:%M:%S')
    elif diff.days == 0:
        if diff.seconds < 60:
            return 'just now'
        elif diff.seconds < 3600:
            return f'{diff.seconds // 60} minutes ago'
        else:
            return f'{diff.seconds // 3600} hours ago'
    elif diff.days == 1:
        return 'yesterday'
    elif diff.days < 7:
        return f'{diff.days} days ago'
    elif diff.days < 30:
        return f'{diff.days // 7} weeks ago'
    elif diff.days < 365:
        return f'{diff.days // 30} months ago'
    else:
        return f'{diff.days // 365} years ago'

# Currency transformers

def extract_price(text):
    """Extract price from text"""
    if not isinstance(text, str):
        return text
    
    # Match common price formats
    match = re.search(r'(?:[$€£¥])\s*(\d+(?:[.,]\d+)?)|(\d+(?:[.,]\d+)?)\s*(?:[$€£¥])', text)
    if match:
        price_str = match.group(1) or match.group(2)
        price_str = price_str.replace(',', '.')
        return float(price_str)
    
    return None

def format_price(price, currency='$', decimals=2):
    """Format price with currency symbol"""
    if not isinstance(price, (int, float)):
        return price
    
    return f"{currency}{price:.{decimals}f}"

# Geolocation transformers

def extract_coordinates(text):
    """Extract latitude and longitude from text"""
    if not isinstance(text, str):
        return text
    
    # Match common coordinate formats
    match = re.search(r'(-?\d+(?:\.\d+)?)[,\s]+(-?\d+(?:\.\d+)?)', text)
    if match:
        lat = float(match.group(1))
        lng = float(match.group(2))
        return {'lat': lat, 'lng': lng}
    
    return None

# List transformers

def filter_empty(items):
    """Filter out empty items from a list"""
    if not isinstance(items, list):
        return items
    
    return [item for item in items if item]

def filter_duplicates(items):
    """Filter out duplicate items from a list while preserving order"""
    if not isinstance(items, list):
        return items
    
    seen = set()
    result = []
    
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    
    return result

def group_by(items, key):
    """Group list items by a key"""
    if not isinstance(items, list):
        return items
    
    result = {}
    
    for item in items:
        if isinstance(item, dict) and key in item:
            group_key = item[key]
            if group_key not in result:
                result[group_key] = []
            result[group_key].append(item)
    
    return result

# Dictionary transformers

def pick(obj, keys):
    """Pick specified keys from a dictionary"""
    if not isinstance(obj, dict):
        return obj
    
    if isinstance(keys, str):
        keys = [keys]
    
    return {k: obj[k] for k in keys if k in obj}

def omit(obj, keys):
    """Omit specified keys from a dictionary"""
    if not isinstance(obj, dict):
        return obj
    
    if isinstance(keys, str):
        keys = [keys]
    
    return {k: v for k, v in obj.items() if k not in keys}

def rename_keys(obj, key_map):
    """Rename keys in a dictionary"""
    if not isinstance(obj, dict):
        return obj
    
    result = {}
    
    for k, v in obj.items():
        if k in key_map:
            result[key_map[k]] = v
        else:
            result[k] = v
    
    return result

def flatten_dict(obj, separator='.'):
    """Flatten a nested dictionary"""
    if not isinstance(obj, dict):
        return obj
    
    result = {}
    
    def _flatten(d, parent_key=''):
        for k, v in d.items():
            key = f"{parent_key}{separator}{k}" if parent_key else k
            
            if isinstance(v, dict):
                _flatten(v, key)
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        _flatten(item, f"{key}[{i}]")
                    else:
                        result[f"{key}[{i}]"] = item
            else:
                result[key] = v
    
    _flatten(obj)
    return result
