#!/usr/bin/env python3
"""Управление Django-проектом «Отгрузки со склада»."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "warehouse_shipments.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
