import os
import runpy
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase


class ProductionSettingsTests(SimpleTestCase):
    def setUp(self):
        self.environment = {
            "SECRET_KEY": "test-only-production-settings-secret-" * 3,
            "ALLOWED_HOSTS": "hr.example.test, hr-backup.example.test",
            "APP_BASE_URL": "https://hr.example.test/",
            "DB_NAME": "hr_test", "DB_USER": "hr_test",
            "DB_PASSWORD": "test-only", "DB_HOST": "localhost",
            "EMAIL_HOST": "smtp.example.test",
            "DEFAULT_FROM_EMAIL": "hr@example.test",
            "STATIC_ROOT": "C:/HRSystem/data/static",
            "MEDIA_ROOT": "C:/HRSystem/data/media",
            "CELERY_BROKER_URL": "redis://worker.example.test:6379/0",
            "CELERY_RESULT_BACKEND": "redis://worker.example.test:6379/1",
        }

    def load_settings(self):
        with patch.dict(os.environ, self.environment, clear=True):
            return runpy.run_module("config.settings.production")

    def test_configured_production_uses_external_services_and_https(self):
        settings = self.load_settings()
        self.assertFalse(settings["DEBUG"])
        self.assertEqual(settings["DATABASES"]["default"]["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(settings["ALLOWED_HOSTS"], ["hr.example.test", "hr-backup.example.test"])
        self.assertEqual(settings["CORS_ALLOWED_ORIGINS"], [])
        self.assertEqual(settings["EMAIL_BACKEND"], "django.core.mail.backends.smtp.EmailBackend")
        self.assertTrue(settings["SECURE_SSL_REDIRECT"])
        self.assertTrue(settings["SESSION_COOKIE_SECURE"])
        self.assertTrue(settings["CSRF_COOKIE_SECURE"])
        self.assertIsNone(settings.get("SECURE_PROXY_SSL_HEADER"))

    def test_required_configuration_cannot_be_omitted(self):
        for name in self.environment:
            with self.subTest(name=name):
                environment = self.environment.copy()
                del environment[name]
                with patch.dict(os.environ, environment, clear=True):
                    with self.assertRaises(ImproperlyConfigured):
                        runpy.run_module("config.settings.production")

    def test_unsafe_values_are_rejected(self):
        for name, value in [
            ("SECRET_KEY", "replace-" + "x" * 60),
            ("ALLOWED_HOSTS", "*"),
            ("APP_BASE_URL", "http://hr.example.test"),
            ("EMAIL_USE_SSL", "true"),
        ]:
            with self.subTest(name=name):
                environment = {**self.environment, name: value}
                with patch.dict(os.environ, environment, clear=True):
                    with self.assertRaises(ImproperlyConfigured):
                        runpy.run_module("config.settings.production")

    def test_proxy_https_requires_explicit_opt_in(self):
        self.environment["TRUST_PROXY_HTTPS"] = "true"
        settings = self.load_settings()
        self.assertEqual(settings["SECURE_PROXY_SSL_HEADER"], ("HTTP_X_FORWARDED_PROTO", "https"))
