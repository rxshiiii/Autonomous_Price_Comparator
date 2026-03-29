"""
Email service integration with SendGrid for notification delivery.
"""
from typing import Dict, List, Optional
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from jinja2 import Environment, FileSystemLoader, TemplateNotFoundError
import json
import structlog
from datetime import datetime

from app.config import settings
from app.models.notification import Notification
from app.models.user import User


logger = structlog.get_logger()


class EmailService:
    """SendGrid email service for notification delivery."""

    def __init__(self):
        """Initialize SendGrid client and Jinja2 environment."""
        self.sg_client = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)

        # Set up Jinja2 template environment
        template_dir = os.path.join(os.path.dirname(__file__), "..", "templates", "emails")
        self.template_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True
        )

        self.from_email = settings.FROM_EMAIL
        self.logger = logger.bind(service="email_service")

    async def send_notification_email(
        self,
        user: User,
        notification: Notification,
        template_name: Optional[str] = None
    ) -> bool:
        """
        Send notification email to user.

        Args:
            user: User to send email to
            notification: Notification object
            template_name: Custom template name (auto-detected if None)

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Auto-detect template based on notification type
            if not template_name:
                template_name = self._get_template_name(notification.notification_type)

            # Prepare template data
            template_data = {
                "user_name": user.full_name or user.email.split("@")[0],
                "notification": {
                    "title": notification.title,
                    "message": notification.message,
                    "type": notification.notification_type,
                    "data": notification.data or {},
                    "created_at": notification.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
                },
                "unsubscribe_url": self._get_unsubscribe_url(user.id),
                "app_url": settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else "https://pricecomparator.com"
            }

            # Render email content
            subject = self._get_email_subject(notification)
            html_content = self._render_template(template_name, template_data)
            text_content = self._extract_text_content(notification)

            # Send email
            success = await self._send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )

            if success:
                self.logger.info(
                    "notification_email_sent",
                    user_id=str(user.id),
                    notification_id=str(notification.id),
                    notification_type=notification.notification_type,
                    template=template_name
                )
            else:
                self.logger.error(
                    "notification_email_failed",
                    user_id=str(user.id),
                    notification_id=str(notification.id)
                )

            return success

        except Exception as e:
            self.logger.error(
                "send_notification_email_error",
                error=str(e),
                user_id=str(user.id),
                notification_id=str(notification.id)
            )
            return False

    async def send_price_drop_alert(
        self,
        user: User,
        product_data: Dict,
        price_change: Dict
    ) -> bool:
        """
        Send dedicated price drop alert email.

        Args:
            user: User to send email to
            product_data: Product information
            price_change: Price change details

        Returns:
            True if sent successfully
        """
        try:
            template_data = {
                "user_name": user.full_name or user.email.split("@")[0],
                "product": product_data,
                "price_change": price_change,
                "savings": price_change.get("old_price", 0) - price_change.get("new_price", 0),
                "unsubscribe_url": self._get_unsubscribe_url(user.id),
                "app_url": settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else "https://pricecomparator.com"
            }

            subject = f"🎉 Price Drop Alert: {product_data.get('name', 'Product')} - Save ₹{template_data['savings']:,.0f}!"
            html_content = self._render_template("price_drop_alert.html", template_data)
            text_content = f"""
Price Drop Alert!

{product_data.get('name')} has dropped in price:
- Old Price: ₹{price_change.get('old_price', 0):,.0f}
- New Price: ₹{price_change.get('new_price', 0):,.0f}
- You Save: ₹{template_data['savings']:,.0f}

View Product: {product_data.get('url', '#')}
"""

            success = await self._send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )

            self.logger.info(
                "price_drop_email_sent",
                user_id=str(user.id),
                product_name=product_data.get('name'),
                savings=template_data['savings'],
                success=success
            )

            return success

        except Exception as e:
            self.logger.error("send_price_drop_alert_error", error=str(e), user_id=str(user.id))
            return False

    async def send_weekly_summary(self, user: User, summary_data: Dict) -> bool:
        """
        Send weekly notification summary email.

        Args:
            user: User to send email to
            summary_data: Weekly summary data

        Returns:
            True if sent successfully
        """
        try:
            template_data = {
                "user_name": user.full_name or user.email.split("@")[0],
                "week_start": summary_data.get("week_start"),
                "week_end": summary_data.get("week_end"),
                "summary": summary_data,
                "unsubscribe_url": self._get_unsubscribe_url(user.id),
                "app_url": settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else "https://pricecomparator.com"
            }

            subject = f"📊 Your Weekly Price Summary - {summary_data.get('total_alerts', 0)} Alerts This Week"
            html_content = self._render_template("weekly_summary.html", template_data)
            text_content = f"""
