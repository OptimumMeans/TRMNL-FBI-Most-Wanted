import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
import time
import base64
import qrcode
from pathlib import Path

load_dotenv()

TRMNL_PLUGIN_UUID = os.getenv('TRMNL_PLUGIN_UUID')
TRMNL_WEBHOOK_URL = f"https://usetrmnl.com/api/custom_plugins/{TRMNL_PLUGIN_UUID}"
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

def generate_qr_code(url, save_path):
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        qr.add_data(url)
        qr.make(fit=True)

        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        qr_image.save(save_path)
        return True
    except Exception as e:
        print(f"Error generating QR code: {e}")
        return False

def get_fbi_data(page=1):
    headers = {
        "Accept": "application/json",
        "User-Agent": "TRMNL-FBI-Plugin/1.0"
    }
    
    try:
        response = requests.get(
            f"https://api.fbi.gov/wanted/v1/list",
            params={'page': page},
            headers=headers
        )
        response.raise_for_status()
        if DEBUG:
            print(f"FBI API Response Status: {response.status_code}")
        return response.json()
    except Exception as e:
        print(f"Error fetching FBI data: {e}")
        return None
    
def download_and_save_image(image_url, save_path):
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Error downloading image: {e}")
        return False

def format_fbi_data(items):
    if not items:
        return None
        
    item = items[0]
    
    dates_of_birth = ', '.join(item.get('dates_of_birth_used', [])) if item.get('dates_of_birth_used') else 'Unknown'
    
    height_min = item.get('height_min', 'Unknown')
    height_max = item.get('height_max', 'Unknown')
    height = f"{height_min}-{height_max}" if height_min != 'Unknown' else 'Unknown'
    
    weight = item.get('weight', 'Unknown')
    
    languages = ', '.join(item.get('languages', [])) if item.get('languages') else 'Unknown'
    
    scars_marks = item.get('scars_and_marks', 'None reported')
    
    fbi_id = item.get('uid', '')
    fbi_url = f"https://www.fbi.gov/wanted/viewing#{fbi_id}" if fbi_id else ''
    
    qr_code_path = 'qr_code.png'
    qr_generated = generate_qr_code(fbi_url, qr_code_path)
    
    qr_code_url = f"https://raw.githubusercontent.com/{os.getenv('GITHUB_REPOSITORY')}/main/qr_code.png" if qr_generated else ''
    
    images = item.get('images', [])
    profile_image_url = ''
    if images:
        original_image = next((img for img in images if img.get('large')), None)
        if original_image:
            image_url = original_image.get('large')
            image_path = 'profile_image.jpg'
            if download_and_save_image(image_url, image_path):
                profile_image_url = f"https://raw.githubusercontent.com/{os.getenv('GITHUB_REPOSITORY')}/main/profile_image.jpg"
    
    formatted_data = {
        'title': item.get('title', 'Unknown'),
        'description': item.get('description', ''),
        'subject': ', '.join(item.get('subjects', [])) if item.get('subjects') else 'Unknown',
        'race': item.get('race', 'Unknown'),
        'sex': item.get('sex', 'Unknown'),
        'nationality': item.get('nationality', 'Unknown'),
        'status': item.get('status', ''),
        'reward_text': item.get('reward_text', ''),
        'warning_message': item.get('warning_message', ''),
        'dates_of_birth': dates_of_birth,
        'place_of_birth': item.get('place_of_birth', 'Unknown'),
        'hair': item.get('hair', 'Unknown'),
        'eyes': item.get('eyes', 'Unknown'),
        'height': height,
        'weight': weight,
        'build': item.get('build', 'Unknown'),
        'complexion': item.get('complexion', 'Unknown'),
        'age_range': item.get('age_range', 'Unknown'),
        'languages': languages,
        'scars_marks': scars_marks,
        'remarks': item.get('remarks', ''),
        'details': item.get('details', ''),
        'caution': item.get('caution', ''),
        'fbi_url': fbi_url,
        'qr_code_url': qr_code_url,
        'profile_image_url': profile_image_url
    }
    
    if DEBUG:
        print(f"Formatted data for: {formatted_data['title']}")
    
    return formatted_data

def send_to_trmnl(data):
    try:
        person_data = format_fbi_data(data.get('items', []))
        if not person_data:
            raise ValueError("No person data available")
            
        webhook_body = {
            "merge_variables": {
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "person": person_data
            }
        }
        
        if DEBUG:
            print(f"Sending data to TRMNL: {json.dumps(webhook_body, indent=2)}")
            
        response = requests.post(
            TRMNL_WEBHOOK_URL,
            json=webhook_body
        )
        response.raise_for_status()
        print(f"Successfully sent data to TRMNL at {datetime.now()}")
    except Exception as e:
        print(f"Error sending to TRMNL: {e}")

def validate_config():
    if not TRMNL_PLUGIN_UUID:
        raise ValueError("TRMNL_PLUGIN_UUID is required. Please set it in your .env file")

def main():
    try:
        validate_config()
        data = get_fbi_data()
        if data:
            send_to_trmnl(data)
        else:
            print("No data received from FBI API")
    except Exception as e:
        print(f"Error in main execution: {e}")

if __name__ == "__main__":
    main()