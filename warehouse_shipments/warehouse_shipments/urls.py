from django.urls import include, path

urlpatterns = [
    path("", include("homepage.urls")),
    path("docks/", include("docks.urls")),
    path("shipments/", include("shipments.urls")),
]

handler404 = "homepage.views.page_not_found"
handler500 = "homepage.views.server_error"
