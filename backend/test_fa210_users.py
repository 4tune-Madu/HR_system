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

        users = connection.get_users()

        print(
            f"Total users: {len(users)}\n"
        )

        for user in users[:10]:

            print("=" * 60)
            print(user)
            print("=" * 60)

            print(
                getattr(
                    user,
                    "__dict__",
                    "No __dict__ available",
                )
            )

            for attribute in [
                "uid",
                "user_id",
                "name",
                "privilege",
                "password",
                "card",
            ]:
                try:
                    print(
                        f"{attribute}: "
                        f"{getattr(user, attribute)}"
                    )
                except AttributeError:
                    print(
                        f"{attribute}: <not available>"
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