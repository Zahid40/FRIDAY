import os
import smtplib
import webbrowser
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from langchain.tools import tool

@tool("send_email")
def send_email(recipient: str, subject: str, body: str) -> str:
    """
    Sends an email using SMTP. Reads credentials (EMAIL_USER, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT) from the system environment/.env.
    Input parameters:
    - recipient: the email address of the receiver
    - subject: email subject line
    - body: body content of the email
    """
    sender = os.environ.get("EMAIL_USER")
    password = os.environ.get("EMAIL_PASSWORD")
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    
    if not sender or not password:
        return "Error: Email credentials (EMAIL_USER/EMAIL_PASSWORD) not configured in .env file."
        
    try:
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())
        server.quit()
        
        return f"Email sent successfully to {recipient}."
    except Exception as e:
        return f"Failed to send email: {e}"

@tool("send_whatsapp_message")
def send_whatsapp_message(phone: str, message: str) -> str:
    """
    Sends a WhatsApp message by launching WhatsApp Web or native client with pre-filled text.
    Input parameters:
    - phone: phone number with country code (e.g. +919876543210 or 919876543210)
    - message: message content
    """
    clean_phone = "".join(filter(str.isdigit, phone))
    encoded_message = urllib.parse.quote(message)
    
    # Standard URL for WhatsApp Web API
    url = f"https://web.whatsapp.com/send?phone={clean_phone}&text={encoded_message}"
    
    try:
        webbrowser.open(url)
        return f"Opened WhatsApp Web with pre-filled message for {phone}."
    except Exception as e:
        return f"Failed to open WhatsApp: {e}"
