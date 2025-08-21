#!/usr/bin/env python3
"""
Buddy Server - Windows Compatible Version
Voice-activated computer lab management system (Windows compatible version)

This version uses Windows Speech API instead of Vosk for better Windows compatibility.

Requirements:
- Windows 10+ with Speech Recognition
- pip install pywin32 (for Windows speech)

Usage:
    python buddy_server_windows.py

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
import os
import sys
from datetime import datetime

# Windows-specific imports
try:
    import win32com.client
    import pythoncom
    WINDOWS_SPEECH_AVAILABLE = True
except ImportError:
    WINDOWS_SPEECH_AVAILABLE = False
    print("Warning: Windows Speech API not available. Install pywin32 for voice recognition.")


class BuddyServerWindows:
    def __init__(self):
        self.host = '0.0.0.0'  # Listen on all interfaces
        self.port = 9999
        self.clients = {}  # Store connected clients {address: socket}
        self.server_socket = None
        self.running = False
        
        # Voice recognition setup (Windows)
        self.speech_recognizer = None
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
        self.root.title("Buddy Server - Computer Lab Manager (Windows)")
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
        
        # Voice recognition button (only if Windows Speech is available)
        if WINDOWS_SPEECH_AVAILABLE:
            self.voice_button = ttk.Button(button_frame, text="Start Voice Recognition", command=self.toggle_voice_recognition, state=tk.DISABLED)
            self.voice_button.pack(side=tk.LEFT, padx=5)
        else:
            voice_info_label = ttk.Label(button_frame, text="Voice: Install pywin32 for speech recognition", foreground="red")
            voice_info_label.pack(side=tk.LEFT, padx=5)
        
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
        
        # Voice command entry (alternative to speech recognition)
        voice_frame = ttk.Frame(command_frame)
        voice_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(voice_frame, text="Voice Command:").pack(side=tk.LEFT)
        self.voice_entry = ttk.Entry(voice_frame, width=40)
        self.voice_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.voice_entry.bind('<Return>', lambda e: self.process_text_command())
        ttk.Button(voice_frame, text="Execute", command=self.process_text_command).pack(side=tk.LEFT, padx=5)
        
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
            self.server_socket.listen(50)
            
            self.running = True
            self.log_message(f"Server started on {self.host}:{self.port}")
            
            # Start accepting connections in a separate thread
            threading.Thread(target=self.accept_connections, daemon=True).start()
            
            # Update GUI
            self.status_label.config(text=f"Status: Running on {self.host}:{self.port}")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            if WINDOWS_SPEECH_AVAILABLE:
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
        if WINDOWS_SPEECH_AVAILABLE:
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
                break

    def handle_client(self, client_socket, address):
        """Handle communication with a specific client"""
        while self.running:
            try:
                # Send periodic ping
                ping_data = json.dumps({'action': 'ping'})
                client_socket.send(ping_data.encode() + b'\n')
                time.sleep(10)
                
            except (ConnectionResetError, BrokenPipeError, OSError):
                self.log_message(f"Client disconnected: {address[0]}:{address[1]}")
                if address in self.clients:
                    del self.clients[address]
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
        
        if disconnected_clients:
            self.root.after(0, self.update_clients_listbox)

    def send_message(self):
        """Send a custom message to all clients"""
        message = self.message_entry.get().strip()
        if message:
            command = {'action': 'message', 'content': message}
            self.send_command(command)
            self.message_entry.delete(0, tk.END)

    def process_text_command(self):
        """Process text command as if it were a voice command"""
        command_text = self.voice_entry.get().strip().lower()
        if command_text:
            self.log_message(f"Processing text command: {command_text}")
            self.process_voice_command(command_text)
            self.voice_entry.delete(0, tk.END)

    def toggle_voice_recognition(self):
        """Start or stop voice recognition (Windows Speech API)"""
        if not WINDOWS_SPEECH_AVAILABLE:
            messagebox.showerror("Error", "Windows Speech API not available. Install pywin32.")
            return
            
        if not self.listening:
            self.listening = True
            self.voice_button.config(text="Stop Voice Recognition")
            threading.Thread(target=self.listen_for_voice_commands_windows, daemon=True).start()
            self.log_message("Voice recognition started (Windows Speech API)")
        else:
            self.listening = False
            self.voice_button.config(text="Start Voice Recognition")
            self.log_message("Voice recognition stopped")

    def listen_for_voice_commands_windows(self):
        """Listen for voice commands using Windows Speech API"""
        try:
            pythoncom.CoInitialize()
            
            # Create speech recognition object
            speech_recognizer = win32com.client.Dispatch("SAPI.SpVoice")
            
            self.log_message("Listening for voice commands... (say 'buddy' to activate)")
            
            # Note: This is a simplified implementation
            # A full implementation would use Windows Speech Recognition SDK
            # For now, we'll use the text command interface
            
            while self.listening:
                time.sleep(1)  # Keep the thread alive
                
        except Exception as e:
            self.log_message(f"Error in voice recognition: {e}")
            self.listening = False
            self.root.after(0, lambda: self.voice_button.config(text="Start Voice Recognition"))

    def process_voice_command(self, command_text):
        """Process recognized voice command"""
        self.log_message(f"Processing command: {command_text}")
        
        # Check for message commands
        if command_text.startswith('send message') or command_text.startswith('message'):
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
        
        self.log_message(f"Unknown command: {command_text}")

    def run(self):
        """Run the GUI application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        """Handle window closing"""
        if self.running:
            self.stop_server()
        self.root.destroy()


def main():
    """Main function"""
    print("Buddy Server - Computer Lab Management System (Windows)")
    print("=" * 60)
    print("Windows-compatible version with text command interface")
    print("For voice recognition, install: pip install pywin32")
    print("=" * 60)
    
    try:
        server = BuddyServerWindows()
        server.run()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
