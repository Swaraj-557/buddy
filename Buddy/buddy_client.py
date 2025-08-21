#!/usr/bin/env python3
"""
Buddy Client - Computer lab management client
Client component that runs on Ubuntu student computers and executes commands from the server.

Requirements:
- Python 3.6+
- Run with appropriate permissions for system commands
- Auto-start on boot (add to startup applications or systemd service)

Usage:
    python buddy_client.py [server_ip]
    
    If no server IP is provided, it will attempt to discover the server automatically.

Author: Buddy System
Date: August 2025
"""

import socket
import json
import subprocess
import threading
import time
import os
import sys
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import signal


class BuddyClient:
    def __init__(self, server_ip=None):
        self.server_ip = server_ip
        self.server_port = 9999
        self.client_socket = None
        self.running = False
        self.reconnect_delay = 5  # seconds
        
        # Message window for displaying messages from server
        self.message_window = None

    def log_message(self, message):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")

    def discover_server(self):
        """Attempt to discover the server on the local network"""
        self.log_message("Attempting to discover server...")
        
        # Get local network range
        try:
            # Get local IP
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
            local_ip = result.stdout.strip().split()[0]
            network_base = '.'.join(local_ip.split('.')[:-1]) + '.'
            
            self.log_message(f"Scanning network: {network_base}1-254")
            
            # Scan common IP ranges
            for i in range(1, 255):
                try:
                    test_ip = f"{network_base}{i}"
                    test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    test_socket.settimeout(0.1)
                    result = test_socket.connect_ex((test_ip, self.server_port))
                    
                    if result == 0:
                        self.log_message(f"Found server at: {test_ip}")
                        test_socket.close()
                        return test_ip
                    
                    test_socket.close()
                except:
                    continue
                    
        except Exception as e:
            self.log_message(f"Error during server discovery: {e}")
        
        return None

    def connect_to_server(self):
        """Connect to the Buddy server"""
        if not self.server_ip:
            self.server_ip = self.discover_server()
            
        if not self.server_ip:
            self.log_message("No server found. Please specify server IP manually.")
            return False
        
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.server_ip, self.server_port))
            self.log_message(f"Connected to server: {self.server_ip}:{self.server_port}")
            return True
            
        except Exception as e:
            self.log_message(f"Error connecting to server: {e}")
            return False

    def listen_for_commands(self):
        """Listen for commands from the server"""
        buffer = ""
        
        while self.running:
            try:
                data = self.client_socket.recv(1024).decode()
                if not data:
                    break
                
                buffer += data
                
                # Process complete JSON messages (separated by newlines)
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        try:
                            command = json.loads(line.strip())
                            self.process_command(command)
                        except json.JSONDecodeError as e:
                            self.log_message(f"Invalid JSON received: {e}")
                            
            except (ConnectionResetError, ConnectionAbortedError, OSError):
                self.log_message("Connection to server lost")
                break
            except Exception as e:
                self.log_message(f"Error receiving data: {e}")
                break

    def process_command(self, command):
        """Process a command received from the server"""
        action = command.get('action', '')
        self.log_message(f"Received command: {action}")
        
        try:
            if action == 'ping':
                # Respond to ping (keep-alive)
                pass
                
            elif action == 'shutdown':
                self.log_message("Shutting down system...")
                subprocess.run(['sudo', 'shutdown', '-h', 'now'], check=False)
                
            elif action == 'restart':
                self.log_message("Restarting system...")
                subprocess.run(['sudo', 'reboot'], check=False)
                
            elif action == 'lock':
                self.log_message("Locking screen...")
                # Try different lock commands based on desktop environment
                lock_commands = [
                    ['gnome-screensaver-command', '--lock'],
                    ['xdg-screensaver', 'lock'],
                    ['loginctl', 'lock-session'],
                    ['dm-tool', 'lock']
                ]
                
                for cmd in lock_commands:
                    try:
                        subprocess.run(cmd, check=True, timeout=5)
                        break
                    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                        continue
                        
            elif action == 'open_app':
                app = command.get('app', '')
                self.log_message(f"Opening application: {app}")
                subprocess.Popen([app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
            elif action == 'close_apps':
                self.log_message("Closing all user applications...")
                # Get list of user processes and close them gracefully
                try:
                    # Close common applications
                    apps_to_close = ['firefox', 'chromium', 'libreoffice', 'gedit', 'nautilus']
                    for app in apps_to_close:
                        subprocess.run(['pkill', '-f', app], check=False)
                except:
                    pass
                    
            elif action == 'show_desktop':
                self.log_message("Showing desktop...")
                # Minimize all windows
                try:
                    subprocess.run(['wmctrl', '-k', 'on'], check=False)
                except:
                    # Fallback for systems without wmctrl
                    subprocess.run(['xdotool', 'key', 'Super+d'], check=False)
                    
            elif action == 'screenshot':
                self.log_message("Taking screenshot...")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"/tmp/buddy_screenshot_{timestamp}.png"
                subprocess.run(['gnome-screenshot', '-f', screenshot_path], check=False)
                
            elif action == 'message':
                content = command.get('content', 'Message from administrator')
                self.show_message(content)
                
            elif action == 'execute_command':
                # Execute custom shell command (use with caution)
                cmd = command.get('command', '')
                if cmd:
                    self.log_message(f"Executing command: {cmd}")
                    subprocess.run(cmd, shell=True, check=False)
                    
            else:
                self.log_message(f"Unknown command: {action}")
                
        except Exception as e:
            self.log_message(f"Error executing command '{action}': {e}")

    def show_message(self, message):
        """Display a message to the user"""
        self.log_message(f"Displaying message: {message}")
        
        # Create a new thread for the GUI to avoid blocking
        threading.Thread(target=self._show_message_gui, args=(message,), daemon=True).start()
        
        # Also try to show via notify-send for system notifications
        try:
            subprocess.run(['notify-send', 'Buddy System', message], check=False)
        except:
            pass

    def _show_message_gui(self, message):
        """Show message in a GUI window"""
        try:
            # Create a simple message window
            root = tk.Tk()
            root.title("Message from Administrator")
            root.geometry("400x200")
            root.attributes('-topmost', True)  # Keep on top
            
            # Center the window
            root.eval('tk::PlaceWindow . center')
            
            # Message label
            msg_label = tk.Label(root, text=message, wraplength=350, font=("Arial", 12), pady=20)
            msg_label.pack(expand=True)
            
            # OK button
            ok_button = tk.Button(root, text="OK", command=root.destroy, font=("Arial", 10))
            ok_button.pack(pady=10)
            
            # Auto close after 30 seconds
            root.after(30000, root.destroy)
            
            root.mainloop()
            
        except Exception as e:
            self.log_message(f"Error showing message GUI: {e}")

    def run(self):
        """Main client loop"""
        self.running = True
        
        while self.running:
            if self.connect_to_server():
                self.log_message("Starting command listener...")
                self.listen_for_commands()
                
            if self.client_socket:
                self.client_socket.close()
                self.client_socket = None
            
            if self.running:
                self.log_message(f"Reconnecting in {self.reconnect_delay} seconds...")
                time.sleep(self.reconnect_delay)

    def stop(self):
        """Stop the client"""
        self.running = False
        if self.client_socket:
            self.client_socket.close()

    def install_as_service(self):
        """Install client as a systemd service for auto-start"""
        service_content = f"""[Unit]
Description=Buddy Client - Computer Lab Management
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'student')}
ExecStart=/usr/bin/python3 {os.path.abspath(__file__)}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        
        service_path = "/etc/systemd/system/buddy-client.service"
        
        try:
            print("Installing Buddy Client as a system service...")
            print("This requires sudo privileges.")
            
            # Write service file
            with open("/tmp/buddy-client.service", "w") as f:
                f.write(service_content)
            
            # Install service
            subprocess.run(['sudo', 'cp', '/tmp/buddy-client.service', service_path], check=True)
            subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
            subprocess.run(['sudo', 'systemctl', 'enable', 'buddy-client.service'], check=True)
            
            print("Service installed successfully!")
            print("To start: sudo systemctl start buddy-client")
            print("To stop: sudo systemctl stop buddy-client")
            print("To check status: sudo systemctl status buddy-client")
            
        except Exception as e:
            print(f"Error installing service: {e}")


def signal_handler(signum, frame):
    """Handle termination signals gracefully"""
    print("\nReceived termination signal. Shutting down...")
    sys.exit(0)


def main():
    """Main function"""
    print("Buddy Client - Computer Lab Management")
    print("=" * 40)
    
    # Handle command line arguments
    server_ip = None
    if len(sys.argv) > 1:
        if sys.argv[1] == '--install-service':
            client = BuddyClient()
            client.install_as_service()
            return
        else:
            server_ip = sys.argv[1]
    
    print(f"Starting client...")
    if server_ip:
        print(f"Server IP: {server_ip}")
    else:
        print("Server IP: Auto-discover")
    print("=" * 40)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        client = BuddyClient(server_ip)
        client.run()
    except KeyboardInterrupt:
        print("\nShutting down client...")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
