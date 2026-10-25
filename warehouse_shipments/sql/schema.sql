PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS docks (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE CHECK (length(trim(name)) > 0),
    capacity INTEGER NOT NULL CHECK (typeof(capacity) = 'integer' AND capacity > 0),
    dock_kind TEXT NOT NULL CHECK (dock_kind IN ('приём', 'отгрузка', 'кросс-докинг'))
);

CREATE TABLE IF NOT EXISTS shipments (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
    slug TEXT NOT NULL UNIQUE CHECK (
        length(slug) > 0 AND slug NOT GLOB '*[^a-zA-Z0-9_-]*' AND slug <> 'statistics'
    ),
    goods_kind TEXT NOT NULL CHECK (goods_kind IN ('электроника', 'мебель', 'одежда')),
    ship_date TEXT NOT NULL CHECK (datetime(ship_date) IS NOT NULL),
    duration INTEGER NOT NULL CHECK (typeof(duration) = 'integer' AND duration > 0),
    pallets INTEGER NOT NULL CHECK (typeof(pallets) = 'integer' AND pallets >= 0),
    status TEXT NOT NULL CHECK (status IN ('запланирована', 'погружается', 'отгружена')),
    dock_id INTEGER NOT NULL REFERENCES docks(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_shipments_dock ON shipments(dock_id);
CREATE INDEX IF NOT EXISTS idx_shipments_date ON shipments(ship_date);
CREATE INDEX IF NOT EXISTS idx_shipments_pallets ON shipments(pallets);
