import os
import json
import logging
import requests
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
        
        logger.info(f"Plugin UUID: {plugin_uuid}")
        logger.info("API Key present: %s", bool(api_key))
        
        if not plugin_uuid or not api_key:
            raise ValueError("Missing required environment variables")
            
        api_service = APIService()
        display_generator = DisplayGenerator(800, 480)
        
        logger.info("Fetching FBI data...")
        data = api_service.get_data()
        
        if not data or 'wanted_list' not in data or not data['wanted_list']:
            raise ValueError("No FBI data available")
        
        person = data['wanted_list'][0]
        logger.info(f"Selected person: {person['title']}")
        
        logger.info("Generating display image...")
        image_data = display_generator.create_display(data)
        
        # Prepare the merge variables
        merge_variables = {
            'title': person['title'],
            'description': person['description'],
            'status': person['status'],
            'reward_text': person.get('reward_text', ''),
            'total_wanted': data['total_wanted'],
            'timestamp': datetime.now(UTC).isoformat()
        }
        
        # Log the data we're about to send
        logger.info("Merge variables to send: %s", json.dumps(merge_variables, indent=2))
        
        # Prepare form data with the correct structure
        form_data = {
            'data': json.dumps(merge_variables),  # Changed from {'merge_variables': merge_variables}
            'image': ('fbi_wanted.bmp', image_data, 'image/bmp')
        }
        
        # Send to TRMNL
        url = f'https://usetrmnl.com/api/custom_plugins/{plugin_uuid}'
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json'
        }
        
        logger.info(f"Sending POST request to: {url}")
        
        # Use requests to send multipart form data
        response = requests.post(
            url,
            headers=headers,
            files={'image': ('fbi_wanted.bmp', image_data, 'image/bmp')},
            data={'data': json.dumps(merge_variables)}  # Changed structure here
        )
        
        # Log full response
        logger.info(f"Response Status: {response.status_code}")
        logger.info(f"Response Headers: {dict(response.headers)}")
        try:
            logger.info(f"Response Content: {response.json()}")
        except:
            logger.info(f"Response Content: {response.text}")
        
        response.raise_for_status()
        logger.info("Successfully updated TRMNL display")
        
    except Exception as e:
        logger.error(f"Error updating TRMNL: {str(e)}")
        logger.error("Full traceback:", exc_info=True)
        raise

if __name__ == '__main__':
    update_trmnl()