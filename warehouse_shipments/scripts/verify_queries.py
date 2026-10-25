"""Вывести реальные результаты каждого запроса из queries.sql. БД не меняется."""
import os
import sys
from pathlib import Path
from pprint import pprint

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "warehouse_shipments.settings")
import django
django.setup()
from shipments import db


def main():
    scenarios = [
        ("list_shipments", db.filter_parameters(pallets=30, limit=3), "pallets_desc", "/shipments/?pallets=30&sort=pallets_desc&limit=3"),
        ("count_filtered", db.filter_parameters(pallets=30), None, "/shipments/?pallets=30"),
        ("shipment_by_slug", {"slug": "laptops-batch"}, None, "/shipments/laptops-batch/"),
        ("list_docks", {}, None, "/docks/"),
        ("overview", {}, None, "/"),
        ("dock_overview", {}, None, "/docks/"),
        ("goods_statistics", {"min_count": 4}, None, "/shipments/statistics/?min_count=4"),
        ("status_statistics", {}, None, "/shipments/statistics/"),
    ]
    for name, params, sort, url in scenarios:
        print(f"\n{name} → {url}")
        pprint(db.fetch_all(name, params, sort=sort), sort_dicts=False)
    with db.connection() as conn:
        print("\nPRAGMA integrity_check:", conn.execute("PRAGMA integrity_check").fetchone()[0])
        print("PRAGMA foreign_key_check:", list(conn.execute("PRAGMA foreign_key_check")))


if __name__ == "__main__":
    main()
