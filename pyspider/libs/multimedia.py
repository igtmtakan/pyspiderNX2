#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-25 17:00:00

import os
import re
import time
import json
import hashlib
import logging
import mimetypes
import threading
import concurrent.futures
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Union, Optional, Any, Tuple, Callable
import requests
from PIL import Image
from io import BytesIO

logger = logging.getLogger('multimedia')

class MultimediaProcessor:
    """
    Process multimedia files (images, videos, audio) from web pages
    """
    
    def __init__(self, response=None, html=None, url=None, download_path=None, max_workers=5):
        """
        Initialize the processor with response or HTML content
        
        Args:
            response: PySpider response object
            html: HTML content as string
            url: URL for making links absolute
            download_path: Path to download files
            max_workers: Maximum number of concurrent downloads
        """
        self.response = response
        self._html = html
        self._url = url
        self._doc = None
        self.download_path = download_path or os.path.join(os.getcwd(), 'downloads')
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.lock = threading.RLock()
        
        # Create download directory if it doesn't exist
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
        
        if response:
            self._html = response.content
            self._url = response.url
            self._doc = response.doc
        elif html and url:
            from pyquery import PyQuery
            self._doc = PyQuery(html)
            self._doc.make_links_absolute(url)
    
    def extract_images(self, min_size: Tuple[int, int] = None, max_size: Tuple[int, int] = None) -> List[Dict]:
        """
        Extract image information from HTML
        
        Args:
            min_size: Minimum image size (width, height)
            max_size: Maximum image size (width, height)
            
        Returns:
            List of image information
        """
        if not self._doc:
            return []
        
        result = []
        
        try:
            # Find all img tags
            img_tags = self._doc('img')
            
            for img in img_tags:
                img = self._doc(img)
                src = img.attr('src')
                if not src:
                    continue
                
                # Make URL absolute
                if self._url:
                    src = urljoin(self._url, src)
                
                # Skip data URLs
                if src.startswith('data:'):
                    continue
                
                # Get image information
                alt = img.attr('alt') or ''
                title = img.attr('title') or ''
                width = img.attr('width')
                height = img.attr('height')
                
                # Convert width and height to integers if possible
                try:
                    width = int(width) if width else None
                    height = int(height) if height else None
                except ValueError:
                    width = None
                    height = None
                
                # Skip images that don't meet size requirements
                if min_size and width and height:
                    if width < min_size[0] or height < min_size[1]:
                        continue
                
                if max_size and width and height:
                    if width > max_size[0] or height > max_size[1]:
                        continue
                
                # Get image filename
                filename = os.path.basename(urlparse(src).path)
                if not filename:
                    filename = f"image_{len(result) + 1}.jpg"
                
                # Add image information to result
                result.append({
                    'url': src,
                    'alt': alt,
                    'title': title,
                    'width': width,
                    'height': height,
                    'filename': filename
                })
        except Exception as e:
            logger.error(f"Error extracting images: {e}")
        
        return result
    
    def extract_videos(self) -> List[Dict]:
        """
        Extract video information from HTML
        
        Returns:
            List of video information
        """
        if not self._doc:
            return []
        
        result = []
        
        try:
            # Find all video tags
            video_tags = self._doc('video')
            
            for video in video_tags:
                video = self._doc(video)
                src = video.attr('src')
                
                # If video tag has no src, check for source tags
                if not src:
                    source_tags = video.find('source')
                    if source_tags:
                        src = self._doc(source_tags[0]).attr('src')
                
                if not src:
                    continue
                
                # Make URL absolute
                if self._url:
                    src = urljoin(self._url, src)
                
                # Get video information
                width = video.attr('width')
                height = video.attr('height')
                poster = video.attr('poster')
                
                # Convert width and height to integers if possible
                try:
                    width = int(width) if width else None
                    height = int(height) if height else None
                except ValueError:
                    width = None
                    height = None
                
                # Make poster URL absolute
                if poster and self._url:
                    poster = urljoin(self._url, poster)
                
                # Get video filename
                filename = os.path.basename(urlparse(src).path)
                if not filename:
                    filename = f"video_{len(result) + 1}.mp4"
                
                # Add video information to result
                result.append({
                    'url': src,
                    'width': width,
                    'height': height,
                    'poster': poster,
                    'filename': filename
                })
            
            # Find all iframe tags that might contain videos
            iframe_tags = self._doc('iframe')
            
            for iframe in iframe_tags:
                iframe = self._doc(iframe)
                src = iframe.attr('src')
                if not src:
                    continue
                
                # Make URL absolute
                if self._url:
                    src = urljoin(self._url, src)
                
                # Check if iframe is from a video platform
                video_platforms = [
                    ('youtube.com/embed/', 'YouTube'),
                    ('player.vimeo.com/video/', 'Vimeo'),
                    ('dailymotion.com/embed/video/', 'Dailymotion'),
                    ('facebook.com/plugins/video.php', 'Facebook')
                ]
                
                platform = None
                for platform_url, platform_name in video_platforms:
                    if platform_url in src:
                        platform = platform_name
                        break
                
                if not platform:
                    continue
                
                # Get iframe dimensions
                width = iframe.attr('width')
                height = iframe.attr('height')
                
                # Convert width and height to integers if possible
                try:
                    width = int(width) if width else None
                    height = int(height) if height else None
                except ValueError:
                    width = None
                    height = None
                
                # Add iframe information to result
                result.append({
                    'url': src,
                    'width': width,
                    'height': height,
                    'platform': platform,
                    'type': 'iframe'
                })
        except Exception as e:
            logger.error(f"Error extracting videos: {e}")
        
        return result
    
    def extract_audio(self) -> List[Dict]:
        """
        Extract audio information from HTML
        
        Returns:
            List of audio information
        """
        if not self._doc:
            return []
        
        result = []
        
        try:
            # Find all audio tags
            audio_tags = self._doc('audio')
            
            for audio in audio_tags:
                audio = self._doc(audio)
                src = audio.attr('src')
                
                # If audio tag has no src, check for source tags
                if not src:
                    source_tags = audio.find('source')
                    if source_tags:
                        src = self._doc(source_tags[0]).attr('src')
                
                if not src:
                    continue
                
                # Make URL absolute
                if self._url:
                    src = urljoin(self._url, src)
                
                # Get audio filename
                filename = os.path.basename(urlparse(src).path)
                if not filename:
                    filename = f"audio_{len(result) + 1}.mp3"
                
                # Add audio information to result
                result.append({
                    'url': src,
                    'filename': filename
                })
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
        
        return result
    
    def download_file(self, url: str, filename: str = None, directory: str = None) -> Optional[str]:
        """
        Download a file from URL
        
        Args:
            url: URL to download
            filename: Filename to save as, None for auto-generated
            directory: Directory to save in, None for default
            
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            # Generate filename if not provided
            if not filename:
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path)
                if not filename:
                    # Generate filename from URL hash
                    url_hash = hashlib.md5(url.encode()).hexdigest()
                    
                    # Try to determine file extension from content type
                    response = self.session.head(url, allow_redirects=True)
                    content_type = response.headers.get('Content-Type', '')
                    extension = mimetypes.guess_extension(content_type.split(';')[0].strip())
                    
                    if not extension:
                        # Default extension based on content type
                        if 'image' in content_type:
                            extension = '.jpg'
                        elif 'video' in content_type:
                            extension = '.mp4'
                        elif 'audio' in content_type:
                            extension = '.mp3'
                        else:
                            extension = '.bin'
                    
                    filename = f"{url_hash}{extension}"
            
            # Use default directory if not provided
            if not directory:
                directory = self.download_path
            
            # Create directory if it doesn't exist
            if not os.path.exists(directory):
                os.makedirs(directory)
            
            # Full path to save file
            file_path = os.path.join(directory, filename)
            
            # Skip if file already exists
            if os.path.exists(file_path):
                logger.info(f"File already exists: {file_path}")
                return file_path
            
            # Download file
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            # Save file
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Downloaded file: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error downloading file from {url}: {e}")
            return None
    
    def download_images(self, images: List[Dict] = None, min_size: Tuple[int, int] = None, max_size: Tuple[int, int] = None) -> List[Dict]:
        """
        Download images from HTML
        
        Args:
            images: List of image information, None to extract from HTML
            min_size: Minimum image size (width, height)
            max_size: Maximum image size (width, height)
            
        Returns:
            List of downloaded image information
        """
        if not images:
            images = self.extract_images(min_size, max_size)
        
        result = []
        
        # Create image directory
        image_dir = os.path.join(self.download_path, 'images')
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)
        
        # Download images in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_image = {
                executor.submit(self.download_file, image['url'], image['filename'], image_dir): image
                for image in images
            }
            
            for future in concurrent.futures.as_completed(future_to_image):
                image = future_to_image[future]
                try:
                    file_path = future.result()
                    if file_path:
                        # Get image dimensions
                        try:
                            with Image.open(file_path) as img:
                                width, height = img.size
                                image['width'] = width
                                image['height'] = height
                                image['format'] = img.format
                        except Exception as e:
                            logger.warning(f"Error getting image dimensions: {e}")
                        
                        image['file_path'] = file_path
                        result.append(image)
                except Exception as e:
                    logger.error(f"Error downloading image {image['url']}: {e}")
        
        return result
    
    def download_videos(self, videos: List[Dict] = None) -> List[Dict]:
        """
        Download videos from HTML
        
        Args:
            videos: List of video information, None to extract from HTML
            
        Returns:
            List of downloaded video information
        """
        if not videos:
            videos = self.extract_videos()
        
        result = []
        
        # Create video directory
        video_dir = os.path.join(self.download_path, 'videos')
        if not os.path.exists(video_dir):
            os.makedirs(video_dir)
        
        # Download videos in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_video = {}
            
            for video in videos:
                # Skip iframe videos
                if video.get('type') == 'iframe':
                    result.append(video)
                    continue
                
                future = executor.submit(self.download_file, video['url'], video['filename'], video_dir)
                future_to_video[future] = video
                
                # Download poster image if available
                if video.get('poster'):
                    poster_filename = f"poster_{video['filename']}.jpg"
                    poster_future = executor.submit(self.download_file, video['poster'], poster_filename, video_dir)
                    future_to_video[poster_future] = {'url': video['poster'], 'is_poster': True, 'video': video}
            
            for future in concurrent.futures.as_completed(future_to_video):
                item = future_to_video[future]
                try:
                    file_path = future.result()
                    if file_path:
                        if item.get('is_poster'):
                            item['video']['poster_path'] = file_path
                        else:
                            item['file_path'] = file_path
                            result.append(item)
                except Exception as e:
                    logger.error(f"Error downloading video {item['url']}: {e}")
        
        return result
    
    def download_audio(self, audio_files: List[Dict] = None) -> List[Dict]:
        """
        Download audio files from HTML
        
        Args:
            audio_files: List of audio information, None to extract from HTML
            
        Returns:
            List of downloaded audio information
        """
        if not audio_files:
            audio_files = self.extract_audio()
        
        result = []
        
        # Create audio directory
        audio_dir = os.path.join(self.download_path, 'audio')
        if not os.path.exists(audio_dir):
            os.makedirs(audio_dir)
        
        # Download audio files in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_audio = {
                executor.submit(self.download_file, audio['url'], audio['filename'], audio_dir): audio
                for audio in audio_files
            }
            
            for future in concurrent.futures.as_completed(future_to_audio):
                audio = future_to_audio[future]
                try:
                    file_path = future.result()
                    if file_path:
                        audio['file_path'] = file_path
                        result.append(audio)
                except Exception as e:
                    logger.error(f"Error downloading audio {audio['url']}: {e}")
        
        return result
    
    def download_all(self, min_image_size: Tuple[int, int] = None, max_image_size: Tuple[int, int] = None) -> Dict[str, List[Dict]]:
        """
        Download all multimedia files from HTML
        
        Args:
            min_image_size: Minimum image size (width, height)
            max_image_size: Maximum image size (width, height)
            
        Returns:
            Dictionary with downloaded file information by type
        """
        result = {
            'images': self.download_images(min_size=min_image_size, max_size=max_image_size),
            'videos': self.download_videos(),
            'audio': self.download_audio()
        }
        
        return result
