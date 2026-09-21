from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import (
    default_token_generator,
)
from django.utils.http import (
    urlsafe_base64_decode,
    urlsafe_base64_encode,
)
from django.conf import settings
from django.utils.encoding import (
    force_bytes,
)
from apps.core.email_service import EmailService
User = get_user_model()

class AccountService:

    @staticmethod
    def generate_password_setup_token(
        *,
        user,
    ):
        return default_token_generator.make_token(
            user
        )

    @staticmethod
    def generate_password_setup_url(
        *,
        user,
    ):
        uidb64 = urlsafe_base64_encode(
            force_bytes(user.pk)
        )

        token = (
            AccountService
            .generate_password_setup_token(
                user=user,
            )
        )

        base_url = (
            settings.APP_BASE_URL.rstrip("/")
        )

        return (
            f"{base_url}"
            f"/api/auth/account/setup/"
            f"{uidb64}/{token}/"
        )



    @staticmethod
    def validate_password_setup_token(
        *,
        uidb64,
        token,
    ):
        try:
            uid = urlsafe_base64_decode(
                uidb64
            ).decode()

            user = User.objects.get(
                pk=uid
            )

        except (
            TypeError,
            ValueError,
            OverflowError,
            User.DoesNotExist,
        ):
            raise ValueError(
                "Invalid password setup link."
            )

        if not default_token_generator.check_token(
            user,
            token,
        ):
            raise ValueError(
                "Invalid or expired password setup link."
            )

        return user

    @staticmethod
    def set_password(
        *,
        user,
        password,
    ):
        if not user.password_reset_required:
            raise ValueError(
                "Password setup is not required for this account."
            )
    
        user.set_password(password)
    
        user.password_reset_required = False
    
        user.save(
            update_fields=[
                "password",
                "password_reset_required",
            ]
        )
    
        return user

    @staticmethod
    def generate_password_setup_link(
        *,
        user,
        base_url,
    ):
        uidb64 = urlsafe_base64_encode(
            force_bytes(user.pk)
        )

        token = (
            AccountService
            .generate_password_setup_token(
                user=user,
            )
        )

        return (
            f"{base_url}/auth/account/setup/"
            f"{uidb64}/{token}/"
        )


    @staticmethod
    def send_password_setup_invitation(
        *,
        user,
    ):
        if not user.is_active:
            raise ValueError(
                "Cannot send an invitation to an inactive account."
            )

        if not user.password_reset_required:
            raise ValueError(
                "Password setup is not required "
                "for this account."
            )

        setup_url = (
            AccountService
            .generate_password_setup_url(
                user=user,
            )
        )

        EmailService.send_employee_account_invitation(
            user=user,
            setup_url=setup_url,
        )

        return setup_url