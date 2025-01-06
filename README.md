# FBI Wanted TRMNL Plugin

A TRMNL plugin that displays FBI's Most Wanted list using the official FBI Wanted API.

## Features

- Displays current FBI Most Wanted list
- Shows detailed information for each wanted person
- Auto-updates every 6 hours via GitHub Actions
- Includes warning messages and reward information when available
- Clean, organized display using TRMNL's design system

## Setup

1. Create a new Private Plugin in TRMNL:
   - Go to Plugins -> Private Plugin -> Add New
   - Name it "FBI Most Wanted"
   - Select "Webhook" for the Strategy
   - Save and copy the Plugin UUID

2. Configure the plugin:
   - Copy `.env.example` to `.env`
   - Add your TRMNL Plugin UUID to `.env`
   - Copy the markup from `markup.html` into TRMNL's plugin markup editor

3. Set up GitHub Actions:
   - Add your TRMNL Plugin UUID as a GitHub secret named `TRMNL_PLUGIN_UUID`
   - The workflow will automatically run every 6 hours

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file with your configuration:
```bash
cp .env.example .env
```

3. Edit `.env` with your TRMNL Plugin UUID

4. Run the script:
```bash
python main.py
```

## GitHub Actions Configuration

The plugin automatically updates every 6 hours using GitHub Actions. You can also trigger updates manually from the Actions tab in your repository.

## License

MIT License

## Acknowledgments

- FBI Wanted API: https://api.fbi.gov/wanted/v1/list
- TRMNL Framework: https://usetrmnl.com/