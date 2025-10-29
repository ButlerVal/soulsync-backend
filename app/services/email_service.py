import logging

logger = logging.getLogger(__name__)

class MockEmailService:
    """
    Mock email service that logs to the console instead of sending real emails.
    Mimics the interface needed for password reset.
    """

    async def send_password_reset_email(self, email_to: str, reset_token: str):
        """
        Simulates sending a password reset email.
        """
        # In a real app, you'd use a service like SendGrid
        # and an HTML template.

        # The URL the user would click in the email
        # (The frontend will handle this route)
        reset_url = f"http://localhost:5173/reset-password?token={reset_token}"

        logger.info("--- MOCK EMAIL SENDER ---")
        logger.info(f"To: {email_to}")
        logger.info("From: noreply@soulsync.com")
        logger.info("Subject: Reset Your SoulSync Password")
        logger.info("")
        logger.info("You requested a password reset.")
        logger.info(f"Click this link to reset your password: {reset_url}")
        logger.info("(This email is mocked and printed to the console.)")
        logger.info("---------------------------")

        return True # Simulate successful sending

# Create a single instance
email_service = MockEmailService()