Your Weekly Price Summary

This week you received {summary_data.get('total_alerts', 0)} price alerts.
Total potential savings: ₹{summary_data.get('total_savings', 0):,.0f}

Visit your dashboard to see more details.
"""

            success = await self._send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )

            self.logger.info("weekly_summary_email_sent", user_id=str(user.id), success=success)
            return success

        except Exception as e:
            self.logger.error("send_weekly_summary_error", error=str(e), user_id=str(user.id))
            return False

    async def send_test_email(self, user_email: str, test_message: str = "Test email") -> bool:
        """
        Send test email for debugging purposes.

        Args:
            user_email: Email address
            test_message: Test message content

        Returns:
            True if sent successfully
        """
        subject = "🧪 Test Email from Price Comparator"
        html_content = f"""
        <html>
            <body>
                <h2>Test Email</h2>
                <p>{test_message}</p>
                <p>Timestamp: {datetime.utcnow().isoformat()}</p>
            </body>
        </html>
        """
        text_content = f"Test Email: {test_message}\nTimestamp: {datetime.utcnow().isoformat()}"

        return await self._send_email(
            to_email=user_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )

    def _get_template_name(self, notification_type: str) -> str:
        """Get template name based on notification type."""
        template_mapping = {
            "price_drop": "price_drop_alert.html",
            "new_recommendation": "recommendation.html",
            "back_in_stock": "back_in_stock.html",
            "system_message": "system_message.html"
        }
        return template_mapping.get(notification_type, "general_notification.html")

    def _get_email_subject(self, notification: Notification) -> str:
        """Generate email subject based on notification."""
        subject_prefixes = {
            "price_drop": "🎉 Price Drop Alert:",
            "new_recommendation": "💡 New Recommendation:",
            "back_in_stock": "📦 Back in Stock:",
            "system_message": "📢 System Update:"
        }

        prefix = subject_prefixes.get(notification.notification_type, "📬 Notification:")
        return f"{prefix} {notification.title}"

    def _render_template(self, template_name: str, template_data: Dict) -> str:
        """Render Jinja2 template with data."""
        try:
            template = self.template_env.get_template(template_name)
            return template.render(**template_data)
        except TemplateNotFoundError:
            self.logger.warning("template_not_found", template=template_name)
            # Fallback to simple HTML
            return self._generate_fallback_html(template_data)
        except Exception as e:
            self.logger.error("template_render_error", error=str(e), template=template_name)
            return self._generate_fallback_html(template_data)

    def _generate_fallback_html(self, template_data: Dict) -> str:
        """Generate simple fallback HTML when template is missing."""
        notification = template_data.get("notification", {})
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #333;">{notification.get('title', 'Notification')}</h2>
                <p style="color: #666; font-size: 16px;">
                    Hello {template_data.get('user_name', 'there')},
                </p>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p>{notification.get('message', 'You have a new notification.')}</p>
                </div>
                <p style="color: #999; font-size: 12px;">
                    Sent at {notification.get('created_at', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'))}
                </p>
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="color: #999; font-size: 11px; text-align: center;">
                    <a href="{template_data.get('unsubscribe_url', '#')}">Unsubscribe</a> |
                    <a href="{template_data.get('app_url', '#')}">Visit App</a>
                </p>
            </body>
        </html>
        """

    def _extract_text_content(self, notification: Notification) -> str:
        """Extract plain text content from notification."""
        return f"""
{notification.title}

{notification.message}

---
Sent at {notification.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
        """

    def _get_unsubscribe_url(self, user_id: str) -> str:
        """Generate unsubscribe URL for user."""
        base_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else "https://pricecomparator.com"
        return f"{base_url}/unsubscribe?user_id={user_id}"

    async def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str
    ) -> bool:
        """
        Send email via SendGrid.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content
            text_content: Plain text content

        Returns:
            True if sent successfully
        """
        try:
            # Create SendGrid mail object
            mail = Mail(
                from_email=Email(self.from_email),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content),
                plain_text_content=Content("text/plain", text_content)
            )

            # Send email
            response = self.sg_client.send(mail)

            # Check response status
            success = 200 <= response.status_code < 300

            if success:
                self.logger.info(
                    "email_sent_successfully",
                    to_email=to_email,
                    subject=subject,
                    status_code=response.status_code
                )
            else:
                self.logger.error(
                    "email_send_failed",
                    to_email=to_email,
                    status_code=response.status_code,
                    response_body=response.body
                )

            return success

        except Exception as e:
            self.logger.error("email_send_error", error=str(e), to_email=to_email)
            return False


# Global email service instance
email_service = EmailService()