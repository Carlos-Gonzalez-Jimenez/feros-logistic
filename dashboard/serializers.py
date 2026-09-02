from django.utils import timezone
from rest_framework import serializers


class DashboardDatesSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(default=timezone.now)

    def validate(self, data):
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({"start_date": "La fecha inicial no puede ser mayor que la fecha final."})

        if start_date and end_date:
            delta = (end_date - start_date).days
            if delta > 90:
                raise serializers.ValidationError({"date_range": "El rango de fechas no puede superar los 90 días."})

        return data
