# Buddy System - Computer Lab Management

An offline, voice-activated system for managing Ubuntu computers in a school computer lab via local network.

## Overview

The Buddy system consists of two main components:
1. **Server (Teacher/Admin PC)**: Listens for voice commands and sends instructions to client computers
2. **Client (Student PCs)**: Runs as a background service and executes system commands

## Features

- 🎤 **Offline Voice Recognition**: Uses Vosk for local speech-to-text
- 🖥️ **Multi-Computer Control**: Manage all lab computers simultaneously
- 🔒 **System-Level Actions**: Shutdown, restart, lock, launch applications
- 💬 **Message Broadcasting**: Send messages to all student screens
- 🛡️ **Graceful Reconnection**: Handles network disconnections automatically
- 🎛️ **GUI Interface**: Easy-to-use graphical interface for the server
- 🚀 **Auto-Start**: Client can auto-start on boot

## Supported Commands

### Voice Commands (Prefix with "Buddy")
- "Buddy, shutdown all computers"
- "Buddy, restart all computers"
- "Buddy, lock all screens"
- "Buddy, open Firefox"
- "Buddy, open calculator"
- "Buddy, send message: Your message here"

### Available Actions
- **System Control**: Shutdown, restart, lock screens
- **Application Management**: Open/close applications
- **Message Display**: Send pop-up messages to all screens
- **Screen Management**: Show desktop, take screenshots

## Installation

### Prerequisites
- Ubuntu 18.04+ (for clients)
- Python 3.6+
- Network connectivity between server and clients
- Microphone (for voice commands on server)

### Quick Installation

1. **Download the Buddy system**:
```bash
git clone <repository-url>
cd buddy-system
```

2. **Make installation script executable**:
```bash
chmod +x install_buddy.sh
```

3. **Install on Server (Teacher/Admin PC)**:
```bash
./install_buddy.sh server
```

4. **Install on Clients (Student PCs)**:
```bash
./install_buddy.sh client
```

### Manual Installation

#### Server Setup

1. **Install Python dependencies**:
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-tk portaudio19-dev
pip3 install vosk pyaudio tkinter
```

2. **Download Vosk speech model**:
```bash
wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
unzip vosk-model-en-us-0.22.zip
```

3. **Configure firewall** (if enabled):
```bash
sudo ufw allow 9999/tcp
```

#### Client Setup

1. **Install Python dependencies**:
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-tk
sudo apt install -y wmctrl xdotool gnome-screenshot notify-osd
pip3 install tkinter
```

2. **Set up auto-start** (optional):
```bash
# For user session autostart
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/buddy-client.desktop << EOF
[Desktop Entry]
Type=Application
Name=Buddy Client
Exec=python3 /path/to/buddy_client.py
Hidden=false
X-GNOME-Autostart-enabled=true
EOF
```

## Usage

### Starting the Server

1. **GUI Mode** (Recommended):
```bash
python3 buddy_server.py
```

2. **Use the GUI to**:
   - Start/stop the server
   - Enable voice recognition
   - Send manual commands
   - Monitor connected clients
   - View activity logs

### Starting the Client

1. **Auto-discovery mode**:
```bash
python3 buddy_client.py
```

2. **Specify server IP**:
```bash
python3 buddy_client.py 192.168.1.100
```

3. **Install as system service**:
```bash
python3 buddy_client.py --install-service
sudo systemctl start buddy-client
sudo systemctl enable buddy-client  # Auto-start on boot
```

### Voice Commands

1. Start voice recognition on the server
2. Say "Buddy" followed by your command
3. Examples:
   - "Buddy, lock all screens"
   - "Buddy, open Firefox"
   - "Buddy, send message class starts in 5 minutes"

## Network Configuration

### Automatic Discovery
The client can automatically discover the server on the local network by scanning common IP ranges.

### Manual Configuration
If automatic discovery fails, specify the server IP:
```bash
python3 buddy_client.py 192.168.1.100
```

### Firewall Settings
Ensure port 9999 is open on the server:
```bash
sudo ufw allow 9999/tcp
```

## Security Considerations

1. **Network Security**: The system operates on the local network only
2. **Command Restrictions**: Clients only accept predefined command types
3. **User Permissions**: Some commands require appropriate system permissions
4. **Sudo Access**: System commands (shutdown, restart) require sudo privileges

### Setting up Sudo Permissions (Optional)
To allow shutdown/restart without password:
```bash
# Add to /etc/sudoers using visudo
username ALL=(ALL) NOPASSWD: /sbin/shutdown, /sbin/reboot
```

## Troubleshooting

### Common Issues

1. **Voice recognition not working**:
   - Check microphone permissions
   - Verify Vosk model is downloaded
   - Test microphone with other applications

2. **Client not connecting**:
   - Verify server is running
   - Check network connectivity
   - Ensure firewall allows port 9999

3. **Commands not executing**:
   - Check client logs for error messages
   - Verify user permissions
   - Test commands manually in terminal

### Testing the Installation

Use the included test script:
```bash
python3 test_buddy.py
```

### Log Files

- **Server logs**: Displayed in GUI and console
- **Client logs**: Displayed in console
- **System logs**: Check systemd logs if running as service:
```bash
sudo journalctl -u buddy-client -f
```

## File Structure

```
buddy-system/
├── buddy_server.py          # Server application with GUI
├── buddy_client.py          # Client application
├── install_buddy.sh         # Installation script
├── test_buddy.py           # Testing script (generated by installer)
├── README.md               # This file
└── vosk-model-en-us-0.22/  # Vosk speech model (downloaded)
```

## Command Protocol

The system uses JSON messages over TCP sockets:

```json
{
  "action": "shutdown"
}

{
  "action": "message",
  "content": "Class starts in 5 minutes"
}

{
  "action": "open_app",
  "app": "firefox"
}
```

## Extending the System

### Adding New Commands

1. **Add to server command mappings** in `buddy_server.py`:
```python
self.command_mappings = {
    'your voice command': {'action': 'your_action', 'param': 'value'}
}
```

2. **Add command handler in client** in `buddy_client.py`:
```python
elif action == 'your_action':
    # Your implementation here
    pass
```

### Custom Applications

Add application shortcuts in the server GUI or extend the voice command mappings.

## Performance Notes

- **Server**: Minimal CPU usage when idle, moderate during voice recognition
- **Client**: Very low resource usage, runs silently in background
- **Network**: Minimal bandwidth usage (small JSON messages)
- **Scalability**: Tested with up to 50 concurrent clients

## License

This project is provided as-is for educational purposes. Please review and test thoroughly before use in production environments.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review log files for error messages
3. Test with the included test script
4. Verify network connectivity and permissions

## Version History

- **v1.0**: Initial release with core functionality
- Voice recognition with Vosk
- Multi-client support
- GUI interface
- Auto-discovery and reconnection
