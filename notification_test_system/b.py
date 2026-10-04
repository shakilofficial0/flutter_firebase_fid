import asyncio

import firebase_admin

from firebase_admin import credentials, messaging


cred = credentials.Certificate("./development.json")

app_options = {
    "projectId": "shobarkhamar-01-dev",
}

firebase_admin.initialize_app(
    cred,
    app_options,
)


FIREBASE_INSTALLATION_ID = "dWpi1LboQ8ugOozHpHIgoj" # demo fid


async def send_multicast(fids: list[str]):
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title="Push Notification",
            body="This works immediately!",
        ),
        fids=fids,
    )

    response = await messaging.send_each_for_multicast_async(message)

    print(f"Success: {response.success_count}, Failure: {response.failure_count}")
    for fid, resp in zip(fids, response.responses):
        print(f"{fid}: raw={resp!r}")
        print(f"  success={resp.success} message_id={resp.message_id}")
        if resp.exception is not None:
            print(f"  exception={resp.exception!r}")
            print(f"  code={getattr(resp.exception, 'code', None)}")
            print(f"  cause={getattr(resp.exception, 'cause', None)!r}")
            http_response = getattr(resp.exception, "http_response", None)
            if http_response is not None:
                print(f"  http_status={http_response.status_code}")
                print(f"  http_body={http_response.text}")


if __name__ == "__main__":
    asyncio.run(send_multicast([FIREBASE_INSTALLATION_ID]))