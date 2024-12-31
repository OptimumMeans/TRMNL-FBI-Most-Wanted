from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import os
import logging
import qrcode
import requests
import certifi
import traceback
import re
import base64
from datetime import datetime
from typing import Dict, Any, Optional
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

class DisplayGenerator:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        try:
            # Get the path to the DejaVu font in the assets directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            font_path = os.path.join(current_dir, '..', 'assets', 'DejaVuSans.ttf')
            
            logger.info(f'Loading font from: {font_path}')
            
            # Initialize fonts with DejaVu
            self.title_font = ImageFont.truetype(font=font_path, size=32)
            self.subtitle_font = ImageFont.truetype(font=font_path, size=16)
            self.name_font = ImageFont.truetype(font=font_path, size=24)
            self.heading_font = ImageFont.truetype(font=font_path, size=18)
            self.date_font = ImageFont.truetype(font=font_path, size=16)
            self.body_font = ImageFont.truetype(font=font_path, size=16)
            self.small_font = ImageFont.truetype(font=font_path, size=14)
        except Exception as e:
            logger.warning(f'Failed to load TrueType font: {e}')
            self.title_font = ImageFont.load_default()
            self.subtitle_font = self.title_font
            self.name_font = self.title_font
            self.heading_font = self.title_font
            self.date_font = self.title_font
            self.body_font = self.title_font
            self.small_font = self.title_font

    def create_display(self, data: Dict[str, Any]) -> Optional[bytes]:
        '''Create FBI Most Wanted display for TRMNL e-ink display.'''
        try:
            if not data or 'wanted_list' not in data:
                return self.create_error_display('No FBI data available')
            
            image = Image.new('1', (self.width, self.height), 1)  # White background
            draw = ImageDraw.Draw(image)
            
            # Draw header
            self._draw_header(draw, data)
            
            # Draw most wanted person
            if data['wanted_list']:
                self._draw_wanted_person(draw, data['wanted_list'][0], image)
            
            # Draw status bar
            self._draw_status_bar(draw, data)
            
            buffer = io.BytesIO()
            image.save(buffer, format='BMP')
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f'Error generating FBI display: {str(e)}')
            logger.error(traceback.format_exc())
            return self.create_error_display(str(e))
        
    def _generate_qr_code(self, url: str, size: int = 100) -> Image.Image:
        '''Generate QR code for FBI Most Wanted URL.'''
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=2,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        # Create QR code image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Resize to desired dimensions
        qr_image = qr_image.resize((size, size), Image.Resampling.NEAREST)
        return qr_image

    def _draw_header(self, draw: ImageDraw, data: Dict[str, Any]) -> None:
        '''Draw FBI Most Wanted header.'''
        # Draw main title in large font
        draw.text(
            (20, 15),
            'FBI MOST WANTED',
            font=self.title_font,
            fill=0
        )
        
        # Draw total count in smaller font
        draw.text(
            (20, 50),
            f"Total Wanted: {data.get('total_wanted', 0)}",
            font=self.subtitle_font,
            fill=0
        )

    def _draw_wanted_person(self, draw: ImageDraw, person: Dict[str, Any], image: Image) -> None:
        '''Draw wanted person information with photo.'''
        # Image dimensions
        right_margin = 20
        image_width = 200
        image_height = 240
        image_x = self.width - image_width - right_margin
        image_y = 80
        text_width = image_x - 40

        # Draw name/title in large bold font
        current_y = 80
        title_lines = self._wrap_text(person['title'], self.name_font, text_width)
        for line in title_lines:
            draw.text(
                (20, current_y),
                line,
                font=self.name_font,
                fill=0
            )
            current_y += 30  # More space between name lines

        # Draw location/date
        current_y += 5  # Small gap after name
        if person['description']:
            desc_parts = person['description'].split('\r\n')
            if len(desc_parts) >= 2:
                # Draw date and location on separate lines
                draw.text(
                    (20, current_y),
                    desc_parts[0],  # Date
                    font=self.date_font,
                    fill=0
                )
                current_y += 20
                draw.text(
                    (20, current_y),
                    desc_parts[1],  # Location
                    font=self.date_font,
                    fill=0
                )
                current_y += 25

        # Process and draw image
        if person['images']:
            wanted_image = self._fetch_image(person['images'])
            if wanted_image:
                wanted_image = wanted_image.convert('L')
                aspect_ratio = wanted_image.height / wanted_image.width
                target_width = image_width
                target_height = int(image_width * aspect_ratio)
                
                if target_height > image_height:
                    target_height = image_height
                    target_width = int(image_height / aspect_ratio)
                    image_x = self.width - target_width - right_margin
                
                wanted_image = wanted_image.resize((target_width, target_height), Image.Resampling.LANCZOS)
                wanted_image = wanted_image.convert('1', dither=Image.FLOYDSTEINBERG)
                image.paste(wanted_image, (image_x, image_y))
            else:
                self._draw_placeholder_image(image, image_x, image_width)

        # Draw details text
        details_text = ""
        if person['details']:
            details_text = re.sub('<[^<]+?>', '', person['details'])
        elif person['description']:
            details_text = person['description']

        if details_text:
            current_y += 15
            details_lines = self._wrap_text(details_text, self.body_font, text_width)
            max_lines = 6  # Limit number of lines to show
            
            # If we have more lines than we can display, add ellipsis
            if len(details_lines) > max_lines:
                for line in details_lines[:max_lines]:
                    draw.text(
                        (20, current_y),
                        line,
                        font=self.body_font,
                        fill=0
                    )
                    current_y += 22
                
                # Add ellipsis text
                draw.text(
                    (20, current_y),
                    "Want to read more? Scan the QR code below...",
                    font=self.body_font,
                    fill=0
                )
            else:
                # Show all lines if we have space
                for line in details_lines:
                    draw.text(
                        (20, current_y),
                        line,
                        font=self.body_font,
                        fill=0
                    )
                    current_y += 22
                
        # Calculate QR code position
        # Place it in bottom right, above status bar
        qr_size = 100
        qr_x = self.width - qr_size - 20  # 20px margin from right
        qr_y = self.height - qr_size - 50  # 50px up from bottom to clear status bar

        # Generate and paste QR code if URL is available
        if person.get('url'):
            qr_image = self._generate_qr_code(person['url'], qr_size)
            image.paste(qr_image, (qr_x, qr_y))
            
            # Add "Scan for details" text above QR code
            draw.text(
                (qr_x, qr_y - 20),
                "Scan for details",
                font=self.small_font,
                fill=0
            )

    def _draw_status_bar(self, draw: ImageDraw, data: Dict[str, Any]) -> None:
        '''Draw status bar at bottom of display.'''
        status_height = 30
        bar_y = self.height - status_height - 10
        
        # Draw black background for status bar
        draw.rectangle(
            [0, bar_y, self.width, bar_y + status_height],
            fill=0
        )
        
        # Format timestamp
        timestamp = data.get('timestamp', 'Unknown')
        if isinstance(timestamp, str):
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                timestamp = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
            except ValueError:
                pass
        
        # Draw timestamp in white text
        status_text = f'Last Update: {timestamp}'
        draw.text(
            (10, bar_y + 5),
            status_text,
            font=self.small_font,
            fill=1  # White text on black background
        )

    def _draw_placeholder_image(self, image: Image, x: int, width: int) -> None:
        '''Draw a placeholder when image cannot be loaded.'''
        placeholder = Image.new('L', (width, 200), 255)
        draw = ImageDraw.Draw(placeholder)
        draw.text(
            (width//2 - 50, 80),
            "Image\nNot Available",
            font=self.body_font,
            fill=0,
            align='center'
        )
        image.paste(placeholder, (x, 90))

    def _fetch_image(self, url: str) -> Optional[Image.Image]:
        '''Fetch image using image proxy service to bypass restrictions.'''
        try:
            # Encode the FBI URL for the proxy service
            encoded_url = urllib.parse.quote_plus(url)
            proxy_url = f'https://wsrv.nl/?url={encoded_url}'
            
            logger.info(f"Attempting to fetch image via proxy: {proxy_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
            }
            
            response = requests.get(proxy_url, headers=headers, timeout=15, verify=False)
            
            if response.status_code == 200:
                logger.info("Successfully fetched image via proxy")
                return Image.open(io.BytesIO(response.content))
            else:
                logger.warning(f"Proxy request failed with status code: {response.status_code}")
                
                # Try alternative proxy URL format
                alt_proxy_url = f'https://images.weserv.nl/?url={encoded_url}'
                logger.info(f"Attempting alternate proxy URL: {alt_proxy_url}")
                
                response = requests.get(alt_proxy_url, headers=headers, timeout=15, verify=False)
                
                if response.status_code == 200:
                    logger.info("Successfully fetched image via alternate proxy")
                    return Image.open(io.BytesIO(response.content))
                else:
                    logger.error(f"All proxy attempts failed. Final status code: {response.status_code}")
                    return None
                
        except Exception as e:
            logger.error(f"Error in image fetch process: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    def create_error_display(self, error_message: str) -> bytes:
        '''Create error display.'''
        image = Image.new('1', (self.width, self.height), 1)
        draw = ImageDraw.Draw(image)
        
        # Draw error header
        draw.text(
            (20, 20),
            'FBI Most Wanted - Error',
            font=self.title_font,
            fill=0
        )
        
        # Draw error message
        error_lines = self._wrap_text(error_message, self.body_font, self.width - 40)
        current_y = 60
        for line in error_lines:
            draw.text(
                (20, current_y),
                line,
                font=self.body_font,
                fill=0
            )
            current_y += 25
        
        buffer = io.BytesIO()
        image.save(buffer, format='BMP')
        return buffer.getvalue()

    def _wrap_text(self, text: str, font: ImageFont, max_width: int) -> list[str]:
        '''Wrap text to fit within specified width.'''
        if not text:
            return []
            
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            line_width = font.getlength(' '.join(current_line))
            if line_width > max_width:
                if len(current_line) == 1:
                    lines.append(current_line[0])
                    current_line = []
                else:
                    current_line.pop()
                    lines.append(' '.join(current_line))
                    current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines