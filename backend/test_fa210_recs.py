from pyzk2 import ZK


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
        print("Connecting...")

        connection = zk.connect()

        print("Connected.\n")

        attendance = connection.get_attendance()

        print(
            f"Total attendance records: {len(attendance)}\n"
        )

        for index, record in enumerate(
            attendance[:50],
            start=1,
        ):
            print("=" * 60)
            print(f"Record #{index}")
            print("\nAttributes:")
            print(
                getattr(
                    record,
                    "__dict__",
                    "No __dict__ available",
                )
            )

          
            print()

    except Exception as exc:
        print(
            f"{type(exc).__name__}: {exc}"
        )

    finally:
        if connection:
            connection.disconnect()
            print("Disconnected.")


if __name__ == "__main__":
    main()