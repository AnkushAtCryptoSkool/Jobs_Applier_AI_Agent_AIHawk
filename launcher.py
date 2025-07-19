#!/usr/bin/env python3
"""
Job Application Automation Launcher

This script provides users with a choice between using the CLI or Web UI interface.
"""

import os
import sys
import subprocess
import webbrowser
import time
import signal
import threading
from pathlib import Path
from typing import Optional

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    """Print the application banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║        🤖 Job Application Automation System 🤖              ║
    ║                                                              ║
    ║     Streamline your job search with AI-powered automation   ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_dependencies():
    """Check if all required dependencies are installed."""
    try:
        import flask
        import flask_socketio
        import yaml
        import click
        import typer
        import rich
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        return False

def check_configuration():
    """Check if the system is configured."""
    data_folder = Path("data_folder")
    required_files = [
        "secrets.yaml",
        "work_preferences.yaml", 
        "plain_text_resume.yaml"
    ]
    
    missing_files = []
    for file in required_files:
        if not (data_folder / file).exists():
            missing_files.append(file)
    
    return len(missing_files) == 0, missing_files

def start_web_ui():
    """Start the web UI server."""
    print("\n🌐 Starting Web UI...")
    print("Please wait while the server starts...")
    
    try:
        # Import and run the Flask app
        from web_ui.app import app, socketio
        
        def open_browser():
            """Open browser after a short delay."""
            time.sleep(2)
            webbrowser.open('http://localhost:5000')
        
        # Start browser in a separate thread
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        print("\n✅ Web UI server starting...")
        print("🌐 Open your browser and go to: http://localhost:5000")
        print("🔄 Browser should open automatically in a few seconds...")
        print("\n💡 Press Ctrl+C to stop the server")
        
        # Run the Flask app with SocketIO
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
        
    except KeyboardInterrupt:
        print("\n\n👋 Web UI server stopped.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting web UI: {e}")
        print("Please check your configuration and try again.")
        sys.exit(1)

def start_cli():
    """Start the CLI interface."""
    print("\n💻 Starting CLI interface...")
    
    try:
        # Check if configuration exists
        configured, missing_files = check_configuration()
        
        if not configured:
            print("\n⚠️  Configuration not found. Running setup wizard...")
            subprocess.run([sys.executable, "-m", "cli.main", "setup"])
        else:
            print("\n✅ Configuration found. Starting CLI...")
            subprocess.run([sys.executable, "-m", "cli.main", "run"])
            
    except KeyboardInterrupt:
        print("\n\n👋 CLI interface stopped.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting CLI: {e}")
        print("Please check your configuration and try again.")
        sys.exit(1)

def run_setup_wizard():
    """Run the setup wizard."""
    print("\n🔧 Running setup wizard...")
    
    try:
        subprocess.run([sys.executable, "-m", "cli.main", "setup"])
        print("\n✅ Setup completed!")
        input("\nPress Enter to return to main menu...")
    except Exception as e:
        print(f"\n❌ Error running setup: {e}")
        input("\nPress Enter to return to main menu...")

def show_status():
    """Show system status."""
    print("\n📊 System Status")
    print("=" * 50)
    
    # Check dependencies
    if check_dependencies():
        print("✅ Dependencies: All required packages installed")
    else:
        print("❌ Dependencies: Missing packages")
    
    # Check configuration
    configured, missing_files = check_configuration()
    if configured:
        print("✅ Configuration: System is configured")
    else:
        print(f"❌ Configuration: Missing files: {', '.join(missing_files)}")
    
    # Check data folder
    data_folder = Path("data_folder")
    output_folder = data_folder / "output"
    
    if data_folder.exists():
        print("✅ Data folder: Found")
    else:
        print("❌ Data folder: Not found")
    
    if output_folder.exists():
        print("✅ Output folder: Found")
    else:
        print("❌ Output folder: Not found")
    
    print("\n" + "=" * 50)
    input("\nPress Enter to return to main menu...")

def show_help():
    """Show help information."""
    help_text = """
    📖 Help & Documentation
    =====================
    
    🚀 Quick Start:
    1. Run setup wizard to configure the system
    2. Choose between Web UI or CLI interface
    3. Generate resumes and cover letters
    4. Manage job applications
    
    🌐 Web UI Features:
    • Modern, intuitive interface
    • Real-time progress updates
    • Easy configuration management
    • Document generation and preview
    • Application tracking
    
    💻 CLI Features:
    • Command-line interface
    • Scriptable automation
    • Batch operations
    • Advanced configuration options
    
    📁 File Structure:
    • data_folder/secrets.yaml - API keys and credentials
    • data_folder/work_preferences.yaml - Job search preferences
    • data_folder/plain_text_resume.yaml - Your resume data
    • data_folder/output/ - Generated documents
    
    🔧 Configuration:
    • OpenAI API key required for AI features
    • Email configuration for automated applications
    • Resume and work preferences setup
    
    🆘 Support:
    • Check system status for configuration issues
    • Review USER_GUIDE.md for detailed instructions
    • Run setup wizard if configuration is missing
    
    """
    print(help_text)
    input("\nPress Enter to return to main menu...")

def main_menu():
    """Display the main menu and handle user choices."""
    while True:
        clear_screen()
        print_banner()
        
        # Show configuration status
        configured, missing_files = check_configuration()
        if configured:
            print("✅ System Status: Ready to use")
        else:
            print("⚠️  System Status: Configuration required")
        
        print("\n📋 Choose your interface:")
        print("1. 🌐 Web UI (Recommended)")
        print("2. 💻 Command Line Interface (CLI)")
        print("3. 🔧 Setup Wizard")
        print("4. 📊 System Status")
        print("5. 📖 Help & Documentation")
        print("6. 🚪 Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == '1':
            if not check_dependencies():
                input("\nPress Enter to continue...")
                continue
            start_web_ui()
        elif choice == '2':
            if not check_dependencies():
                input("\nPress Enter to continue...")
                continue
            start_cli()
        elif choice == '3':
            run_setup_wizard()
        elif choice == '4':
            show_status()
        elif choice == '5':
            show_help()
        elif choice == '6':
            print("\n👋 Thank you for using Job Application Automation!")
            print("Good luck with your job search! 🍀")
            sys.exit(0)
        else:
            print("\n❌ Invalid choice. Please enter a number between 1-6.")
            input("Press Enter to continue...")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n\n👋 Goodbye!")
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handler for graceful exit
    signal.signal(signal.SIGINT, signal_handler)
    
    # Check if running with command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--web' or sys.argv[1] == '-w':
            start_web_ui()
        elif sys.argv[1] == '--cli' or sys.argv[1] == '-c':
            start_cli()
        elif sys.argv[1] == '--setup' or sys.argv[1] == '-s':
            run_setup_wizard()
        elif sys.argv[1] == '--help' or sys.argv[1] == '-h':
            print("""
Job Application Automation Launcher

Usage:
  python launcher.py [OPTIONS]

Options:
  -w, --web     Start Web UI interface
  -c, --cli     Start CLI interface
  -s, --setup   Run setup wizard
  -h, --help    Show this help message

Interactive Mode:
  python launcher.py    Show interactive menu
            """)
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Use --help for available options")
    else:
        # Run interactive menu
        main_menu() 