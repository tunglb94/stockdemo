from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include([
        path("accounts/", include("accounts.urls")),
        path("market/", include("market_data.urls")),
        path("trading/", include("trading.urls")),
        path("bots/", include("bots.urls")),
        path("crypto/", include("crypto.urls")),
    ])),
]
