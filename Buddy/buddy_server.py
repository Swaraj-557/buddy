#!/usr/bin/env python3
"""
Buddy Server - Voice-activated computer lab management system
Server component that listens for voice commands and sends instructions to client computers.

Requirements:
- pip install vosk pyaudio tkinter
- Download Vosk model (e.g., vosk-model-en-us-0.22)

Usage:
    python buddy_server.py

Author: Buddy System
Date: August 2025
"""

import socket
import threading
import json
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import queue
import pyaudio
import vosk
import os
import sys
from datetime import datetime


class BuddyServer:
    def __init__(self):
        self.host = '0.0.0.0'  # Listen on all interfaces
        self.port = 9999
        self.clients = {}  # Store connected clients {address: socket}
        self.server_socket = None
        self.running = False
        
        # Voice recognition setup
        self.model_path = "vosk-model-en-us-0.22"  # Download from https://alphacephei.com/vosk/models
        self.model = None
        self.recognizer = None
        self.microphone = None
        self.audio_queue = queue.Queue()
        self.listening = False
        
        # GUI setup
        self.root = None
        self.setup_gui()
        
        # Command mappings
        self.command_mappings = {
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

    def setup_gui(self):
        """Set up the GUI interface"""
        self.root = tk.Tk()
        self.root.title("Buddy Server - Computer Lab Manager")
        self.root.geometry("800x600")
        
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Server Status")
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="Status: Stopped", font=("Arial", 12))
        self.status_label.pack(pady=5)
        
        # Control buttons
        button_frame = ttk.Frame(status_frame)
        button_frame.pack(pady=5)
        
        self.start_button = ttk.Button(button_frame, text="Start Server", command=self.start_server)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Stop Server", command=self.stop_server, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.voice_button = ttk.Button(button_frame, text="Start Voice Recognition", command=self.toggle_voice_recognition, state=tk.DISABLED)
        self.voice_button.pack(side=tk.LEFT, padx=5)
        
        # Connected clients frame
        clients_frame = ttk.LabelFrame(main_frame, text="Connected Clients")
        clients_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Clients listbox
        self.clients_listbox = tk.Listbox(clients_frame, height=6)
        self.clients_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Manual command frame
        command_frame = ttk.LabelFrame(main_frame, text="Manual Commands")
        command_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(command_frame, text="Quick Commands:").pack(anchor=tk.W, padx=5, pady=(5, 0))
        
        quick_buttons_frame = ttk.Frame(command_frame)
        quick_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(quick_buttons_frame, text="Shutdown All", command=lambda: self.send_command({'action': 'shutdown'})).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_buttons_frame, text="Restart All", command=lambda: self.send_command({'action': 'restart'})).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_buttons_frame, text="Lock All", command=lambda: self.send_command({'action': 'lock'})).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_buttons_frame, text="Open Firefox", command=lambda: self.send_command({'action': 'open_app', 'app': 'firefox'})).pack(side=tk.LEFT, padx=2)
        
        # Custom message
        message_frame = ttk.Frame(command_frame)
        message_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(message_frame, text="Send Message:").pack(side=tk.LEFT)
        self.message_entry = ttk.Entry(message_frame, width=40)
        self.message_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(message_frame, text="Send", command=self.send_message).pack(side=tk.LEFT, padx=5)
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def log_message(self, message):
        """Add message to the log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        print(f"[{timestamp}] {message}")

    def start_server(self):
        """Start the server to listen for client connections"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(50)  # Allow up to 50 connections
            
            self.running = True
            self.log_message(f"Server started on {self.host}:{self.port}")
            
            # Start accepting connections in a separate thread
            threading.Thread(target=self.accept_connections, daemon=True).start()
            
            # Update GUI
            self.status_label.config(text=f"Status: Running on {self.host}:{self.port}")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.voice_button.config(state=tk.NORMAL)
            
        except Exception as e:
            self.log_message(f"Error starting server: {e}")
            messagebox.showerror("Error", f"Failed to start server: {e}")

    def stop_server(self):
        """Stop the server"""
        self.running = False
        self.listening = False
        
        # Close all client connections
        for addr, client_socket in list(self.clients.items()):
            try:
                client_socket.close()
            except:
                pass
        self.clients.clear()
        
        # Close server socket
        if self.server_socket:
            self.server_socket.close()
        
        # Update GUI
        self.status_label.config(text="Status: Stopped")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.voice_button.config(state=tk.DISABLED, text="Start Voice Recognition")
        self.clients_listbox.delete(0, tk.END)
        
        self.log_message("Server stopped")

    def accept_connections(self):
        """Accept incoming client connections"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                self.clients[address] = client_socket
                self.log_message(f"Client connected: {address[0]}:{address[1]}")
                
                # Update clients listbox
                self.root.after(0, lambda: self.clients_listbox.insert(tk.END, f"{address[0]}:{address[1]}"))
                
                # Start handling this client in a separate thread
                threading.Thread(target=self.handle_client, args=(client_socket, address), daemon=True).start()
                
            except OSError:
                break  # Server socket closed

    def handle_client(self, client_socket, address):
        """Handle communication with a specific client"""
        while self.running:
            try:
                # Send periodic ping to check if client is still alive
                ping_data = json.dumps({'action': 'ping'})
                client_socket.send(ping_data.encode() + b'\n')
                time.sleep(10)  # Ping every 10 seconds
                
            except (ConnectionResetError, BrokenPipeError, OSError):
                # Client disconnected
                self.log_message(f"Client disconnected: {address[0]}:{address[1]}")
                if address in self.clients:
                    del self.clients[address]
                
                # Update clients listbox
                self.root.after(0, self.update_clients_listbox)
                break

    def update_clients_listbox(self):
        """Update the clients listbox"""
        self.clients_listbox.delete(0, tk.END)
        for addr in self.clients.keys():
            self.clients_listbox.insert(tk.END, f"{addr[0]}:{addr[1]}")

    def send_command(self, command):
        """Send command to all connected clients"""
        if not self.clients:
            self.log_message("No clients connected")
            return
        
        command_str = json.dumps(command)
        disconnected_clients = []
        
        for address, client_socket in self.clients.items():
            try:
                client_socket.send(command_str.encode() + b'\n')
                self.log_message(f"Sent command to {address[0]}: {command}")
            except (ConnectionResetError, BrokenPipeError, OSError):
                disconnected_clients.append(address)
        
        # Remove disconnected clients
        for addr in disconnected_clients:
            if addr in self.clients:
                del self.clients[addr]
                self.log_message(f"Removed disconnected client: {addr[0]}")
        
        if disconnected_clients:
            self.root.after(0, self.update_clients_listbox)

    def send_message(self):
        """Send a custom message to all clients"""
        message = self.message_entry.get().strip()
        if message:
            command = {'action': 'message', 'content': message}
            self.send_command(command)
            self.message_entry.delete(0, tk.END)

    def setup_voice_recognition(self):
        """Initialize voice recognition"""
        try:
            if not os.path.exists(self.model_path):
                self.log_message("Vosk model not found. Please download vosk-model-en-us-0.22")
                messagebox.showerror("Error", f"Vosk model not found at {self.model_path}\nPlease download from https://alphacephei.com/vosk/models")
                return False
            
            self.model = vosk.Model(self.model_path)
            self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
            
            # Setup microphone
            self.microphone = pyaudio.PyAudio()
            return True
            
        except Exception as e:
            self.log_message(f"Error setting up voice recognition: {e}")
            messagebox.showerror("Error", f"Failed to setup voice recognition: {e}")
            return False

    def toggle_voice_recognition(self):
        """Start or stop voice recognition"""
        if not self.listening:
            if self.setup_voice_recognition():
                self.listening = True
                self.voice_button.config(text="Stop Voice Recognition")
                threading.Thread(target=self.listen_for_voice_commands, daemon=True).start()
                self.log_message("Voice recognition started")
        else:
            self.listening = False
            self.voice_button.config(text="Start Voice Recognition")
            self.log_message("Voice recognition stopped")

    def listen_for_voice_commands(self):
        """Listen for voice commands using microphone"""
        try:
            stream = self.microphone.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=8000
            )
            
            self.log_message("Listening for voice commands... (say 'buddy' to activate)")
            
            while self.listening:
                data = stream.read(4000, exception_on_overflow=False)
                
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get('text', '').lower().strip()
                    
                    if text:
                        self.log_message(f"Heard: {text}")
                        
                        # Check if command starts with activation word "buddy"
                        if text.startswith('buddy'):
                            command_text = text[5:].strip()  # Remove "buddy" and process the rest
                            self.process_voice_command(command_text)
            
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            self.log_message(f"Error in voice recognition: {e}")
            self.listening = False
            self.root.after(0, lambda: self.voice_button.config(text="Start Voice Recognition"))

    def process_voice_command(self, command_text):
        """Process recognized voice command"""
        self.log_message(f"Processing command: {command_text}")
        
        # Check for message commands
        if command_text.startswith('send message') or command_text.startswith('message'):
            # Extract message content
            if 'send message' in command_text:
                message_content = command_text.split('send message', 1)[1].strip()
            else:
                message_content = command_text.split('message', 1)[1].strip()
            
            if message_content:
                command = {'action': 'message', 'content': message_content}
                self.send_command(command)
                return
        
        # Check predefined commands
        for voice_command, action in self.command_mappings.items():
            if voice_command in command_text:
                self.send_command(action)
                return
        
        # If no command matched
        self.log_message(f"Unknown command: {command_text}")

    def run(self):
        """Run the GUI application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        """Handle window closing"""
        if self.running:
            self.stop_server()
        if self.microphone:
            self.microphone.terminate()
        self.root.destroy()


def main():
    """Main function"""
    print("Buddy Server - Computer Lab Management System")
    print("=" * 50)
    print("Requirements:")
    print("1. Install dependencies: pip install vosk pyaudio tkinter")
    print("2. Download Vosk model from: https://alphacephei.com/vosk/models")
    print("   Extract to: vosk-model-en-us-0.22/")
    print("3. Ensure clients are running on target computers")
    print("=" * 50)
    
    try:
        server = BuddyServer()
        server.run()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
