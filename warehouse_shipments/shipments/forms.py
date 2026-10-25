from django import forms
from .db import GOODS_KINDS, SORTS, STATUSES


class ShipmentFilterForm(forms.Form):
    q = forms.CharField(
        required=False, max_length=100, label="Название партии",
        widget=forms.TextInput(attrs={"placeholder": "Найти отгрузку…", "class": "search-input"}),
    )
    pallets = forms.IntegerField(
        required=False, min_value=0, max_value=1_000_000, label="Минимум палет",
        widget=forms.NumberInput(attrs={"placeholder": "Например, 30", "inputmode": "numeric"}),
    )
    status = forms.ChoiceField(
        required=False, label="Статус",
        choices=[("", "Все статусы")] + [(s, s.capitalize()) for s in STATUSES],
    )
    goods_kind = forms.ChoiceField(
        required=False, label="Тип груза",
        choices=[("", "Все типы")] + [(g, g.capitalize()) for g in GOODS_KINDS],
    )
    sort = forms.ChoiceField(
        required=False, initial="date_desc", label="Сортировка",
        choices=[(key, value[1]) for key, value in SORTS.items()],
    )
    limit = forms.IntegerField(
        required=False, min_value=1, max_value=500, label="Показать записей",
        widget=forms.NumberInput(attrs={"placeholder": "Все", "inputmode": "numeric"}),
    )


class StatisticsFilterForm(forms.Form):
    min_count = forms.IntegerField(
        required=False, min_value=1, max_value=1_000_000, initial=4,
        label="Минимум отгрузок одного типа",
        widget=forms.NumberInput(attrs={"inputmode": "numeric"}),
    )
