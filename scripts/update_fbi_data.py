#!/usr/bin/env python3

import os
import json
from datetime import datetime, UTC
import requests
from PIL import Image, ImageDraw, ImageFont
import io
from urllib.parse import urlparse, urlunparse
import random
import qrcode

# Import your existing classes
from src.services.display import DisplayGenerator
from src.services.api_service import APIService

def notify_trmnl(data, display_generator):
    """Send update to TRMNL via webhook"""
    trmnl_uuid = os.environ.get('TRMNL_PLUGIN_UUID')
    trmnl_api_key = os.environ.get('TRMNL_API_KEY')
    
    if not trmnl_uuid or not trmnl_api_key:
        raise ValueError("Missing TRMNL credentials")
        
    # Generate the display image
    image_data = display_generator.create_display(data)
    
    # Create the webhook URL
    url = f"https://usetrmnl.com/api/custom_plugins/{trmnl_uuid}"
    
    # Prepare the payload
    payload = {
        'merge_variables': {
            'title': data['wanted_list'][0]['title'],
            'description': data['wanted_list'][0]['description'],
            'status': data['wanted_list'][0]['status'],
            'reward_text': data['wanted_list'][0].get('reward_text', ''),
            'total_wanted': data['total_wanted'],
            'timestamp': data['timestamp']
        }
    }
    
    # Send the update to TRMNL
    files = {
        'image': ('image.bmp', image_data, 'image/bmp')
    }
    
    headers = {
        'Authorization': f'Bearer {trmnl_api_key}'
    }
    
    response = requests.post(url, headers=headers, files=files, data={'data': json.dumps(payload)})
    response.raise_for_status()

def main():
    try:
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Initialize your existing services
        api_service = APIService()
        display_generator = DisplayGenerator(800, 480)
        
        # Get FBI data using your existing service
        data = api_service.get_data()
        
        # Save the data
        with open('data/current_wanted.json', 'w') as f:
            json.dump(data, f, indent=2)
            
        # Save the display image
        image_data = display_generator.create_display(data)
        with open('data/display.bmp', 'wb') as f:
            f.write(image_data)
            
        # Download the FBI image if available
        if data['wanted_list'][0].get('images'):
            response = requests.get(data['wanted_list'][0]['images'])
            if response.status_code == 200:
                with open('data/wanted_image.jpg', 'wb') as f:
                    f.write(response.content)
                    
        # Generate QR code if URL available
        if data['wanted_list'][0].get('url'):
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(data['wanted_list'][0]['url'])
            qr.make(fit=True)
            qr_image = qr.make_image(fill_color="black", back_color="white")
            qr_image.save('data/wanted_qr.png')
            
        # Notify TRMNL
        notify_trmnl(data, display_generator)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == '__main__':
    main()