import json

import paho.mqtt.client as mqtt
from django.core.management import BaseCommand

from core.models import Config, Vehicle, VehicleLocation


class Command(BaseCommand):
    help = "Suscriptor MQTT"

    def on_message(self, client, userdata, message):
        topic = message.topic

        try:
            payload = json.loads(message.payload.decode('utf-8'))
        except json.decoder.JSONDecodeError:
            payload = message.payload

        try:
            if isinstance(payload, dict) and payload.get('_type') == 'location':
                driver_id = int(topic.split('/')[-1])
                vehicle = Vehicle.objects.get(device_id=driver_id, use_mobile_gps=True, active=True)
                VehicleLocation.objects.update_or_create(
                    create_defaults=dict(
                        driver_id=driver_id,
                        vehicle=vehicle,
                        lat=payload.get('lat'),
                        lon=payload.get('lon'),
                        alt=payload.get('alt'),
                        cog=payload.get('cog', 0),
                        vel=payload.get('vel', 0),
                        acc=payload.get('acc', 0),
                        vac=payload.get('vac', 0),
                        batt=payload.get('batt', 0) / 100,
                        broker_id=payload.get('_id'),
                    ),
                    broker_id=payload.get('_id'),
                )
        except Exception as e:
            pass

    def handle(self, *args, **options):
        config = Config.objects.first()

        def on_connect(client, *args, **kwargs):
            client.subscribe(config.mqtt_location_topic)

        client = mqtt.Client(client_id=config.mqtt_client_id)
        if config.mqtt_username and config.mqtt_password:
            client.username_pw_set(config.mqtt_username, config.mqtt_password)
            # client.username_pw_set('admin', '@dminF3r0s*')
            # client.username_pw_set('ferosgrupo', '@b123456*')
        client.on_connect = on_connect
        client.on_message = self.on_message

        client.connect(config.mqtt_host, config.mqtt_port)
        client.loop_forever()
