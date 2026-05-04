"""
Notifier - Handles notifications and alerts.
"""

import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import Optional

from loguru import logger

from .config import Settings


class Notifier:
    """
    Notification handler for Naukri Profile Tracker.
    
    Supports:
    - Email notifications
    - Console logging
    - Future: Push notifications, Slack, Telegram
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize Notifier.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.enabled = settings.notification_enabled
    
    async def send_notification(
        self,
        subject: str,
        message: str,
        priority: str = "normal"
    ) -> bool:
        """
        Send a notification.
        
        Args:
            subject: Notification subject/title
            message: Notification body
            priority: Priority level ('low', 'normal', 'high')
        
        Returns:
            bool: True if notification sent successfully
        """
        if not self.enabled:
            logger.debug(f"Notifications disabled. Would send: {subject}")
            return True
        
        logger.info(f"Sending notification: {subject}")
        
        # Log to console
        self._log_notification(subject, message, priority)
        
        # Send email if configured
        if self.settings.notification_email and self.settings.smtp_username:
            await self._send_email(subject, message)
        
        return True
    
    def _log_notification(self, subject: str, message: str, priority: str) -> None:
        """Log notification to console/file."""
        if priority == "high":
            logger.warning(f"🔔 [ALERT] {subject}: {message}")
        else:
            logger.info(f"📬 [NOTIFICATION] {subject}: {message}")
    
    async def _send_email(self, subject: str, message: str) -> bool:
        """
        Send email notification.
        
        Args:
            subject: Email subject
            message: Email body
        
        Returns:
            bool: True if email sent successfully
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = self.settings.smtp_username
            msg['To'] = self.settings.notification_email
            msg['Subject'] = f"[Naukri Tracker] {subject}"
            
            # Create HTML email body
            html_body = self._create_email_body(subject, message)
            msg.attach(MIMEText(html_body, 'html'))
            
            # Connect and send
            with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as server:
                server.starttls()
                server.login(
                    self.settings.smtp_username,
                    self.settings.smtp_password.get_secret_value()
                )
                server.send_message(msg)
            
            logger.info(f"Email sent to {self.settings.notification_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def _create_email_body(self, subject: str, message: str) -> str:
        """Create HTML email body."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #0066cc; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .footer {{ text-align: center; padding: 10px; font-size: 12px; color: #666; }}
                .highlight {{ background: #e6f3ff; padding: 10px; border-left: 3px solid #0066cc; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Naukri Profile Tracker</h2>
                </div>
                <div class="content">
                    <h3>{subject}</h3>
                    <div class="highlight">
                        <pre>{message}</pre>
                    </div>
                    <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                <div class="footer">
                    <p>This is an automated notification from Naukri Profile Tracker</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    async def send_daily_summary(self, summary: dict) -> bool:
        """
        Send daily activity summary.
        
        Args:
            summary: Daily summary data
        
        Returns:
            bool: True if sent successfully
        """
        subject = f"Daily Summary - {datetime.now().strftime('%Y-%m-%d')}"
        
        message = f"""
Daily Activity Summary
======================

Profile Views: {summary.get('profile_views', 'N/A')}
New Messages: {summary.get('new_messages', 0)}
Interview Requests: {summary.get('interview_requests', 0)}
Jobs Recommended: {summary.get('jobs_recommended', 0)}
Resume Updated: {'Yes' if summary.get('resume_updated') else 'No'}

Applications Status:
{self._format_applications(summary.get('applications', []))}

Have a great day!
        """
        
        return await self.send_notification(subject, message, "normal")
    
    def _format_applications(self, applications: list) -> str:
        """Format applications list for display."""
        if not applications:
            return "  No active applications"
        
        lines = []
        for app in applications[:5]:  # Top 5
            lines.append(f"  - {app.get('title', 'N/A')} at {app.get('company', 'N/A')}: {app.get('status', 'N/A')}")
        
        return "\n".join(lines)
    
    async def send_alert(self, alert_type: str, details: dict) -> bool:
        """
        Send a high-priority alert.
        
        Args:
            alert_type: Type of alert
            details: Alert details
        
        Returns:
            bool: True if sent successfully
        """
        subject = f"🚨 Alert: {alert_type}"
        message = f"""
ALERT: {alert_type}
====================

{self._format_alert_details(details)}

Please check your Naukri account for more details.
        """
        
        return await self.send_notification(subject, message, "high")
    
    def _format_alert_details(self, details: dict) -> str:
        """Format alert details."""
        lines = []
        for key, value in details.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)
