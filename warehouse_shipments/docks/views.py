from django.shortcuts import render
from django.views.decorators.http import require_safe
from shipments import db


@require_safe
@db.database_view
def dock_list(request):
    return render(request, "docks/dock_list.html", {
        "docks": db.get_docks(), "dock_overview": db.get_dock_overview(),
    })
