from django.http import Http404
from django.shortcuts import render
from django.views.decorators.http import require_safe

from . import db
from .forms import ShipmentFilterForm, StatisticsFilterForm


@require_safe
@db.database_view
def shipment_list(request):
    form = ShipmentFilterForm(request.GET)
    shipments, matched_count = [], 0
    if form.is_valid():
        filters = {key: form.cleaned_data.get(key) for key in ("pallets", "status", "goods_kind", "q", "limit")}
        shipments = db.get_shipments(sort=form.cleaned_data["sort"] or "date_desc", **filters)
        matched_count = db.count_shipments(**filters)
    return render(request, "shipments/shipment_list.html", {
        "shipments": shipments, "form": form, "matched_count": matched_count,
        "overview": db.get_overview(), "has_filters": bool(request.GET),
    })


@require_safe
@db.database_view
def shipment_detail(request, slug):
    shipment = db.get_shipment(slug)
    if shipment is None:
        raise Http404("Отгрузка не найдена")
    return render(request, "shipments/shipment_detail.html", {"shipment": shipment})


@require_safe
@db.database_view
def statistics(request):
    data = request.GET.copy()
    if not data.get("min_count", "").strip():
        data["min_count"] = "4"
    form = StatisticsFilterForm(data)
    groups, min_count = [], None
    overview = db.get_overview()
    if form.is_valid():
        min_count = form.cleaned_data["min_count"]
        groups = db.get_goods_statistics(min_count)
    statuses = db.get_status_statistics()
    for status in statuses:
        status["percentage"] = round(status["shipment_count"] / overview["total"] * 100, 1) if overview["total"] else 0
    return render(request, "shipments/statistics.html", {
        "groups": groups, "overview": overview, "statuses": statuses,
        "form": form, "min_count": min_count, "docks": db.get_docks(),
    })
