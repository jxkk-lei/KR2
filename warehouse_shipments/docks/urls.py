from django.urls import path
from . import views

app_name = "docks"
urlpatterns = [path("", views.dock_list, name="list")]
