from django.urls import path
from . import views

app_name = "shipments"
urlpatterns = [
    path("", views.shipment_list, name="list"),
    # Фиксированный адрес обязательно раньше <slug:slug>.
    path("statistics/", views.statistics, name="statistics"),
    path("<slug:slug>/", views.shipment_detail, name="detail"),
]
