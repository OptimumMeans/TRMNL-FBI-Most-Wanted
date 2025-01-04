from PIL import Image, ImageDraw, ImageFont
import io
import os
import logging
import qrcode
import requests
import traceback
import re
from datetime import datetime
from typing import Dict, Any, Optional
import urllib.parse

logger = logging.getLogger(__name__)

class DisplayGenerator:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            font_path = os.path.join(current_dir, '..', 'assets', 'DejaVuSans.ttf')
            
            logger.info(f'Loading font from: {font_path}')
            
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
        try:
            if not data or 'wanted_list' not in data:
                return self.create_error_display('No FBI data available')
            
            image = Image.new('1', (self.width, self.height), 1)# White background
            draw = ImageDraw.Draw(image)
            
            self._draw_header(draw, data)
            
            if data['wanted_list']:
                self._draw_wanted_person(draw, data['wanted_list'][0], image)
            
            self._draw_status_bar(draw, data)
            
            buffer = io.BytesIO()
            image.save(buffer, format='BMP')
            return buffer.getvalue()
        except Exception as e:
            logger.error(f'Error generating FBI display: {str(e)}')
            logger.error(traceback.format_exc())
            return self.create_error_display(str(e))

    def _wrap_text(self, text: str, font: ImageFont, max_width: int) -> list[str]:
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
        
    def _generate_qr_code(self, url: str, size: int = 100) -> Image.Image:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=2,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        qr_image = qr_image.resize((size, size), Image.Resampling.NEAREST)
        return qr_image
    
    def _draw_qr_code(self, draw: ImageDraw, image: Image, url: str, qr_x: int, qr_y: int) -> None:
        qr_size = 100
        
        qr_image = self._generate_qr_code(url, qr_size)
        image.paste(qr_image, (qr_x, qr_y))
        
        label_text = "Scan for details"
        label_width = self.small_font.getlength(label_text)
        
        text_x = qr_x + (qr_size - label_width) // 2
        text_y = qr_y + qr_size + 5  # 5px padding
        
        padding = 4
        draw.rectangle(
            [
                text_x - padding,
                text_y - padding,
                text_x + label_width + padding,
                text_y + self.small_font.size + padding
            ],
            fill=0  # Black background
        )
        
        draw.text(
            (text_x, text_y),
            label_text,
            font=self.small_font,
            fill=1  # White text on black background
        )

    def _draw_header(self, draw: ImageDraw, data: Dict[str, Any]) -> None:
        draw.text(
            (20, 15),
            'FBI MOST WANTED',
            font=self.title_font,
            fill=0
        )
        
        draw.text(
            (20, 50),
            f"Total Wanted: {data.get('total_wanted', 0)}",
            font=self.subtitle_font,
            fill=0
        )

    def _draw_wanted_person(self, draw: ImageDraw, person: Dict[str, Any], image: Image) -> None:
        # Image dimensions
        right_margin = 20
        image_width = 200
        image_height = 240
        image_x = self.width - image_width - right_margin
        image_y = 80
        text_width = image_x - 40

        current_y = 80
        title_lines = self._wrap_text(person['title'], self.name_font, text_width)
        for line in title_lines:
            draw.text(
                (20, current_y),
                line,
                font=self.name_font,
                fill=0
            )
            current_y += 30

        current_y += 5
        if person['description']:
            desc_parts = person['description'].split('\r\n')
            if len(desc_parts) >= 2:
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

        details_text = ""
        if person['details']:
            details_text = re.sub('<[^<]+?>', '', person['details'])
        elif person['description']:
            details_text = person['description']

        if details_text:
            current_y += 15
            details_lines = self._wrap_text(details_text, self.body_font, text_width)
            max_lines = 6  # Limit number of lines to show
            
            # If we have more lines than displayable, add ...
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
                # Show all lines if space provides
                for line in details_lines:
                    draw.text(
                        (20, current_y),
                        line,
                        font=self.body_font,
                        fill=0
                    )
                    current_y += 22
                
        if person.get('reward_text'):
            current_y += 15
            
            draw.text(
                (20, current_y),
                "REWARD",
                font=self.heading_font,
                fill=0
            )
            current_y += 25
            
            reward_text_lines = self._wrap_text(person['reward_text'], self.body_font, text_width)
            for line in reward_text_lines:
                draw.text(
                    (20, current_y),
                    line,
                    font=self.body_font,
                    fill=0
                )
                current_y += 22
                
        qr_size = 100
        qr_x = self.width - qr_size - 20
        qr_y = self.height - qr_size - 70

        if person.get('url'):
            self._draw_qr_code(draw, image, person['url'], qr_x, qr_y)

    def _draw_status_bar(self, draw: ImageDraw, data: Dict[str, Any]) -> None:
        status_height = 30
        bar_y = self.height - status_height - 10
        
        draw.rectangle(
            [0, bar_y, self.width, bar_y + status_height],
            fill=0
        )
        
        timestamp = data.get('timestamp', 'Unknown')
        if isinstance(timestamp, str):
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                timestamp = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
            except ValueError:
                pass
        
        status_text = f'Last Update: {timestamp}'
        draw.text(
            (10, bar_y + 5),
            status_text,
            font=self.small_font,
            fill=1  # White text on black background
        )

    def _draw_placeholder_image(self, image: Image, x: int, width: int) -> None:
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
        try:
            # Encode FBI URL for proxy service
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
        image = Image.new('1', (self.width, self.height), 1)
        draw = ImageDraw.Draw(image)
        
        draw.text(
            (20, 20),
            'FBI Most Wanted - Error',
            font=self.title_font,
            fill=0
        )
        
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