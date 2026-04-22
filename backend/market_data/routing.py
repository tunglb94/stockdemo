from django.urls import re_path
from .consumers import MarketConsumer

websocket_urlpatterns = [
    re_path(r"ws/market/(?P<symbol>[A-Z0-9]+)/$", MarketConsumer.as_asgi()),
]
