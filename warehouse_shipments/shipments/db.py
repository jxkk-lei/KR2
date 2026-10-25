"""Единственная точка доступа к данным: SQL → sqlite3 → обычные словари.

SQL берётся из sql/queries.sql. Пользовательские значения передаются execute()
отдельным словарём. Подставляемый ORDER BY выбирается только из константы SORTS.
"""
import logging
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from functools import lru_cache, wraps
from pathlib import Path

from django.conf import settings
from django.shortcuts import render

logger = logging.getLogger(__name__)

SORTS = {
    "date_desc": ("s.ship_date DESC, s.id DESC", "Сначала новые"),
    "date_asc": ("s.ship_date ASC, s.id ASC", "Сначала ранние"),
    "pallets_desc": ("s.pallets DESC, s.id ASC", "Больше палет"),
    "pallets_asc": ("s.pallets ASC, s.id ASC", "Меньше палет"),
    "title": ("s.title COLLATE NOCASE ASC, s.id ASC", "По названию"),
}
GOODS_KINDS = ("электроника", "мебель", "одежда")
STATUSES = ("запланирована", "погружается", "отгружена")


@lru_cache(maxsize=1)
def load_queries():
    text = (settings.BASE_DIR / "sql" / "queries.sql").read_text(encoding="utf-8")
    parts = re.split(r"^-- name: (\w+)\s*$", text, flags=re.MULTILINE)
    return {parts[i]: parts[i + 1].strip() for i in range(1, len(parts), 2)}


@contextmanager
def connection():
    # mode=rw не создаёт пустую БД при неверном пути или удалении файла.
    uri = Path(settings.SHIPMENTS_DB_PATH).resolve().as_uri() + "?mode=rw"
    conn = sqlite3.connect(uri, uri=True, timeout=5)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
    finally:
        # Контекстный менеджер sqlite3 сам по себе НЕ закрывает соединение.
        conn.close()


def fetch_all(name, parameters=None, *, sort=None):
    sql = load_queries()[name]
    if name == "list_shipments":
        sql = sql.format(order_by=SORTS.get(sort, SORTS["date_desc"])[0])
    with connection() as conn:
        rows = conn.execute(sql, parameters or {}).fetchall()
    result = [dict(row) for row in rows]
    for row in result:
        if "ship_date" in row:
            # Фильтр date в DTL получает datetime, а не строку из SQLite.
            row["ship_date"] = datetime.fromisoformat(row["ship_date"])
    return result


def filter_parameters(*, pallets=None, status="", goods_kind="", q="", limit=None):
    # Символы LIKE экранируются: поиск % и _ означает именно эти символы.
    search = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return {
        "pallets": pallets, "status": status, "goods_kind": goods_kind,
        "query": q, "search": f"%{search}%", "limit": limit if limit is not None else -1,
    }


def get_shipments(*, sort="date_desc", **filters):
    return fetch_all("list_shipments", filter_parameters(**filters), sort=sort)


def count_shipments(**filters):
    return fetch_all("count_filtered", filter_parameters(**filters))[0]["total"]


def get_shipment(slug):
    rows = fetch_all("shipment_by_slug", {"slug": slug})
    return rows[0] if rows else None


def get_docks():
    return fetch_all("list_docks")


def get_overview():
    return fetch_all("overview")[0]


def get_dock_overview():
    return fetch_all("dock_overview")[0]


def get_goods_statistics(min_count=4):
    return fetch_all("goods_statistics", {"min_count": min_count})


def get_status_statistics():
    return fetch_all("status_statistics")


def database_view(view):
    """На всех страницах ошибки sqlite3 дают понятный ответ HTTP 503."""
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        try:
            return view(request, *args, **kwargs)
        except sqlite3.Error:
            logger.exception("Ошибка получения данных склада")
            response = render(request, "database_error.html", status=503)
            response["Retry-After"] = "30"
            return response
    return wrapped
