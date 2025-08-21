#!/bin/bash
"""
Buddy System Installation Script
This script helps set up the Buddy system on both server and client machines.

Usage:
    ./install_buddy.sh [server|client]
    
Author: Buddy System
Date: August 2025
"""

echo "==============================================="
echo "Buddy System - Computer Lab Management"
echo "Installation and Setup Script"
echo "==============================================="

# Function to install Python dependencies
install_python_deps() {
    echo "Installing Python dependencies..."
    
    # Update package list
    sudo apt update
    
    # Install Python and pip if not present
    sudo apt install -y python3 python3-pip python3-tk
    
    # Install required Python packages
    pip3 install --user vosk pyaudio tkinter
    
    # Install system dependencies for audio
    sudo apt install -y portaudio19-dev python3-dev
    sudo apt install -y alsa-base alsa-utils pulseaudio
    
    echo "Python dependencies installed successfully!"
}

# Function to download Vosk model (for server)
install_vosk_model() {
    echo "Downloading Vosk speech recognition model..."
    
    if [ ! -d "vosk-model-en-us-0.22" ]; then
        echo "Downloading model (this may take a few minutes)..."
        wget -q --show-progress https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
        
        if [ $? -eq 0 ]; then
            echo "Extracting model..."
            unzip -q vosk-model-en-us-0.22.zip
            rm vosk-model-en-us-0.22.zip
            echo "Vosk model installed successfully!"
        else
            echo "Error downloading model. Please download manually from:"
            echo "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip"
            echo "Extract to: vosk-model-en-us-0.22/"
        fi
    else
        echo "Vosk model already exists."
    fi
}

# Function to install system utilities for client
install_client_utilities() {
    echo "Installing client system utilities..."
    
    # Install utilities for various client functions
    sudo apt install -y wmctrl xdotool gnome-screenshot
    sudo apt install -y notify-osd libnotify-bin
    
    echo "Client utilities installed successfully!"
}

# Function to set up client autostart
setup_client_autostart() {
    echo "Setting up client autostart..."
    
    # Create desktop entry for autostart
    AUTOSTART_DIR="$HOME/.config/autostart"
    mkdir -p "$AUTOSTART_DIR"
    
    cat > "$AUTOSTART_DIR/buddy-client.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Buddy Client
Comment=Computer Lab Management Client
Exec=python3 $(pwd)/buddy_client.py
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF
    
    echo "Client autostart configured!"
    echo "The client will start automatically on next login."
}

# Function to install client as systemd service
install_client_service() {
    echo "Installing client as systemd service..."
    
    python3 buddy_client.py --install-service
    
    echo "To start the service: sudo systemctl start buddy-client"
    echo "To enable on boot: sudo systemctl enable buddy-client"
}

# Function to set up firewall rules
setup_firewall() {
    echo "Configuring firewall rules..."
    
    # Allow Buddy server port
    sudo ufw allow 9999/tcp comment "Buddy System"
    
    echo "Firewall configured for Buddy System (port 9999)"
}

# Function to create test script
create_test_script() {
    cat > test_buddy.py << 'EOF'
#!/usr/bin/env python3
"""
Buddy System Test Script
Tests basic functionality of the Buddy system.
"""

import socket
import json
import time

def test_server_connection(server_ip="localhost", port=9999):
    """Test connection to Buddy server"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((server_ip, port))
        sock.close()
        
        if result == 0:
            print(f"✓ Server is reachable at {server_ip}:{port}")
            return True
        else:
            print(f"✗ Cannot connect to server at {server_ip}:{port}")
            return False
    except Exception as e:
        print(f"✗ Error testing connection: {e}")
        return False

def test_send_command(server_ip="localhost", port=9999):
    """Test sending a command to the server"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server_ip, port))
        
        # Send test message
        test_command = json.dumps({"action": "message", "content": "Test message from test script"})
        sock.send(test_command.encode() + b'\n')
        
        sock.close()
        print("✓ Test command sent successfully")
        return True
        
    except Exception as e:
        print(f"✗ Error sending test command: {e}")
        return False

def main():
    print("Buddy System Test Script")
    print("=" * 30)
    
    server_ip = input("Enter server IP (default: localhost): ").strip()
    if not server_ip:
        server_ip = "localhost"
    
    print(f"\nTesting connection to {server_ip}...")
    if test_server_connection(server_ip):
        print("\nTesting command sending...")
        test_send_command(server_ip)
    
    print("\nTest completed!")

if __name__ == "__main__":
    main()
EOF
    
    chmod +x test_buddy.py
    echo "Test script created: test_buddy.py"
}

# Main installation logic
if [ "$1" = "server" ]; then
    echo "Installing Buddy Server..."
    install_python_deps
    install_vosk_model
    setup_firewall
    create_test_script
    
    echo ""
    echo "==============================================="
    echo "Buddy Server Installation Complete!"
    echo "==============================================="
    echo "To start the server:"
    echo "  python3 buddy_server.py"
    echo ""
    echo "To test the installation:"
    echo "  python3 test_buddy.py"
    echo ""
    
elif [ "$1" = "client" ]; then
    echo "Installing Buddy Client..."
    install_python_deps
    install_client_utilities
    
    echo ""
    echo "Setup options:"
    echo "1. Autostart on login (recommended for student computers)"
    echo "2. Install as system service (recommended for lab computers)"
    echo "3. Manual start only"
    
    read -p "Choose option (1-3): " choice
    
    case $choice in
        1)
            setup_client_autostart
            ;;
        2)
            install_client_service
            ;;
        3)
            echo "Manual start only selected."
            ;;
        *)
            echo "Invalid choice. Setting up autostart..."
            setup_client_autostart
            ;;
    esac
    
    create_test_script
    
    echo ""
    echo "==============================================="
    echo "Buddy Client Installation Complete!"
    echo "==============================================="
    echo "To start the client manually:"
    echo "  python3 buddy_client.py [server_ip]"
    echo ""
    echo "To test the installation:"
    echo "  python3 test_buddy.py"
    echo ""
    
else
    echo "Usage: $0 [server|client]"
    echo ""
    echo "Examples:"
    echo "  $0 server    # Install on teacher/admin computer"
    echo "  $0 client    # Install on student computer"
    echo ""
    echo "Requirements:"
    echo "- Ubuntu 18.04+ or similar Linux distribution"
    echo "- Python 3.6+"
    echo "- Internet connection for initial setup"
    echo "- Sudo privileges"
    echo ""
fi
