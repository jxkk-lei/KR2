from django.shortcuts import render
from django.views.decorators.http import require_safe
from shipments import db


@require_safe
@db.database_view
def home(request):
    return render(request, "homepage/home.html", {
        "overview": db.get_overview(),
        "dock_overview": db.get_dock_overview(),
        "shipments": db.get_shipments(sort="date_asc", status="погружается", limit=4),
        "upcoming": db.get_shipments(sort="date_asc", status="запланирована", limit=4),
        "docks": db.get_docks(),
    })


def page_not_found(request, exception):
    return render(request, "404.html", status=404)


def server_error(request):
    return render(request, "500.html", status=500)
