from pyzk2 import ZK
from datetime import datetime, timezone as dt_timezone
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase

from apps.organization.models import Organization
from apps.employee.services import EmployeeService

from apps.attendance.models import (
    AttendanceDevice,
    AttendanceDeviceEmployee,
    AttendanceEvent,
    AttendanceRecord,
    AttendanceException,
)

from apps.attendance.services import (
    AttendanceDeviceService,
)

from apps.attendance.integrations.fa210 import (
    FA210Adapter,
)

DEVICE_IP = "10.0.0.151"
DEVICE_PORT = 4370


def main():
    connection = None

    zk = ZK(
        DEVICE_IP,
        port=DEVICE_PORT,
        timeout=10,
        password=0,
        force_udp=False,
        ommit_ping=False,
    )

    try:
        print("Connecting to FA210-Plus...")

        connection = zk.connect()

        print("CONNECTED")
        print()

        print("Device Information")
        print("------------------")

        try:
            print(
                "Device Name:",
                connection.get_device_name(),
            )
        except Exception as exc:
            print(
                "Device Name: ERROR -",
                exc,
            )

        try:
            print(
                "Serial Number:",
                connection.get_serialnumber(),
            )
        except Exception as exc:
            print(
                "Serial Number: ERROR -",
                exc,
            )

        try:
            print(
                "Firmware:",
                connection.get_firmware_version(),
            )
        except Exception as exc:
            print(
                "Firmware: ERROR -",
                exc,
            )

        try:
            print(
                "Platform:",
                connection.get_platform(),
            )
        except Exception as exc:
            print(
                "Platform: ERROR -",
                exc,
            )

        print()
        print("Reading attendance records...")

        attendance = connection.get_attendance()

        print(
            "Attendance records:",
            len(attendance),
        )

        for record in attendance[:10]:
            print(record)

    except Exception as exc:
        print()
        print("CONNECTION FAILED")
        print(type(exc).__name__)
        print(str(exc))

    finally:
        if connection:
            connection.disconnect()
            print()
            print("Disconnected.")


if __name__ == "__main__":
    main()
