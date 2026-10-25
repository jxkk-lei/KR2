"""Изолированная sqlite3-база для тестов; исходные демонстрационные данные не меняются."""
import io
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import SimpleTestCase, override_settings


class DatabaseTestCase(SimpleTestCase):
    def setUp(self):
        super().setUp()
        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.db_path = Path(self.temp_dir.name) / "shipments.db"
        self.settings_override = override_settings(SHIPMENTS_DB_PATH=self.db_path)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        call_command("initdb", stdout=io.StringIO())

    def execute(self, sql, parameters=()):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.execute(sql, parameters)
            rows = cursor.fetchall()
            conn.commit()
            return rows
        finally:
            conn.close()

    def add_shipment(self, *, slug="extra-batch", goods_kind="одежда"):
        self.execute(
            """INSERT INTO shipments
               (title, slug, goods_kind, ship_date, duration, pallets, status, dock_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("Дополнительная партия", slug, goods_kind, "2026-10-27 10:00:00", 35, 25, "запланирована", 1),
        )
