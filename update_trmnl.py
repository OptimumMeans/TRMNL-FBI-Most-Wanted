#!/usr/bin/env python3

import os
import json
import logging
import requests
import base64
from datetime import datetime, UTC
from src.services.api_service import APIService
from src.services.display import DisplayGenerator

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_trmnl():
    try:
        plugin_uuid = os.environ.get('TRMNL_PLUGIN_UUID')
        api_key = os.environ.get('TRMNL_API_KEY')
        
        logger.debug("Starting update process")
        logger.debug(f"Plugin UUID: {plugin_uuid}")
        
        if not plugin_uuid or not api_key:
            raise ValueError("Missing required environment variables")
            
        # Get FBI data and generate image
        api_service = APIService()
        display_generator = DisplayGenerator(800, 480)
        
        data = api_service.get_data()
        person = data['wanted_list'][0]
        image_data = display_generator.create_display(data)
        
        # Convert image to base64 for logging
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        logger.debug(f"Generated image size: {len(image_data)} bytes")
        logger.debug(f"First 100 bytes of image (base64): {image_b64[:100]}")
        
        # Prepare multipart request
        url = f'https://usetrmnl.com/api/custom_plugins/{plugin_uuid}'
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json'
        }
        
        # Send as both file and base64
        files = {
            'image': ('fbi_wanted.bmp', image_data, 'image/bmp'),
            'file': ('fbi_wanted.bmp', image_data, 'image/bmp')
        }
        
        payload = {
            'data': json.dumps({
                'title': person['title'],
                'description': person['description'],
                'status': person.get('status', 'WANTED'),
                'reward_text': person.get('reward_text', ''),
                'total_wanted': data['total_wanted'],
                'timestamp': datetime.now(UTC).isoformat(),
                'image_base64': image_b64
            })
        }
        
        logger.debug("Sending request to TRMNL")
        response = requests.post(url, headers=headers, files=files, data=payload)
        
        # Log response details
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response headers: {dict(response.headers)}")
        try:
            logger.debug(f"Response content: {response.json()}")
        except:
            logger.debug(f"Raw response: {response.text}")
        
        response.raise_for_status()
        logger.info("Successfully updated TRMNL display")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    update_trmnl()