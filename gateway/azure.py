# HACK:
import sys
# Important: Azure is doing somehing fun with their installs. 
# https://stackoverflow.com/questions/54400662/no-module-named-azure-eventhub-azure-is-not-a-package
sys.path.insert( 0, '/opt/venv/lib/python3.9/site-packages' )
sys.path.insert( 0, '/go/src/github.com/synpse-hq/azure-iot-hub-example/pyenv/lib/python3.9/site-packages' )

import asyncio
import os
import uuid
from nats.aio.client import Client as NATS
from azure.iot.device import IoTHubDeviceClient
from azure.iot.device import Message, X509

async def run(loop):
    # nc is the NATS connection to recieve messages from our application
    nc = NATS()

    async def disconnected_cb():
        print("Got disconnected...")
        os._exit(1)

    async def reconnected_cb():
        print("Got reconnected...")

    await nc.connect(os.getenv("NATS_HOSTNAME"),
                     reconnected_cb=reconnected_cb,
                     disconnected_cb=disconnected_cb,
                     max_reconnect_attempts=-1,
                     loop=loop)

    hostname = os.getenv("HOSTNAME")
    # The device that has been created on the portal using X509 CA signing or Self signing capabilities
    device_id = os.getenv("DEVICE_ID")

    x509 = X509(
        cert_file="device1.crt",
        key_file="device1.key",
    )

    # The client object is used to interact with your Azure IoT hub.
    azure_client = IoTHubDeviceClient.create_from_x509_certificate(
        hostname=hostname, device_id=device_id, x509=x509
    )

    azure_client.connect()
    print("Connected to Azure IoT Core")

    def send_message(i):
        print("sending message: {}".format(i))
        msg = Message(str(i))
        msg.message_id = uuid.uuid4()
        azure_client.send_message(msg)
       

    async def metrics_request(msg):
        data = msg.data.decode()
        send_message(data)

    # Use queue named 'metrics' for distributing requests
    # among subscribers.
    await nc.subscribe("metrics", cb=metrics_request)

    print("Listening for requests on 'metrics' subject...")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(loop))
    loop.run_forever()
    loop.close()