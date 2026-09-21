from django.conf import settings
from django.core.mail import send_mail


class EmailService:

    @staticmethod
    def send_employee_account_invitation(
        *,
        user,
        setup_url,
    ):
        subject = (
            "Set up your HR Management System account"
        )

        message = (
            f"Hello {user.first_name},\n\n"
            "An HR administrator has created an account "
            "for you on the HR Management System.\n\n"
            "Use the link below to set your password:\n\n"
            f"{setup_url}\n\n"
            "For security reasons, this link should only "
            "be used by you.\n\n"
            "Regards,\n"
            "HR Management System"
        )

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )