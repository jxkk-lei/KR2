# Отгрузки со склада

Контрольная работа № 2. Вариант 31. Полноценное Django-приложение для просмотра
доков, отгрузок и статистики. Данные проходят цепочку:

**SQLite → SQL → Python sqlite3 → view → context → Django templates → HTML/CSS/JavaScript.**

Django ORM для данных не используется. Все восемь именованных запросов из
`sql/queries.sql` выполняются в работающем приложении.

## Запуск

Нужны Python 3.10 или новее и Django из `requirements.txt`. Проверено на
Python 3.14.3 и Django 5.2.18. Node.js и дополнительные сервисы для запуска не нужны.

Из папки проекта:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 manage.py check
python3 manage.py runserver --insecure
```

Откройте **http://127.0.0.1:8000/**. Остановка сервера: `Ctrl+C`.
В Windows виртуальное окружение включается командой `.venv\Scripts\activate`;
вместо `python3` можно использовать `python`.

На macOS также есть `run.command`: после установки зависимостей его можно запустить
двойным щелчком или командой `./run.command`.

База `data/shipments.db` уже содержит **4 дока и 12 отгрузок**. Для создания базы
заново по отсутствующему пути используется:

```bash
python3 manage.py initdb
```

Команда повторного запуска не дублирует данные и сохраняет изменения существующих
записей. Миграции Django выполнять не нужно. Предметная БД создаётся SQL-скриптами
`sql/schema.sql` и `sql/seed.sql`.

По умолчанию `DEBUG=False`: страницы ошибок не раскрывают внутренние сведения.
Флаг `--insecure` нужен стандартному серверу разработки Django для раздачи локальных
статических файлов при `DEBUG=False`. Он не меняет режим обработки ошибок.
Для обычного размещения предусмотрены WSGI и ASGI; статика собирается командой
`python3 manage.py collectstatic --noinput` и обслуживается веб-сервером.

## Страницы

| Адрес | Назначение | Имя маршрута |
| --- | --- | --- |
| `/` | Обзор склада, актуальные счётчики, активные и запланированные партии | `homepage:home` |
| `/docks/` | Все доки, вместимость, назначение и активность | `docks:list` |
| `/shipments/` | Карточки отгрузок, фильтры, сортировка и ограничение | `shipments:list` |
| `/shipments/statistics/` | Сводные показатели, группировки и HAVING | `shipments:statistics` |
| `/shipments/laptops-batch/` | Пример подробной страницы отгрузки | `shipments:detail` |

Маршрут `statistics/` объявлен перед `<slug:slug>/`. Ссылки в шаблонах строятся
именованными маршрутами через `{% url %}`.

## Фильтрация и сортировка

Форма списка отправляет GET-запрос. Можно комбинировать параметры:

| Параметр | Значение |
| --- | --- |
| `pallets` | Минимум палет, целое число от 0 до 1 000 000 |
| `status` | `запланирована`, `погружается`, `отгружена` |
| `goods_kind` | `электроника`, `мебель`, `одежда` |
| `q` | Фрагмент названия партии, до 100 символов; `%` и `_` ищутся буквально |
| `sort` | `date_desc`, `date_asc`, `pallets_desc`, `pallets_asc`, `title` |
| `limit` | От 1 до 500 записей; пустое значение показывает все |

Значения проходят проверку Django Forms, затем передаются отдельным словарём
в `sqlite3.Connection.execute()`. Для `ORDER BY` выбирается только заранее заданный
фрагмент SQL из `SORTS`. Пользовательский ввод не подставляется в SQL.
Счётчик «Найдено» учитывает фильтры, а «Показано» — ещё и `LIMIT`.

Примеры для исходной базы:

```text
/shipments/?pallets=30                         → 5 отгрузок
/shipments/?pallets=45                         → 2 отгрузки
/shipments/?pallets=1000                       → понятное сообщение, 0 записей
/shipments/?sort=pallets_desc&limit=2          → 60 и 45 палет
/shipments/?sort=date_asc&limit=3              → три наиболее ранние записи
/shipments/statistics/?min_count=4            → электроника: 5; мебель: 4
/shipments/statistics/?min_count=3            → ещё и одежда: 3
/shipments/statistics/?min_count=6            → пустая выборка групп
```

Веб-интерфейс содержит все необходимые поля; вручную редактировать URL не требуется.
Переключатель карточек и компактного списка работает на JavaScript и сохраняет вид
в браузере. Фильтрация выполняется сервером. На мобильном экране есть выдвижное
меню с закрытием по Escape. В деталях отгрузки можно скопировать ссылку.

## База данных

| Таблица | Поля |
| --- | --- |
| `docks` | `id`, `name`, `capacity`, `dock_kind` |
| `shipments` | `id`, `title`, `slug`, `goods_kind`, `ship_date`, `duration`, `pallets`, `status`, `dock_id` |

`shipments.dock_id` — внешний ключ на `docks.id`. Есть ограничения уникальности slug,
допустимых статусов и типов, неотрицательного количества палет, положительной
продолжительности и вместимости. Добавлены индексы по доку, дате и количеству палет.
Дата хранится в ISO-формате и передаётся в шаблон как `datetime`.

Все подключения находятся в `shipments/db.py`, включают `PRAGMA foreign_keys = ON`
и закрываются в `finally`, включая случаи ошибок. Чтение с `mode=rw` не создаёт
пустой файл при пропавшей БД. Новые HTTP-запросы читают актуальные записи SQLite.

Отгрузки связаны с доками запросами `JOIN`, доки без отгрузок сохраняются в списке
за счёт `LEFT JOIN`. Статистика использует `COUNT`, `SUM`, `AVG`, `GROUP BY`, `HAVING`.
При пороге `min_count=4` группа одежды с тремя партиями отсекается условием HAVING.

## Структура

```text
warehouse_shipments/
├── manage.py
├── requirements.txt
├── run.command
├── warehouse_shipments/       # settings, root urls, wsgi, asgi
├── homepage/                 # apps, urls, views, tests, templates/homepage/home.html
├── docks/                    # apps, urls, views, tests, templates/docks/dock_list.html
├── shipments/
│   ├── db.py                 # только sqlite3, без ORM
│   ├── forms.py
│   ├── urls.py
│   ├── views.py
│   ├── tests.py
│   ├── testing.py            # изолированная временная SQLite-база тестов
│   ├── management/commands/initdb.py
│   └── templates/shipments/
│       ├── shipment_list.html
│       ├── shipment_detail.html
│       ├── statistics.html
│       └── includes/
│           ├── shipment_card.html
│           └── status.html
├── templates/
│   ├── base.html
│   ├── 404.html
│   ├── 500.html
│   ├── database_error.html
│   └── includes/icons.html
├── static/
│   ├── css/style.css
│   ├── js/main.js
│   └── img/logo.png
├── sql/
│   ├── schema.sql
│   ├── seed.sql
│   └── queries.sql
├── data/shipments.db
├── scripts/
│   ├── create_logo.py
│   └── verify_queries.py
└── docs/
    ├── requirements.md
    ├── demonstration.md
    ├── verification.md
    └── screenshots/
