#!/usr/bin/env python3

import os
import json
import logging
import requests
import traceback
from datetime import datetime, UTC
from src.services.api_service import APIService
from src.services.display import DisplayGenerator

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_trmnl():
    """Update TRMNL display with new FBI Most Wanted data"""
    try:
        # Get and validate environment variables
        plugin_uuid = os.environ.get('TRMNL_PLUGIN_UUID')
        api_key = os.environ.get('TRMNL_API_KEY')
        
        logger.debug("Starting update process")
        logger.debug(f"Plugin UUID: {plugin_uuid}")
        logger.debug(f"API Key present: {bool(api_key)}")
        
        if not plugin_uuid or not api_key:
            raise ValueError("Missing required environment variables")
            
        # Initialize services with try/except blocks
        try:
            api_service = APIService()
            display_generator = DisplayGenerator(800, 480)
        except Exception as e:
            logger.error(f"Error initializing services: {str(e)}")
            raise
            
        # Get FBI data with error handling
        try:
            logger.debug("Fetching FBI data...")
            data = api_service.get_data()
            logger.debug(f"Received data: {json.dumps(data, indent=2)}")
        except Exception as e:
            logger.error(f"Error fetching FBI data: {str(e)}")
            raise
            
        if not data or 'wanted_list' not in data or not data['wanted_list']:
            raise ValueError("No FBI data available")
        
        person = data['wanted_list'][0]
        logger.debug(f"Selected person: {person['title']}")
        
        # Generate display image with error handling
        try:
            logger.debug("Generating display image...")
            image_data = display_generator.create_display(data)
            logger.debug(f"Generated image size: {len(image_data)} bytes")
        except Exception as e:
            logger.error(f"Error generating display: {str(e)}")
            raise
            
        # Prepare TRMNL payload
        try:
            # Format merge variables
            merge_variables = {
                'title': person['title'],
                'description': person['description'],
                'status': person.get('status', 'WANTED'),
                'reward_text': person.get('reward_text', ''),
                'total_wanted': data['total_wanted'],
                'timestamp': datetime.now(UTC).isoformat()
            }
            
            logger.debug(f"Prepared merge variables: {json.dumps(merge_variables, indent=2)}")
            
            # Set up request components
            url = f'https://usetrmnl.com/api/custom_plugins/{plugin_uuid}'
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Accept': 'application/json'
            }
            
            files = {
                'image': ('fbi_wanted.bmp', image_data, 'image/bmp')
            }
            
            form_data = {
                'data': json.dumps(merge_variables)
            }
            
            logger.debug(f"Sending request to: {url}")
            logger.debug(f"Headers: {headers}")
            logger.debug(f"Form data: {form_data}")
            
            # Make request with full error handling
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    files=files,
                    data=form_data,
                    timeout=30  # Add timeout
                )
                
                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Response headers: {dict(response.headers)}")
                
                try:
                    response_json = response.json()
                    logger.debug(f"Response JSON: {json.dumps(response_json, indent=2)}")
                except:
                    logger.debug(f"Raw response: {response.text}")
                
                response.raise_for_status()
                
            except requests.exceptions.Timeout:
                logger.error("Request timed out")
                raise
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {str(e)}")
                raise
                
        except Exception as e:
            logger.error(f"Error in TRMNL update: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
            
        logger.info("Successfully updated TRMNL display")
        
    except Exception as e:
        logger.error(f"Fatal error in update process: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise

if __name__ == '__main__':
    update_trmnl()