# PhantomJS to Puppeteer Migration Guide

## Overview

As of version 0.5.0, PySpider has removed PhantomJS support and replaced it with Puppeteer. This document provides guidance on migrating your existing code from PhantomJS to Puppeteer.

## Why the Change?

PhantomJS development has been [officially suspended](https://github.com/ariya/phantomjs/issues/15344) since March 2018. It is no longer maintained and has several security vulnerabilities and compatibility issues with modern web standards.

Puppeteer offers several advantages:
- Based on modern Chromium engine
- Actively maintained by Google
- Better performance and stability
- Support for modern web standards
- Better JavaScript execution

## Migration Steps

### 1. Update Your Fetch Type

Change your `fetch_type` from `'js'` or `'phantomjs'` to `'puppeteer'`:

```python
# Old code
self.crawl('http://example.com', 
           fetch_type='js',  # or 'phantomjs'
           callback=self.index_page)

# New code
self.crawl('http://example.com', 
           fetch_type='puppeteer',
           callback=self.index_page)
```

### 2. JavaScript Execution

The JavaScript execution API remains compatible. You can continue to use the same parameters:

```python
self.crawl('http://example.com',
           fetch_type='puppeteer',
           js_script='function() { window.scrollTo(0, document.body.scrollHeight); }',
           js_run_at='document-end',
           callback=self.index_page)
```

### 3. Configuration

Update your configuration to remove any PhantomJS-specific settings and add Puppeteer settings if needed:

```json
{
    "puppeteer": {
        "port": 22222,
        "auto_restart": true
    }
}
```

### 4. Compatibility Mode

For backward compatibility, PySpider automatically redirects requests with `fetch_type='js'` or `fetch_type='phantomjs'` to Puppeteer. However, this compatibility mode may be removed in future versions, so it's recommended to update your code.

When using the compatibility mode, you'll see a warning message in the logs:

```
WARNING: PhantomJS is deprecated and will be removed in future versions. Your request with fetch_type='js' has been redirected to puppeteer. Please update your code to use fetch_type='puppeteer' directly.
```

## Puppeteer-Specific Features

Puppeteer offers some additional features not available in PhantomJS:

### 1. Screenshots

```python
self.crawl('http://example.com',
           fetch_type='puppeteer',
           screenshot_path='/path/to/screenshot.png',
           callback=self.index_page)
```

### 2. PDF Generation

```python
self.crawl('http://example.com',
           fetch_type='puppeteer',
           pdf_path='/path/to/output.pdf',
           callback=self.index_page)
```

### 3. Mobile Emulation

```python
self.crawl('http://example.com',
           fetch_type='puppeteer',
           mobile=True,
           callback=self.index_page)
```

## Troubleshooting

If you encounter issues after migrating from PhantomJS to Puppeteer:

1. Make sure Node.js is installed and accessible
2. Check that Puppeteer is properly installed (`npm install puppeteer`)
3. Verify that the Puppeteer fetcher is running (`node fetcher/puppeteer_fetcher.js`)
4. Check the logs for any error messages

For more detailed information, refer to the [Puppeteer documentation](https://pptr.dev/).
