# Buddy System Configuration
# Copy this file to config.py and modify as needed

# Server Configuration
SERVER_HOST = '0.0.0.0'  # Listen on all interfaces
SERVER_PORT = 9999       # Default port for Buddy system

# Voice Recognition Configuration
VOSK_MODEL_PATH = 'vosk-model-en-us-0.22'  # Path to Vosk model
ACTIVATION_WORD = 'buddy'                   # Word to activate voice commands
VOICE_TIMEOUT = 30                          # Seconds before stopping voice recognition

# Client Configuration
RECONNECT_DELAY = 5      # Seconds to wait before reconnecting
PING_INTERVAL = 10       # Seconds between ping messages
MAX_MESSAGE_DISPLAY = 30 # Seconds to display messages

# Network Configuration
DISCOVERY_TIMEOUT = 0.1  # Timeout for network discovery
MAX_CLIENTS = 50         # Maximum number of connected clients

# Security Configuration
ALLOWED_COMMANDS = [
    'shutdown', 'restart', 'lock', 'open_app', 'close_apps',
    'show_desktop', 'screenshot', 'message', 'ping'
]

# Application Shortcuts
APP_SHORTCUTS = {
    'firefox': 'firefox',
    'browser': 'firefox',
    'calculator': 'gnome-calculator',
    'file manager': 'nautilus',
    'text editor': 'gedit',
    'terminal': 'gnome-terminal'
}

# Voice Command Mappings
VOICE_COMMANDS = {
    'shutdown all computers': {'action': 'shutdown'},
    'restart all computers': {'action': 'restart'},
    'reboot all computers': {'action': 'restart'},
    'lock all screens': {'action': 'lock'},
    'lock all computers': {'action': 'lock'},
    'open firefox': {'action': 'open_app', 'app': 'firefox'},
    'open browser': {'action': 'open_app', 'app': 'firefox'},
    'open calculator': {'action': 'open_app', 'app': 'gnome-calculator'},
    'open file manager': {'action': 'open_app', 'app': 'nautilus'},
    'close all applications': {'action': 'close_apps'},
    'show desktop': {'action': 'show_desktop'},
    'take screenshot': {'action': 'screenshot'},
}
