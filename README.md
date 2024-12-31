# FBI Most Wanted TRMNL Plugin

A TRMNL e-ink display plugin that shows information about FBI Most Wanted fugitives, randomly selecting and displaying one person from the current Most Wanted list.

## Features

- Displays FBI Most Wanted information on TRMNL e-ink display
- Randomly selects one person from the current Most Wanted list
- Shows detailed information including:
  - Photo (when available)
  - Name and status
  - Reward information
  - Description and details
- Advanced image processing for e-ink optimization
- Built-in caching system to minimize API calls
- Comprehensive error handling and display
- Cloudflare-aware image fetching system

## Prerequisites

- Python 3.12+
- TRMNL device and API key
- Chrome/Chromium (for Selenium-based image fetching)
- Docker (optional)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/OptimumMeans/TRMNL-FBI-Most-Wanted
cd TRMNL-FBI-Most-Wanted
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create .env file:
```bash
cp .env.template .env
```

5. Update .env with your configuration:
```
TRMNL_API_KEY=your_api_key_here
TRMNL_PLUGIN_UUID=your_plugin_uuid_here
CACHE_TIMEOUT=600  # Cache timeout in seconds
```

## Development

### Running Locally

```bash
python -m src.app
```

The development server will automatically open your default browser to:
- Home page: http://localhost:8080/
- Webhook endpoint: http://localhost:8080/webhook

### Project Structure
```
├── .env.template         # Environment variables template
├── .gitignore           # Git ignore rules
├── README.md            # Project documentation
├── render.yaml          # Render deployment configuration
├── requirements.txt     # Python dependencies
├── src/                 # Source code directory
│   ├── app.py          # Main application entry point
│   ├── config.py       # Configuration management
│   ├── services/       # Core services
│   │   ├── api_service.py    # FBI API interaction service
│   │   └── display.py        # Display generation service
│   └── utils/          # Utility functions
│       ├── __init__.py      # Package exports
│       ├── formatters.py    # Data formatting utilities
│       └── validators.py    # Data validation utilities
└── tests/              # Test files
    └── test_display.py  # Display service tests
```

### Core Components

1. **API Service** (`src/services/api_service.py`)
   - Handles FBI Most Wanted API interactions
   - Implements caching mechanism
   - Random selection of wanted persons
   - Image URL processing and validation

2. **Display Generator** (`src/services/display.py`)
   - Creates optimized images for e-ink display
   - Handles error displays
   - Advanced image processing features:
     - Cloudflare bypass for image fetching
     - Dithering optimization for e-ink
     - Dynamic text wrapping and layout
     - Placeholder generation for missing images

3. **Configuration** (`src/config.py`)
   - Environment-based configuration
   - Display dimensions
   - Cache timeout settings
   - API credentials

### FBI API Integration

The plugin integrates with the FBI Most Wanted API (https://api.fbi.gov/wanted/v1/list) to fetch:
- Total number of wanted persons
- Individual profiles including:
  - Name and status
  - Description and details
  - Reward information
  - Photo URLs

### Display Features

The plugin creates an optimized display showing:
1. Header with FBI Most Wanted title and total count
2. Main content area with:
   - Person's name/title
   - Status
   - Photo (if available)
   - Reward information
   - Description
   - Additional details
3. Status bar with last update timestamp

## Testing

Run the test suite:

```bash
python -m pytest tests/
```

Current test coverage includes:
- Display generator initialization
- Error display generation
- API service functionality
- Display creation with mock data

## Deployment

Deploy using render.yaml configuration:

```bash
render deploy
```

The render.yaml file includes:
- Python 3.12.0 runtime
- Gunicorn web server
- Environment variable configuration
- Chrome/Chromium dependencies

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT
