#!/usr/bin/env python3
"""
Mentor4Trading – ForexFactory Kalender Bot
Postet täglich High-Impact Events in deinen Telegram Kanal
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
import pytz
import os
import sys

# ─────────────────────────────────────────────
# KONFIGURATION – hier anpassen!
# ─────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()
BOT_TOKEN   = os.environ.get("BOT_TOKEN", "")
CHANNEL_ID  = os.environ.get("CHANNEL_ID", "")

# Welche Währungen sollen gezeigt werden?
CURRENCIES  = ["USD", "EUR", "GBP", "JPY"]

# Nur diese Impact-Level posten (High = rot auf FF)
SHOW_HIGH   = True
SHOW_MEDIUM = False   # auf True setzen wenn du auch gelbe Events willst
SHOW_LOW    = False

TIMEZONE    = "Europe/Berlin"  # MEZ / MESZ automatisch
# ─────────────────────────────────────────────

FF_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"

IMPACT_EMOJI = {
    "High":   "🔴",
    "Medium": "🟡",
    "Low":    "⚪",
    "Non-Economic": "ℹ️"
}

FLAG_EMOJI = {
    "USD": "🇺🇸",
    "EUR": "🇪🇺",
    "GBP": "🇬🇧",
    "JPY": "🇯🇵",
    "CHF": "🇨🇭",
    "AUD": "🇦🇺",
    "CAD": "🇨🇦",
    "NZD": "🇳🇿",
}


def fetch_calendar():
    """ForexFactory XML Calendar holen"""
    try:
        r = requests.get(FF_URL, timeout=15, headers={
            "User-Agent": "Mozilla/5.0"
        })
        r.raise_for_status()
        return r.content
    except Exception as e:
        print(f"[ERROR] Kalender abrufen fehlgeschlagen: {e}")
        return None


def parse_events(xml_data):
    """Events aus XML parsen und für heute filtern"""
    root = ET.fromstring(xml_data)
    tz_berlin = pytz.timezone(TIMEZONE)
    today = datetime.now(tz_berlin).date()

    events = []
    for event in root.findall("event"):
        try:
            currency = event.findtext("country", "").strip().upper()
            impact   = event.findtext("impact", "").strip()
            title    = event.findtext("title", "").strip()
            date_str = event.findtext("date", "").strip()
            time_str = event.findtext("time", "").strip()

            # Währungs-Filter
            if currency not in CURRENCIES:
                continue

            # Impact-Filter
            if impact == "High"   and not SHOW_HIGH:   continue
            if impact == "Medium" and not SHOW_MEDIUM:  continue
            if impact == "Low"    and not SHOW_LOW:     continue
            if impact == "Non-Economic":                continue

            # Datum parsen (FF liefert z.B. "05-20-2026")
            try:
                event_date = datetime.strptime(date_str, "%m-%d-%Y").date()
            except:
                continue

            # Nur heutige Events
            if event_date != today:
                continue

            # Zeit umrechnen (FF liefert UTC)
            if time_str and time_str.lower() not in ("", "all day", "tentative"):
                try:
                    dt_utc = datetime.strptime(
                        f"{date_str} {time_str}", "%m-%d-%Y %I:%M%p"
                    ).replace(tzinfo=timezone.utc)
                    dt_local = dt_utc.astimezone(tz_berlin)
                    time_display = dt_local.strftime("%H:%M")
                    sort_key = dt_local
                except:
                    time_display = time_str
                    sort_key = datetime.max.replace(tzinfo=timezone.utc)
            else:
                time_display = "ganztägig"
                sort_key = datetime.max.replace(tzinfo=timezone.utc)

            events.append({
                "time":     time_display,
                "currency": currency,
                "impact":   impact,
                "title":    title,
                "sort_key": sort_key
            })

        except Exception as e:
            print(f"[WARN] Event überspringen: {e}")
            continue

    # Nach Uhrzeit sortieren
    events.sort(key=lambda x: x["sort_key"])
    return events


def build_message(events):
    """Telegram-Nachricht formatieren"""
    tz_berlin = pytz.timezone(TIMEZONE)
    now = datetime.now(tz_berlin)

    # Wochentag auf Deutsch
    weekdays = {
        "Monday": "Montag", "Tuesday": "Dienstag", "Wednesday": "Mittwoch",
        "Thursday": "Donnerstag", "Friday": "Freitag",
        "Saturday": "Samstag", "Sunday": "Sonntag"
    }
    day_de = weekdays.get(now.strftime("%A"), now.strftime("%A"))
    date_str = now.strftime(f"{day_de}, %d.%m.%Y")

    msg = f"📅 *Wirtschaftskalender – {date_str}*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━\n\n"

    if not events:
        msg += "✅ Keine High-Impact Events heute – ruhiger Tag!\n"
    else:
        for e in events:
            emoji   = IMPACT_EMOJI.get(e["impact"], "⚫")
            flag    = FLAG_EMOJI.get(e["currency"], "🌐")
            msg += f"{emoji} `{e['time']}` {flag} *{e['currency']}* – {e['title']}\n"

    msg += "\n━━━━━━━━━━━━━━━━━━━━━\n"

    # Warnhinweis wenn Events da sind
    high_count = sum(1 for e in events if e["impact"] == "High")
    if high_count >= 3:
        msg += "⚠️ *Viele News heute – SL absichern, klein traden!*\n"
    elif high_count > 0:
        msg += "⚠️ *News beachten – ggf. vor Release aus Trades raus!*\n"
    else:
        msg += "📊 *Saubere Chartarbeit möglich – viel Erfolg!*\n"

    msg += "\n🔗 [mentor4trading.netlify.app](https://mentor4trading.netlify.app)"
    return msg


def send_to_telegram(message):
    """Nachricht an Telegram senden"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id":    CHANNEL_ID,
        "text":       message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        print(f"[OK] Nachricht gesendet! Message-ID: {r.json()['result']['message_id']}")
        return True
    except Exception as e:
        print(f"[ERROR] Telegram Fehler: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"       Response: {e.response.text}")
        return False


def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Bot startet...")

    # Config prüfen
    if BOT_TOKEN == "DEIN_BOT_TOKEN_HIER":
        print("[ERROR] BOT_TOKEN nicht gesetzt! Bitte in der Config anpassen.")
        sys.exit(1)

    # Kalender holen
    xml_data = fetch_calendar()
    if not xml_data:
        sys.exit(1)

    # Events parsen
    events = parse_events(xml_data)
    print(f"[INFO] {len(events)} relevante Events heute gefunden.")

    # Nachricht bauen
    message = build_message(events)
    print(f"[INFO] Nachricht:\n{message}\n")

    # Senden
    success = send_to_telegram(message)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
