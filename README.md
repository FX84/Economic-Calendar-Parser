# Парсер экономического календаря

Economic-Calendar-Parser (`calendar.py`) — это скрипт на Python для парсинга и анализа экономического календаря (макростатистика, решения центральных банков, новости по рынкам). Позволяет загружать события с популярных источников (ForexFactory, Investing.com), фильтровать их по странам и важности, конвертировать время в нужный часовой пояс, сохранять данные в разные форматы и получать уведомления о ближайших событиях.

---

## 🚀 Возможности
- Поддержка провайдеров:
  - [ForexFactory](https://www.forexfactory.com/calendar)
  - [Investing.com](https://www.investing.com/economic-calendar/)
- Фильтрация событий:
  - по странам (USD, EUR, GBP и т.д.)
  - по важности (high, medium, low)
  - по ключевым словам в названии события
- Конвертация времени:
  - UTC → любой часовой пояс (по умолчанию `Europe/Madrid`)
- Сохранение результатов:
  - CSV
  - JSON
  - SQLite (с автоматическим созданием таблицы и индексов)
- Уведомления о ближайших событиях:
  - вывод в консоль
  - выбор окна времени (например, 24 часа, 3 часа, 90 минут)
- CLI-интерфейс с удобными параметрами
- MIT лицензия — можно свободно использовать и изменять

---

## 📦 Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/FX84/Economic-Calendar-Parser.git
cd Economic-Calendar-Parser
````

2. Установите зависимости:

```bash
pip install -r requirements.txt
```

Минимальный набор библиотек:

* `requests`
* `beautifulsoup4`
* `lxml`
* `python-dateutil`

---

## 🔧 Использование

### Базовый запуск

```bash
python calendar.py --providers forex_factory investing_com --out-format csv
```

### Фильтрация по странам и важности

```bash
python calendar.py \
  --providers forex_factory \
  --countries USD EUR \
  --importance high medium \
  --out-format json
```

### Сохранение в SQLite

```bash
python calendar.py \
  --providers investing_com \
  --out-format sqlite \
  --sqlite-path ./data/calendar.sqlite
```

### Уведомления о ближайших событиях

```bash
python calendar.py \
  --notify upcoming \
  --notify-window "12h" \
  --tz Europe/Madrid
```

---

## ⚙️ Аргументы CLI

| Параметр          | Описание                                             | Значение по умолчанию    |
| ----------------- | ---------------------------------------------------- | ------------------------ |
| `--providers`     | Провайдеры (`forex_factory`, `investing_com`)        | оба                      |
| `--countries`     | Список стран (например: `USD EUR GBP`)               | все                      |
| `--importance`    | Важность (`high`, `medium`, `low`)                   | все                      |
| `--date-from`     | Дата начала диапазона (`YYYY-MM-DD`)                 | текущая дата             |
| `--date-to`       | Дата конца диапазона (`YYYY-MM-DD`)                  | текущая дата             |
| `--tz`            | Часовой пояс вывода (`Europe/Madrid`, `UTC`, и т.д.) | `Europe/Madrid`          |
| `--out-format`    | Форматы сохранения (`csv`, `json`, `sqlite`)         | `csv`                    |
| `--out-dir`       | Папка для файлов                                     | `./data`                 |
| `--sqlite-path`   | Путь к базе SQLite                                   | `./data/calendar.sqlite` |
| `--notify`        | Уведомления (`upcoming`)                             | выключено                |
| `--notify-window` | Окно для уведомлений (`24h`, `3h`, `90m`)            | `24h`                    |
| `--log-level`     | Уровень логов (`DEBUG`, `INFO`, `WARN`, `ERROR`)     | `INFO`                   |

---

## 📂 Примеры файлов

* **CSV**

```csv
id,provider,title,country,importance,time_utc,time_local,timezone,actual_value,forecast_value,previous_value
1a2b3c...,forex_factory,Non-Farm Employment Change,USD,high,2025-10-04T12:30:00Z,2025-10-04 14:30,UTC,236000,210000,205000
```

* **JSON**

```json
[
{
  "id": "1a2b3c...",
  "provider": "investing_com",
  "title": "CPI (г/г)",
  "country": "EUR",
  "importance": "high",
  "time_utc": "2025-10-05T09:00:00Z",
  "time_local": "2025-10-05 11:00",
  "timezone": "UTC",
  "actual_value": 3.1,
  "forecast_value": 3.0,
  "previous_value": 2.8
}
]
```

---

## ⚠️ Ограничения и примечания

* HTML-разметка у сайтов может меняться, при необходимости корректируйте CSS-селекторы в коде.
* Не запускайте парсер слишком часто (уважайте источники данных).
* Проект создан в образовательных целях и не является торговой рекомендацией.

---

## 📝 Лицензия

[MIT](LICENSE) — вы можете свободно использовать, модифицировать и распространять этот проект.
