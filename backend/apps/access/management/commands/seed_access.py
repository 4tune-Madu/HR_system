from django.core.management.base import BaseCommand

from apps.access.constants import PERMISSIONS
from apps.access.models import Permission, Role
from apps.access.roles import ROLE_PERMISSIONS


class Command(BaseCommand):

    help = "Seed default permissions and system roles."

    def handle(self, *args, **options):

        self.stdout.write(
            "Seeding permissions..."
        )

        permissions = {}

        for permission_data in PERMISSIONS:

            permission, created = (
                Permission.objects.update_or_create(
                    code=permission_data["code"],
                    defaults={
                        "name": permission_data["name"],
                        "description": permission_data[
                            "description"
                        ],
                    },
                )
            )

            permissions[permission.code] = permission

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created permission: "
                        f"{permission.code}"
                    )
                )
            else:
                self.stdout.write(
                    f"Updated permission: "
                    f"{permission.code}"
                )

        self.stdout.write(
            "Seeding roles..."
        )

        for role_code, permission_codes in (
            ROLE_PERMISSIONS.items()
        ):

            role, created = Role.objects.update_or_create(
                organization=None,
                code=role_code,
                defaults={
                    "name": role_code.replace(
                        "_",
                        " ",
                    ).title(),

                    "is_system_role": True,
                },
            )

            role.permissions.set(
                [
                    permissions[code]
                    for code in permission_codes
                ]
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created role: {role_code}"
                    )
                )
            else:
                self.stdout.write(
                    f"Updated role: {role_code}"
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Access data seeded successfully."
            )
        )