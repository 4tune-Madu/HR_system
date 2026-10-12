from datetime import datetime

from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from apps.attendance.models import (
    AttendanceDevice,
    AttendanceSyncLog,
)

from apps.attendance.services import (
    AttendanceSyncService,
)


class Command(BaseCommand):

    help = (
        "Synchronize attendance records from "
        "attendance devices."
    )

    def add_arguments(
        self,
        parser,
    ):
        parser.add_argument(
            "--device",
            type=str,
            help=(
                "Attendance device UUID."
            ),
        )

        parser.add_argument(
            "--serial",
            type=str,
            help=(
                "Attendance device serial number."
            ),
        )

        parser.add_argument(
            "--all",
            action="store_true",
            help=(
                "Synchronize all active network "
                "attendance devices."
            ),
        )

        parser.add_argument(
            "--from-date",
            type=str,
            help=(
                "Only process attendance on or "
                "after YYYY-MM-DD."
            ),
        )

        parser.add_argument(
            "--to-date",
            type=str,
            help=(
                "Only process attendance on or "
                "before YYYY-MM-DD."
            ),
        )

    def handle(
        self,
        *args,
        **options,
    ):
        device_id = options.get(
            "device"
        )

        serial = options.get(
            "serial"
        )

        synchronize_all = options.get(
            "all"
        )

        selected_count = sum(
            bool(value)
            for value in [
                device_id,
                serial,
                synchronize_all,
            ]
        )

        if selected_count != 1:
            raise CommandError(
                "Use exactly one of "
                "--device, --serial, or --all."
            )

        start_date = self.parse_date(
            options.get("from_date")
        )

        end_date = self.parse_date(
            options.get("to_date")
        )

        if (
            start_date is not None
            and end_date is not None
            and end_date < start_date
        ):
            raise CommandError(
                "--to-date cannot be earlier "
                "than --from-date."
            )

        # -----------------------------------
        # Resolve devices
        # -----------------------------------

        if synchronize_all:

            devices = list(
                AttendanceDevice.objects.filter(
                    is_active=True,
                    connection_type=(
                        AttendanceDevice
                        .ConnectionType
                        .NETWORK
                    ),
                )
                .order_by("name")
            )

            if not devices:
                raise CommandError(
                    "No active network attendance "
                    "devices were found."
                )

        elif device_id:

            try:

                device = (
                    AttendanceDevice.objects.get(
                        id=device_id,
                        is_active=True,
                    )
                )

            except AttendanceDevice.DoesNotExist:

                raise CommandError(
                    "Active attendance device "
                    "not found."
                )

            devices = [device]

        else:

            try:

                device = (
                    AttendanceDevice.objects.get(
                        serial_number=serial,
                        is_active=True,
                    )
                )

            except AttendanceDevice.DoesNotExist:

                raise CommandError(
                    "Active attendance device "
                    "with the supplied serial number "
                    "was not found."
                )

            devices = [device]

        # -----------------------------------
        # Totals
        # -----------------------------------

        total = {
            "records_read": 0,
            "records_in_range": 0,
            "created": 0,
            "duplicates": 0,
            "resolved_existing": 0,
            "unresolved": 0,
            "invalid": 0,
            "attendance_days_rebuilt": 0,
        }

        failed_devices = 0

        # -----------------------------------
        # Synchronize devices
        # -----------------------------------

        for device in devices:

            self.stdout.write(
                self.style.NOTICE(
                    f"Synchronizing "
                    f"{device.name} "
                    f"({device.serial_number})..."
                )
            )

            try:

                sync_log = (
                    AttendanceSyncService.run_sync(
                        device=device,
                        start_date=start_date,
                        end_date=end_date,
                        trigger=(
                            AttendanceSyncLog
                            .Trigger
                            .MANUAL
                        ),
                    )
                )

            except Exception as exc:

                failed_devices += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"Synchronization failed: "
                        f"{exc}"
                    )
                )

                self.stdout.write("")

                continue

            # -----------------------------------
            # Display synchronization result
            # -----------------------------------

            self.stdout.write(
                f"  Status: "
                f"{sync_log.status}"
            )

            self.stdout.write(
                f"  Records read: "
                f"{sync_log.records_read}"
            )

            self.stdout.write(
                f"  Records in range: "
                f"{sync_log.records_in_range}"
            )

            self.stdout.write(
                f"  Created: "
                f"{sync_log.created}"
            )

            self.stdout.write(
                f"  Duplicates: "
                f"{sync_log.duplicates}"
            )

            self.stdout.write(
                f"  Resolved existing: "
                f"{sync_log.resolved_existing}"
            )

            self.stdout.write(
                f"  Unresolved: "
                f"{sync_log.unresolved}"
            )

            self.stdout.write(
                f"  Invalid: "
                f"{sync_log.invalid}"
            )

            self.stdout.write(
                f"  Attendance days rebuilt: "
                f"{sync_log.attendance_days_rebuilt}"
            )

            if sync_log.error_message:

                self.stdout.write(
                    self.style.ERROR(
                        f"  Error: "
                        f"{sync_log.error_message}"
                    )
                )

            # -----------------------------------
            # Add to totals
            # -----------------------------------

            total[
                "records_read"
            ] += sync_log.records_read

            total[
                "records_in_range"
            ] += sync_log.records_in_range

            total[
                "created"
            ] += sync_log.created

            total[
                "duplicates"
            ] += sync_log.duplicates

            total[
                "resolved_existing"
            ] += sync_log.resolved_existing

            total[
                "unresolved"
            ] += sync_log.unresolved

            total[
                "invalid"
            ] += sync_log.invalid

            total[
                "attendance_days_rebuilt"
            ] += (
                sync_log
                .attendance_days_rebuilt
            )

            self.stdout.write("")

        # -----------------------------------
        # Overall result
        # -----------------------------------

        if failed_devices:

            self.stdout.write(
                self.style.ERROR(
                    "Attendance synchronization "
                    "completed with failures."
                )
            )

        else:

            self.stdout.write(
                self.style.SUCCESS(
                    "Attendance synchronization "
                    "completed successfully."
                )
            )

        # -----------------------------------
        # Totals
        # -----------------------------------

        self.stdout.write(
            f"Total records read: "
            f"{total['records_read']}"
        )

        self.stdout.write(
            f"Total records in range: "
            f"{total['records_in_range']}"
        )

        self.stdout.write(
            f"Total created: "
            f"{total['created']}"
        )

        self.stdout.write(
            f"Total duplicates: "
            f"{total['duplicates']}"
        )

        self.stdout.write(
            f"Total resolved existing: "
            f"{total['resolved_existing']}"
        )

        self.stdout.write(
            f"Total unresolved: "
            f"{total['unresolved']}"
        )

        self.stdout.write(
            f"Total invalid: "
            f"{total['invalid']}"
        )

        self.stdout.write(
            f"Total attendance days rebuilt: "
            f"{total['attendance_days_rebuilt']}"
        )

        if failed_devices:

            raise CommandError(
                f"{failed_devices} attendance "
                f"device synchronization(s) failed."
            )

    @staticmethod
    def parse_date(
        value,
    ):
        if not value:
            return None

        try:

            return datetime.strptime(
                value,
                "%Y-%m-%d",
            ).date()

        except ValueError:

            raise CommandError(
                "Dates must use YYYY-MM-DD format."
            )