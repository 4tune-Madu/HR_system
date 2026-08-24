from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.http import (
    urlsafe_base64_encode,
)
from apps.authentication.services import AccountService
from django.utils.encoding import force_bytes
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from django.core import mail

User = get_user_model()


class AuthenticationAPITests(APITestCase):

    def setUp(self):

        # -----------------------------------
        # User
        # -----------------------------------

        self.user = User.objects.create_user(
            email="test@example.com",
            password="TestPassword123!",
            first_name="Test",
            last_name="User",
        )

    # =================================================
    # Login
    # =================================================

    def test_login(self):

        response = self.client.post(
            "/api/auth/login/",
            {
                "email": "test@example.com",
                "password": "TestPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "access",
            response.data,
        )

        self.assertIn(
            "refresh",
            response.data,
        )

    def test_login_with_invalid_password(self):

        response = self.client.post(
            "/api/auth/login/",
            {
                "email": "test@example.com",
                "password": "WrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_login_with_unknown_email(self):

        response = self.client.post(
            "/api/auth/login/",
            {
                "email": "unknown@example.com",
                "password": "TestPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    # =================================================
    # Me
    # =================================================

    def test_me(self):

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            "/api/auth/me/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["email"],
            self.user.email,
        )

        self.assertEqual(
            response.data["first_name"],
            self.user.first_name,
        )

        self.assertEqual(
            response.data["last_name"],
            self.user.last_name,
        )

    def test_me_requires_authentication(self):

        response = self.client.get(
            "/api/auth/me/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    # =================================================
    # Logout
    # =================================================

    def test_logout(self):

        self.client.force_authenticate(
            user=self.user,
        )

        refresh = RefreshToken.for_user(
            self.user
        )

        response = self.client.post(
            "/api/auth/logout/",
            {
                "refresh": str(refresh),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["detail"],
            "Successfully logged out.",
        )

    def test_logout_requires_refresh_token(self):

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.post(
            "/api/auth/logout/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            response.data["detail"],
            "Refresh token is required.",
        )

    def test_logout_rejects_invalid_refresh_token(self):

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.post(
            "/api/auth/logout/",
            {
                "refresh": "invalid-refresh-token",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            response.data["detail"],
            "Invalid refresh token.",
        )

    # =================================================
    # Password Setup Helpers
    # =================================================

    def create_password_setup_user(self):

        user = User.objects.create_user(
            email="newemployee@example.com",
            first_name="New",
            last_name="Employee",
        )

        user.set_unusable_password()

        user.password_reset_required = True

        user.save(
            update_fields=[
                "password",
                "password_reset_required",
            ]
        )

        uidb64 = urlsafe_base64_encode(
            force_bytes(str(user.pk))
        )

        token = (
            default_token_generator.make_token(
                user
            )
        )

        return user, uidb64, token


    # =================================================
    # Password Setup
    # =================================================

    def test_set_password(self):

        user, uidb64, token = (
            self.create_password_setup_user()
        )

        self.assertTrue(
            user.password_reset_required
        )

        self.assertFalse(
            user.has_usable_password()
        )

        response = self.client.post(
            (
                f"/api/auth/account/setup/"
                f"{uidb64}/{token}/"
            ),
            {
                "password": "NewPassword123!",
                "password_confirmation": (
                    "NewPassword123!"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["detail"],
            "Password successfully set.",
        )

        user.refresh_from_db()

        self.assertFalse(
            user.password_reset_required
        )

        self.assertTrue(
            user.has_usable_password()
        )

        self.assertTrue(
            user.check_password(
                "NewPassword123!"
            )
        )


    def test_set_password_requires_matching_passwords(
        self,
    ):

        user, uidb64, token = (
            self.create_password_setup_user()
        )

        response = self.client.post(
            (
                f"/api/auth/account/setup/"
                f"{uidb64}/{token}/"
            ),
            {
                "password": "NewPassword123!",
                "password_confirmation": (
                    "DifferentPassword123!"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        user.refresh_from_db()

        self.assertTrue(
            user.password_reset_required
        )

        self.assertFalse(
            user.has_usable_password()
        )


    def test_set_password_rejects_invalid_token(self):

        user, uidb64, token = (
            self.create_password_setup_user()
        )

        response = self.client.post(
            (
                f"/api/auth/account/setup/"
                f"{uidb64}/"
                "invalid-token/"
            ),
            {
                "password": "NewPassword123!",
                "password_confirmation": (
                    "NewPassword123!"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        user.refresh_from_db()

        self.assertTrue(
            user.password_reset_required
        )

        self.assertFalse(
            user.has_usable_password()
        )


    def test_set_password_rejects_invalid_uid(self):

        user, uidb64, token = (
            self.create_password_setup_user()
        )

        response = self.client.post(
            (
                "/api/auth/account/setup/"
                "invalid-uid/"
                f"{token}/"
            ),
            {
                "password": "NewPassword123!",
                "password_confirmation": (
                    "NewPassword123!"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        user.refresh_from_db()

        self.assertTrue(
            user.password_reset_required
        )

        self.assertFalse(
            user.has_usable_password()
        )


    def test_set_password_cannot_be_reused(self):

        user, uidb64, token = (
            self.create_password_setup_user()
        )

        first_response = self.client.post(
            (
                f"/api/auth/account/setup/"
                f"{uidb64}/{token}/"
            ),
            {
                "password": "NewPassword123!",
                "password_confirmation": (
                    "NewPassword123!"
                ),
            },
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_200_OK,
        )

        user.refresh_from_db()

        self.assertFalse(
            user.password_reset_required
        )

        self.assertTrue(
            user.has_usable_password()
        )

        second_response = self.client.post(
            (
                f"/api/auth/account/setup/"
                f"{uidb64}/{token}/"
            ),
            {
                "password": "AnotherPassword123!",
                "password_confirmation": (
                    "AnotherPassword123!"
                ),
            },
            format="json",
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )


    def test_set_password_rejects_account_that_does_not_require_setup(
        self,
    ):

        user = User.objects.create_user(
            email="normal@example.com",
            password="ExistingPassword123!",
            first_name="Normal",
            last_name="User",
        )

        self.assertFalse(
            user.password_reset_required
        )

        self.assertTrue(
            user.has_usable_password()
        )

        uidb64 = urlsafe_base64_encode(
            force_bytes(str(user.pk))
        )

        token = (
            default_token_generator.make_token(
                user
            )
        )

        response = self.client.post(
            (
                f"/api/auth/account/setup/"
                f"{uidb64}/{token}/"
            ),
            {
                "password": "NewPassword123!",
                "password_confirmation": (
                    "NewPassword123!"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        user.refresh_from_db()

        self.assertFalse(
            user.password_reset_required
        )

        self.assertTrue(
            user.check_password(
                "ExistingPassword123!"
            )
        )


    def test_set_password_rejects_weak_password(
        self,
    ):

        user, uidb64, token = (
            self.create_password_setup_user()
        )

        response = self.client.post(
            (
                f"/api/auth/account/setup/"
                f"{uidb64}/{token}/"
            ),
            {
                "password": "123",
                "password_confirmation": "123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        user.refresh_from_db()

        self.assertTrue(
            user.password_reset_required
        )

        self.assertFalse(
            user.has_usable_password()
        )

    def test_send_password_setup_invitation(self):

        user = User.objects.create_user(
            email="employee@example.com",
            first_name="Jane",
            last_name="Smith",
        )

        user.set_unusable_password()

        user.password_reset_required = True

        user.save(
            update_fields=[
                "password",
                "password_reset_required",
            ]
        )

        setup_url = (
            AccountService
            .send_password_setup_invitation(
                user=user,
            )
        )

        self.assertEqual(
            len(mail.outbox),
            1,
        )

        email = mail.outbox[0]

        self.assertEqual(
            email.to,
            ["employee@example.com"],
        )

        self.assertIn(
            "Set up your HR Management System account",
            email.subject,
        )

        self.assertIn(
            setup_url,
            email.body,
        )

    def test_invitation_rejected_after_password_setup(
        self,
    ):

        user = User.objects.create_user(
            email="employee@example.com",
            password="ExistingPassword123!",
            first_name="Jane",
            last_name="Smith",
        )

        user.password_reset_required = False

        user.save(
            update_fields=[
                "password_reset_required",
            ]
        )

        with self.assertRaises(ValueError):

            AccountService.send_password_setup_invitation(
                user=user,
            )

    def test_provisioned_account_cannot_login_before_password_setup(
        self,
    ):
        user = User.objects.create_user(
            email="employee@example.com",
            first_name="Jane",
            last_name="Smith",
        )
    
        user.set_unusable_password()
    
        user.password_reset_required = True
    
        user.save(
            update_fields=[
                "password",
                "password_reset_required",
            ]
        )
    
        response = self.client.post(
            "/api/auth/login/",
            {
                "email": "employee@example.com",
                "password": "NewPassword123!",
            },
            format="json",
        )
    
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
    
    def test_employee_can_login_after_password_setup(
        self,
    ):
        user = User.objects.create_user(
            email="employee@example.com",
        )
    
        user.set_unusable_password()
    
        user.password_reset_required = True
    
        user.save(
            update_fields=[
                "password",
                "password_reset_required",
            ]
        )
    
        uidb64 = urlsafe_base64_encode(
            force_bytes(user.pk)
        )
    
        token = default_token_generator.make_token(
            user
        )
    
        setup_response = self.client.post(
            (
                f"/api/auth/account/setup/"
                f"{uidb64}/{token}/"
            ),
            {
                "password": "NewPassword123!",
                "password_confirmation": (
                    "NewPassword123!"
                ),
            },
            format="json",
        )
    
        self.assertEqual(
            setup_response.status_code,
            status.HTTP_200_OK,
        )
    
        login_response = self.client.post(
            "/api/auth/login/",
            {
                "email": "employee@example.com",
                "password": "NewPassword123!",
            },
            format="json",
        )
    
        self.assertEqual(
            login_response.status_code,
            status.HTTP_200_OK,
        )
    
        self.assertIn(
            "access",
            login_response.data,
        )
    
        self.assertIn(
            "refresh",
            login_response.data,
        )
    
    def test_password_setup_clears_reset_requirement(
        self,
    ):
        user = User.objects.create_user(
            email="employee@example.com",
        )
    
        user.set_unusable_password()
        user.password_reset_required = True
    
        user.save(
            update_fields=[
                "password",
                "password_reset_required",
            ]
        )
    
        uidb64 = urlsafe_base64_encode(
            force_bytes(user.pk)
        )
    
        token = default_token_generator.make_token(
            user
        )
    
        response = self.client.post(
            (
                f"/api/auth/account/setup/"
                f"{uidb64}/{token}/"
            ),
            {
                "password": "NewPassword123!",
                "password_confirmation": (
                    "NewPassword123!"
                ),
            },
            format="json",
        )
    
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
    
        user.refresh_from_db()
    
        self.assertFalse(
            user.password_reset_required,
        )
    
        self.assertTrue(
            user.has_usable_password(),
        )