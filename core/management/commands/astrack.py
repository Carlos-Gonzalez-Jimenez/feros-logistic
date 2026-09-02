import json

from django.core.management import BaseCommand

from core.models import VehicleLocation, Vehicle, Config
from delivery.services import AsTrackCubaServices


class Command(BaseCommand):
    help = "AsTrack Suscriptor"

    def handle(self, *args, **options):
        config = Config.objects.first()
        service = AsTrackCubaServices(config.astrack_url, config.astrack_websocket, config.astrack_token)

        socket = service.socket_using_token(on_message=self.on_message)
        socket.run_forever()

    def on_message(self, ws, message):
        payload = json.loads(message)
        if payload.get('positions'):
            for p in payload['positions']:
                vehicle = Vehicle.objects.filter(device_id=p['deviceId'], use_mobile_gps=False, active=True).first()
                if vehicle:
                    try:
                        VehicleLocation.objects.update_or_create(
                            create_defaults=dict(
                                driver_id=vehicle.driver_id,
                                vehicle=vehicle,
                                lat=p.get('latitude'),
                                lon=p.get('longitude'),
                                alt=p.get('altitude'),
                                cog=p.get('cog', 0),
                                vel=p.get('speed', 0),
                                acc=p.get('accuracy', 0),
                                vac=p.get('vac', 0),
                                batt=p.get('batt', 100) / 100,
                                broker_id=p.get('id'),
                            ),
                            broker_id=p.get('id'),
                        )
                    except Exception as e:
                        print(e)
