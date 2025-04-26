# Advanced Data Extraction in PySpider

PySpider now includes advanced data extraction features that make it easier to extract data from web pages. These features include:

1. **Advanced Selectors**: Combine XPath, CSS, and RegEx selectors for more flexible data extraction
2. **Structured Data Extraction**: Extract structured data like JSON-LD, Microdata, and RDFa
3. **Multimedia Processing**: Extract and download images, videos, and audio files

## 1. Advanced Selectors

The `AdvancedSelector` class provides a unified interface for using XPath, CSS, and RegEx selectors.

### Basic Usage

```python
# Using the response object directly
title = response.xpath('//h1/text()')
links = response.csss('a', 'href')
pattern = response.regex(r'<h1>(.*?)</h1>')

# Using the advanced selector
title = response.advanced.xpath_first('//h1/text()')
links = response.advanced.css('a', 'href')
pattern = response.advanced.regex_first(r'<h1>(.*?)</h1>')
```

### Combined Selectors

You can try multiple selectors in order until one succeeds:

```python
title = response.advanced.select([
    {'type': 'css', 'selector': 'h1', 'attr': 'text'},
    {'type': 'xpath', 'selector': '//h1/text()'},
    {'type': 'regex', 'pattern': '<h1>(.*?)</h1>'}
])
```

### Table Extraction

Extract data from HTML tables:

```python
table_data = response.extract_table('table')
```

### List Extraction

Extract data from HTML lists:

```python
list_data = response.extract_list('ul', 'li')
```

## 2. Structured Data Extraction

The `StructuredDataExtractor` class provides methods for extracting structured data from web pages.

### JSON-LD Extraction

```python
json_ld = response.structured_data.extract_json_ld()
```

### Microdata Extraction

```python
microdata = response.structured_data.extract_microdata()
```

### RDFa Extraction

```python
rdfa = response.structured_data.extract_rdfa()
```

### Open Graph Extraction

```python
opengraph = response.structured_data.extract_opengraph()
```

### Twitter Cards Extraction

```python
twitter_cards = response.structured_data.extract_twitter_cards()
```

### All Structured Data

Extract all types of structured data at once:

```python
all_structured_data = response.structured_data.extract_all()
```

## 3. Multimedia Processing

The `MultimediaProcessor` class provides methods for extracting and downloading multimedia files.

### Image Extraction

```python
images = response.multimedia.extract_images()
```

### Video Extraction

```python
videos = response.multimedia.extract_videos()
```

### Audio Extraction

```python
audio = response.multimedia.extract_audio()
```

### Downloading Multimedia Files

```python
# Download images
downloaded_images = response.multimedia.download_images()

# Download videos
downloaded_videos = response.multimedia.download_videos()

# Download audio files
downloaded_audio = response.multimedia.download_audio()

# Download all multimedia files
downloaded_all = response.multimedia.download_all()
```

## Sample Project

A sample project demonstrating these features is available in `pyspider/sample_projects/advanced_extraction.py`.

## Installation

To use the multimedia processing features, you need to install additional dependencies:

```bash
pip install -r requirements-multimedia.txt
```
