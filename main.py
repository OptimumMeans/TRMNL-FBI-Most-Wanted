import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
import time

load_dotenv()

TRMNL_PLUGIN_UUID = os.getenv('TRMNL_PLUGIN_UUID')
TRMNL_WEBHOOK_URL = f"https://usetrmnl.com/api/custom_plugins/{TRMNL_PLUGIN_UUID}"

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
        return response.json()
    except Exception as e:
        print(f"Error fetching FBI data: {e}")
        return None

def format_fbi_data(items):
    formatted_items = []
    
    for item in items:
        formatted_item = {
            'title': item.get('title', 'Unknown'),
            'description': item.get('description', ''),
            'subject': ', '.join(item.get('subjects', [])) if item.get('subjects') else '',
            'race': item.get('race', 'Unknown'),
            'sex': item.get('sex', 'Unknown'),
            'status': item.get('status', ''),
            'reward_text': item.get('reward_text', ''),
            'warning_message': item.get('warning_message', '')
        }
        formatted_items.append(formatted_item)
    
    return formatted_items

def send_to_trmnl(data):
    try:
        webhook_body = {
            "merge_variables": {
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_wanted": data.get('total', 0),
                "wanted_list": format_fbi_data(data.get('items', [])),
                "page": data.get('page', 1)
            }
        }
        
        response = requests.post(
            TRMNL_WEBHOOK_URL,
            json=webhook_body
        )
        response.raise_for_status()
        print(f"Successfully sent data to TRMNL at {datetime.now()}")
        
    except Exception as e:
        print(f"Error sending to TRMNL: {e}")

def main():
    data = get_fbi_data()
    if data:
        send_to_trmnl(data)

if __name__ == "__main__":
    main()