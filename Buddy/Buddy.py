#!/usr/bin/env python3
"""
Buddy System Launcher
Simple launcher script to start either the server or client component.

Usage:
    python Buddy.py server    # Start the server
    python Buddy.py client    # Start the client
    python Buddy.py           # Interactive mode

Author: Buddy System
Date: August 2025
"""

import sys
import os
import subprocess

def print_banner():
    """Print the Buddy system banner"""
    print("=" * 50)
    print("    BUDDY SYSTEM - Computer Lab Management")
    print("=" * 50)
    print("Offline voice-activated system for managing")
    print("Ubuntu computers in a school computer lab")
    print("=" * 50)

def show_help():
    """Show help information"""
    print("\nUsage:")
    print("  python Buddy.py server    # Start the server (teacher/admin PC)")
    print("  python Buddy.py client    # Start the client (student PC)")
    print("  python Buddy.py help      # Show this help")
    print("\nComponents:")
    print("  server  - Voice recognition and command center")
    print("  client  - Background service for receiving commands")
    print("\nFiles:")
    print("  buddy_server.py  - Server application")
    print("  buddy_client.py  - Client application")
    print("  README.md        - Complete documentation")
    print("\nFirst time setup:")
    print("  ./install_buddy.sh server   # Install server dependencies")
    print("  ./install_buddy.sh client   # Install client dependencies")

def start_server():
    """Start the Buddy server"""
    print("\nStarting Buddy Server...")
    if os.path.exists("buddy_server.py"):
        subprocess.run([sys.executable, "buddy_server.py"])
    else:
        print("Error: buddy_server.py not found!")
        return False

def start_client():
    """Start the Buddy client"""
    print("\nStarting Buddy Client...")
    if os.path.exists("buddy_client.py"):
        # Check if server IP was provided
        if len(sys.argv) > 2:
            subprocess.run([sys.executable, "buddy_client.py", sys.argv[2]])
        else:
            subprocess.run([sys.executable, "buddy_client.py"])
    else:
        print("Error: buddy_client.py not found!")
        return False

def interactive_mode():
    """Interactive mode for choosing component"""
    print("\nSelect component to start:")
    print("1. Server (Teacher/Admin PC)")
    print("2. Client (Student PC)")
    print("3. Help")
    print("4. Exit")
    
    try:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            start_server()
        elif choice == "2":
            server_ip = input("Enter server IP (or press Enter for auto-discovery): ").strip()
            if server_ip:
                sys.argv.append(server_ip)
            start_client()
        elif choice == "3":
            show_help()
        elif choice == "4":
            print("Goodbye!")
        else:
            print("Invalid choice!")
            
    except KeyboardInterrupt:
        print("\nGoodbye!")

def main():
    """Main function"""
    print_banner()
    
    if len(sys.argv) < 2:
        interactive_mode()
    elif sys.argv[1].lower() == "server":
        start_server()
    elif sys.argv[1].lower() == "client":
        start_client()
    elif sys.argv[1].lower() in ["help", "-h", "--help"]:
        show_help()
    else:
        print(f"\nUnknown command: {sys.argv[1]}")
        show_help()

if __name__ == "__main__":
    main()