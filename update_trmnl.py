#!/usr/bin/env python3

import os
import json
import logging
import requests
import qrcode
from datetime import datetime, UTC
from src.services.api_service import APIService
from src.services.display import DisplayGenerator

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def save_image(image_data: bytes, filename: str):
    """Save binary image data to file"""
    with open(filename, 'wb') as f:
        f.write(image_data)

def generate_qr(url: str, filename: str):
    """Generate QR code and save to file"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    qr_image = qr.make_image(fill_color="black", back_color="white")
    qr_image.save(filename)

def update_trmnl():
    try:
        plugin_uuid = os.environ.get('TRMNL_PLUGIN_UUID')
        api_key = os.environ.get('TRMNL_API_KEY')
        
        logger.info("Starting update process")
        
        # Get FBI data
        api_service = APIService()
        data = api_service.get_data()
        person = data['wanted_list'][0]
        
        # Generate and save images
        display_generator = DisplayGenerator(800, 480)
        image_data = display_generator.create_display(data)
        save_image(image_data, 'wanted.jpg')
        
        # Generate QR code
        generate_qr(person['url'], 'qr.jpg')
        
        # Save data to JSON
        storage_data = {
            "Name": person['title'],
            "Description": person['description'],
            "Status": person.get('status', 'WANTED'),
            "RewardText": person.get('reward_text', 'No reward information available'),
            "TotalWanted": data['total_wanted'],
            "Attribution": "Data provided by FBI.gov",
            "LastUpdate": datetime.now(UTC).isoformat(),
            "QRCodeURL": "qr.jpg"
        }
        
        with open('FBIMostWanted.json', 'w') as f:
            json.dump(storage_data, f, indent=2)
        
        # Send to TRMNL
        url = f'https://usetrmnl.com/api/custom_plugins/{plugin_uuid}'
        headers = {'Authorization': f'Bearer {api_key}'}
        
        with open('wanted.jpg', 'rb') as f:
            files = {'image': ('wanted.jpg', f, 'image/jpeg')}
            response = requests.post(
                url,
                headers=headers,
                files=files,
                data={'data': json.dumps(storage_data)}
            )
        
        response.raise_for_status()
        logger.info("Successfully updated TRMNL display")
        
    except Exception as e:
        logger.error(f"Error updating TRMNL: {str(e)}")
        raise

if __name__ == '__main__':
    update_trmnl()