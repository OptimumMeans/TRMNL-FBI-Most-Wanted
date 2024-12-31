from flask import Flask, Response, jsonify
from flask_cors import CORS
import logging
from datetime import datetime, UTC
import traceback
import os
import webbrowser
from threading import Timer

from .services.display import DisplayGenerator, get_trmnl_markup
from .config import Config
from .services.display import DisplayGenerator
from .services.api_service import APIService
from .utils.formatters import format_timestamp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize services
api_service = APIService()
display_generator = DisplayGenerator(Config.DISPLAY_WIDTH, Config.DISPLAY_HEIGHT)

def open_browser():
    webbrowser.open('http://localhost:8080/webhook')

@app.route('/')
def home():
    return jsonify({
        'name': 'TRMNL Plugin',
        'description': 'TRMNL Plugin Boilerplate',
        'version': '1.0.0',
        'status': 'running',
        'last_update': api_service.last_update.isoformat() if api_service.last_update else None,
        'refresh_interval': Config.REFRESH_INTERVAL
    })

# In src/app.py
@app.route('/webhook', methods=['GET'])
def trmnl_webhook():
    try:
        data = api_service.get_data()
        logger.info(f'Data retrieved: {data}')
        
        # Generate markup response using the get_trmnl_markup function
        markup = get_trmnl_markup(data)
        
        return jsonify(markup), 200
        
    except Exception as e:
        logger.error(f'Webhook error: {str(e)}')
        logger.error(traceback.format_exc())
        return jsonify({
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print('=' * 80)
    print('TRMNL Plugin Development Server')
    print('=' * 80)
    print(f'Server URL: http://localhost:{Config.PORT}')
    print(f'Webhook URL: http://localhost:{Config.PORT}/webhook')
    print('-' * 80)
    print('Opening webhook URL in browser...')
    print('Press Ctrl+C to quit')
    print('=' * 80)
    
    # Open browser after a short delay
    Timer(1.5, open_browser).start()
    
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