```

В каждом приложении сохранены стандартные `__init__.py`, `apps.py`, `admin.py`,
`models.py`, `migrations/__init__.py`. Модели не объявляются: данные обрабатывает sqlite3.

## Проверка

```bash
python3 manage.py check
python3 manage.py test --verbosity 2
python3 scripts/verify_queries.py
```

Автотесты используют отдельную временную БД и не меняют `data/shipments.db`.
Проверяются реальные HTTP-ответы, контекст, вывод шаблонов, обновление данных,
фильтры, `ORDER BY`, `LIMIT`, `HAVING`, ограничения БД, закрытие соединений и ошибки.
`verify_queries.py` выводит реальные результаты всех восьми запросов и проверки
целостности; в исходные данные он изменений не вносит.

Подробный [сценарий демонстрации](docs/demonstration.md),
[соответствие всем 27 критериям](docs/requirements.md) и
[результаты проверок](docs/verification.md) находятся в `docs/`.

## Настройки окружения

| Переменная | Назначение | По умолчанию |
| --- | --- | --- |
| `SHIPMENTS_DB_PATH` | Путь к SQLite-файлу | `data/shipments.db` относительно проекта |
| `DJANGO_DEBUG` | `1` включает отладку | `0` |
| `DJANGO_ALLOWED_HOSTS` | Имена хостов через запятую | `localhost,127.0.0.1,[::1]` |
| `DJANGO_SECRET_KEY` | Секрет Django | Локальный учебный ключ |

Параметры можно задать в окружении процесса; сторонний загрузчик `.env` не нужен.
Для внешнего размещения задайте собственный ключ и допустимые хосты.

## Справочные материалы

Реализация использует официальные API:
[sqlite3](https://docs.python.org/3.14/library/sqlite3.html),
[Django render и context](https://docs.djangoproject.com/en/5.2/topics/http/shortcuts/),
[Django test client](https://docs.djangoproject.com/en/5.2/topics/testing/tools/).
