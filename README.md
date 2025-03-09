# Local Media Display

Displays currently playing Windows media information and album art through a web interface, accessible on your local network.

## Setup
1. Install requirements:
```bash
pip install flask winsdk
```

2. Run the app:
- Double-click `media_display.pyw`
- Access at `http://localhost:5000` or `http://[your-ip]:5000`

## Auto-start
Add shortcut to `start_server.bat` in `shell:startup`
