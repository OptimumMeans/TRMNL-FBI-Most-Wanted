#!/usr/bin/env python3

import os
import json
import logging
import requests
from datetime import datetime, UTC
from src.services.api_service import APIService
from src.services.display import DisplayGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_trmnl():
    """Update TRMNL display with new FBI Most Wanted data"""
    try:
        # Get required environment variables
        plugin_uuid = os.environ.get('TRMNL_PLUGIN_UUID')
        api_key = os.environ.get('TRMNL_API_KEY')
        
        if not plugin_uuid or not api_key:
            raise ValueError("Missing required environment variables")
            
        # Initialize services
        api_service = APIService()
        display_generator = DisplayGenerator(800, 480)
        
        # Get new FBI data
        logger.info("Fetching new FBI data...")
        data = api_service.get_data()
        
        if not data or 'wanted_list' not in data or not data['wanted_list']:
            raise ValueError("No FBI data available")
            
        # Generate the display image
        logger.info("Generating display image...")
        image_data = display_generator.create_display(data)
        
        # Prepare the TRMNL payload
        person = data['wanted_list'][0]
        payload = {
            'merge_variables': {
                'title': person['title'],
                'description': person['description'],
                'status': person['status'],
                'reward_text': person.get('reward_text', ''),
                'total_wanted': data['total_wanted'],
                'timestamp': datetime.now(UTC).isoformat()
            }
        }
        
        # Prepare the files
        files = {
            'image': ('image.bmp', image_data, 'image/bmp')
        }
        
        # Send to TRMNL
        logger.info("Sending update to TRMNL...")
        url = f'https://usetrmnl.com/api/custom_plugins/{plugin_uuid}'
        headers = {'Authorization': f'Bearer {api_key}'}
        
        response = requests.post(
            url,
            headers=headers,
            files=files,
            data={'data': json.dumps(payload)}
        )
        
        response.raise_for_status()
        logger.info("Successfully updated TRMNL display")
        
    except Exception as e:
        logger.error(f"Error updating TRMNL: {str(e)}")
        raise

if __name__ == '__main__':
    update_trmnl()