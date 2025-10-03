#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
calendar.py — Economic Calendar Parser

Скрипт парсит экономический календарь с сайтов (forex factory, investing),
нормализует данные, сохраняет в CSV/JSON/SQLite и может уведомлять о ближайших событиях.
"""

import argparse
import csv
import hashlib
import json
import logging
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser, tz

# -------------------------------
# Константы
# -------------------------------
USER_AGENT = "calendar.py (educational; contact: you@example.com)"
IMPORTANCE_MAP = {
    "low": "low",
    "medium": "medium",
    "high": "high"
}

# -------------------------------
# Утилиты
# -------------------------------

def sha1_id(*args) -> str:
    """Генерация ID события на основе строки"""
    text = "|".join([str(a) for a in args if a])
    return hashlib.sha1(text.encode("utf-8")).hexdigest()

def parse_number(s: Optional[str]) -> Optional[float]:
    """Парсинг числовых значений: '236K' -> 236000.0, '3.1%' -> 3.1"""
    if not s:
        return None
    s = s.strip().replace(",", "")
    mult = 1
    if s.endswith("%"):
        s = s.replace("%", "")
    if s.endswith("K"):
        mult = 1e3
        s = s.replace("K", "")
    elif s.endswith("M"):
        mult = 1e6
        s = s.replace("M", "")
    try:
        return float(s) * mult
    except ValueError:
        return None

def convert_time(dt_str: str, tz_from: str, tz_to: str) -> (str, str):
    """Конвертация времени из одной зоны в UTC и в локальную (--tz)"""
    try:
        dt_obj = dateparser.parse(dt_str)
        if tz_from:
            from_zone = tz.gettz(tz_from)
            dt_obj = dt_obj.replace(tzinfo=from_zone)
        else:
            dt_obj = dt_obj.replace(tzinfo=tz.UTC)
        utc_time = dt_obj.astimezone(tz.UTC)
        local_time = dt_obj.astimezone(tz.gettz(tz_to))
        return utc_time.isoformat(), local_time.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return None, None

# -------------------------------
# Базовый класс провайдера
# -------------------------------

class ProviderBase:
    def fetch(self, date_from: str, date_to: str, countries: List[str], importance: List[str]) -> List[Dict[str, Any]]:
        raise NotImplementedError

# -------------------------------
# Провайдер: ForexFactory
# -------------------------------

class ForexFactoryProvider(ProviderBase):
    BASE_URL = "https://www.forexfactory.com/calendar"

    def fetch(self, date_from, date_to, countries, importance):
        logging.info("Загружаем ForexFactory...")
        # ⚠️ Здесь пример. Страницу можно адаптировать по факту.
        url = f"{self.BASE_URL}?week={date_from}"
        headers = {"User-Agent": USER_AGENT}
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code != 200:
            logging.warning("ForexFactory: не удалось загрузить")
            return []
        soup = BeautifulSoup(resp.text, "lxml")
        events = []
        rows = soup.select("tr.calendar_row")
        for row in rows:
            try:
                time_cell = row.select_one(".calendar__time")
                title_cell = row.select_one(".calendar__event")
                country_cell = row.select_one(".calendar__country")
                impact_cell = row.select_one(".calendar__impact")
                actual_cell = row.select_one(".calendar__actual")
                forecast_cell = row.select_one(".calendar__forecast")
                previous_cell = row.select_one(".calendar__previous")

                if not title_cell:
                    continue

                title = title_cell.get_text(strip=True)
                country = country_cell.get_text(strip=True) if country_cell else ""
                imp = impact_cell.get_text(strip=True).lower() if impact_cell else "medium"

                # Фильтрация по стране и важности
                if countries and country not in countries:
                    continue
                if importance and imp not in importance:
                    continue

                dt_str = time_cell.get_text(strip=True)
                utc_time, local_time = convert_time(dt_str, "America/New_York", "UTC")

                event = {
                    "provider": "forex_factory",
                    "title": title,
                    "country": country,
                    "importance": IMPORTANCE_MAP.get(imp, "medium"),
                    "time_utc": utc_time,
                    "time_local": local_time,
                    "timezone": "UTC",
                    "actual_value": parse_number(actual_cell.get_text(strip=True)) if actual_cell else None,
                    "forecast_value": parse_number(forecast_cell.get_text(strip=True)) if forecast_cell else None,
                    "previous_value": parse_number(previous_cell.get_text(strip=True)) if previous_cell else None,
                }
                event["id"] = sha1_id(event["provider"], event["title"], event["country"], event["time_utc"])
                events.append(event)
            except Exception as e:
                logging.debug(f"Ошибка парсинга строки: {e}")
        return events

# -------------------------------
# Провайдер: Investing.com
# -------------------------------

class InvestingProvider(ProviderBase):
    BASE_URL = "https://www.investing.com/economic-calendar/"

    def fetch(self, date_from, date_to, countries, importance):
        logging.info("Загружаем Investing.com...")
        headers = {"User-Agent": USER_AGENT}
        resp = requests.get(self.BASE_URL, headers=headers, timeout=20)
        if resp.status_code != 200:
            logging.warning("Investing.com: не удалось загрузить")
            return []
        soup = BeautifulSoup(resp.text, "lxml")
        events = []
        # ⚠️ Аналогично — структура упрощена
        rows = soup.select("tr.js-event-item")
        for row in rows:
            try:
                title = row.get("data-event-title", "")
                country = row.get("data-country", "")
                imp = row.get("data-event-importance", "medium").lower()
                dt_str = row.get("data-event-datetime", "")
                utc_time, local_time = convert_time(dt_str, "UTC", "UTC")

                if countries and country not in countries:
                    continue
                if importance and imp not in importance:
                    continue

                event = {
                    "provider": "investing_com",
                    "title": title,
                    "country": country,
                    "importance": IMPORTANCE_MAP.get(imp, "medium"),
                    "time_utc": utc_time,
                    "time_local": local_time,
                    "timezone": "UTC",
                    "actual_value": None,
                    "forecast_value": None,
                    "previous_value": None,
                }
                event["id"] = sha1_id(event["provider"], event["title"], event["country"], event["time_utc"])
                events.append(event)
            except Exception as e:
                logging.debug(f"Ошибка парсинга строки Investing: {e}")
        return events

# -------------------------------
# Сохранение
# -------------------------------

def save_csv(events: List[Dict[str, Any]], path: str):
    keys = list(events[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(events)
    logging.info(f"Сохранено CSV: {path}")

def save_json(events: List[Dict[str, Any]], path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    logging.info(f"Сохранено JSON: {path}")

def save_sqlite(events: List[Dict[str, Any]], path: str):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
      id TEXT PRIMARY KEY,
      provider TEXT,
      title TEXT,
      country TEXT,
      importance TEXT,
      time_utc TEXT,
      time_local TEXT,
      timezone TEXT,
      actual_value REAL,
      forecast_value REAL,
      previous_value REAL
    )""")
    for e in events:
        cur.execute("""INSERT OR IGNORE INTO events
          (id, provider, title, country, importance, time_utc, time_local, timezone,
          actual_value, forecast_value, previous_value)
          VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
          (e["id"], e["provider"], e["title"], e["country"], e["importance"], e["time_utc"], e["time_local"],
           e["timezone"], e["actual_value"], e["forecast_value"], e["previous_value"]))
    conn.commit()
    conn.close()
    logging.info(f"Сохранено в SQLite: {path}")

# -------------------------------
# Уведомления
# -------------------------------

def notify_upcoming(events: List[Dict[str, Any]], window: str, tz_name: str):
    """Показать события в ближайшее время"""
    now = datetime.now(tz=tz.gettz(tz_name))
    # интерпретация окна (например "24h")
    num, unit = int(window[:-1]), window[-1]
    if unit == "h":
        delta = timedelta(hours=num)
    elif unit == "m":
        delta = timedelta(minutes=num)
    else:
        delta = timedelta(hours=24)
    until = now + delta
    for e in events:
        if not e["time_utc"]:
            continue
        ev_time = dateparser.parse(e["time_utc"])
        if now.astimezone(tz.UTC) <= ev_time <= until.astimezone(tz.UTC):
            print(f"[{e['time_local']}] {e['country']} • {e['title']} • {e['importance'].upper()}")

# -------------------------------
# main()
# -------------------------------

def main():
    parser = argparse.ArgumentParser(description="Economic Calendar Parser")
    parser.add_argument("--providers", nargs="+", default=["forex_factory", "investing_com"])
    parser.add_argument("--countries", nargs="*", default=[])
    parser.add_argument("--importance", nargs="*", default=[])
    parser.add_argument("--date-from", default=datetime.utcnow().strftime("%Y-%m-%d"))
    parser.add_argument("--date-to", default=datetime.utcnow().strftime("%Y-%m-%d"))
    parser.add_argument("--tz", default="Europe/Madrid")
    parser.add_argument("--out-format", nargs="*", default=["csv"])
    parser.add_argument("--out-dir", default="./data")
    parser.add_argument("--sqlite-path", default="./data/calendar.sqlite")
    parser.add_argument("--notify", choices=["upcoming"], default=None)
    parser.add_argument("--notify-window", default="24h")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    os.makedirs(args.out_dir, exist_ok=True)

    providers = []
    if "forex_factory" in args.providers:
        providers.append(ForexFactoryProvider())
    if "investing_com" in args.providers:
        providers.append(InvestingProvider())

    all_events = []
    for p in providers:
        evs = p.fetch(args.date_from, args.date_to, args.countries, args.importance)
        all_events.extend(evs)

    if not all_events:
        logging.warning("События не найдены")
        sys.exit(2)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    if "csv" in args.out_format:
        save_csv(all_events, os.path.join(args.out_dir, f"events_{ts}.csv"))
    if "json" in args.out_format:
        save_json(all_events, os.path.join(args.out_dir, f"events_{ts}.json"))
    if "sqlite" in args.out_format:
        save_sqlite(all_events, args.sqlite_path)

    if args.notify == "upcoming":
        notify_upcoming(all_events, args.notify_window, args.tz)

    sys.exit(0)

if __name__ == "__main__":
    main()