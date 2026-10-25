"""Создание предметной БД без ORM и миграций Django."""
import sqlite3
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Создать SQLite-базу и заполнить демонстрационными данными, если она пуста."

    def handle(self, *args, **options):
        path = Path(settings.SHIPMENTS_DB_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path)
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            schema = (settings.BASE_DIR / "sql" / "schema.sql").read_text(encoding="utf-8")
            seed = (settings.BASE_DIR / "sql" / "seed.sql").read_text(encoding="utf-8")
            conn.executescript("BEGIN IMMEDIATE;\n" + schema)
            dock_count = conn.execute("SELECT COUNT(*) FROM docks").fetchone()[0]
            shipment_count = conn.execute("SELECT COUNT(*) FROM shipments").fetchone()[0]
            if dock_count == 0 and shipment_count == 0:
                # executescript коммитит предыдущую транзакцию, поэтому seed имеет свою.
                conn.commit()
                conn.executescript("BEGIN IMMEDIATE;\n" + seed + "\nCOMMIT;")
                self.stdout.write(self.style.SUCCESS("Созданы 4 дока и 12 отгрузок."))
            else:
                conn.commit()
                self.stdout.write("База уже содержит данные; существующие записи сохранены.")
        except sqlite3.Error as exc:
            conn.rollback()
            raise CommandError(f"Не удалось подготовить SQLite-базу: {exc}") from exc
        finally:
            conn.close()
