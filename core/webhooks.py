from rest_framework import generics

from core import serializers


class OdooSaleWebhook(generics.CreateAPIView):
    serializer_class = serializers.OdooWebhookSerializer
