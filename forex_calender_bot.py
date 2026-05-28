#!/usr/bin/env python3
"""
Mentor4Trading – ForexFactory Kalender Bot
+ Täglicher Homepage Hinweis (20:00)
+ Wöchentlicher Indikator Post (Montag 08:00)
+ Wöchentlicher Twitch/TikTok Hinweis (Sonntag 18:00)
+ Täglicher Community Hinweis (12:00)
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
import pytz
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
BOT_TOKEN   = os.environ.get("BOT_TOKEN", "")
CHANNEL_ID  = os.environ.get("CHANNEL_ID", "")
CURRENCIES  = ["USD", "EUR"]
SHOW_HIGH   = True
SHOW_MEDIUM = True
SHOW_LOW    = False
TIMEZONE    = "Europe/Berlin"
# ─────────────────────────────────────────────

FF_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"

IMPACT_EMOJI = {
    "High":   "🔴",
    "Medium": "🟡",
    "Low":    "⚪",
}

FLAG_EMOJI = {
    "USD": "🇺🇸", "EUR": "🇪🇺"
}


def send_to_telegram(message):
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
        print(f"[OK] Gesendet!")
        return True
    except Exception as e:
        print(f"[ERROR] Telegram Fehler: {e}")
        return False


def fetch_calendar():
    try:
        r = requests.get(FF_URL, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        return r.content
    except Exception as e:
        print(f"[ERROR] Kalender abrufen fehlgeschlagen: {e}")
        return None


def parse_events(xml_data):
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

            if currency not in CURRENCIES: continue
            if impact == "High"   and not SHOW_HIGH:   continue
            if impact == "Medium" and not SHOW_MEDIUM:  continue
            if impact == "Low"    and not SHOW_LOW:     continue
            if impact == "Non-Economic":                continue

            try:
                event_date = datetime.strptime(date_str, "%m-%d-%Y").date()
            except:
                continue

            if event_date != today: continue

            if time_str and time_str.lower() not in ("", "all day", "tentative"):
                try:
                    dt_utc = datetime.strptime(
                        f"{date_str} {time_str}", "%m-%d-%Y %I:%M%p"
                    ).replace(tzinfo=timezone.utc)
                    dt_local = dt_utc.astimezone(pytz.timezone(TIMEZONE))
                    time_display = dt_local.strftime("%H:%M")
                    sort_key = dt_local
                except:
                    time_display = time_str
                    sort_key = datetime.max.replace(tzinfo=timezone.utc)
            else:
                time_display = "ganztägig"
                sort_key = datetime.max.replace(tzinfo=timezone.utc)

            events.append({
                "time": time_display, "currency": currency,
                "impact": impact, "title": title, "sort_key": sort_key
            })
        except:
            continue

    events.sort(key=lambda x: x["sort_key"])
    return events


def build_calendar_message(events):
    tz_berlin = pytz.timezone(TIMEZONE)
    now = datetime.now(tz_berlin)
    weekdays = {
        "Monday": "Montag", "Tuesday": "Dienstag", "Wednesday": "Mittwoch",
        "Thursday": "Donnerstag", "Friday": "Freitag",
        "Saturday": "Samstag", "Sunday": "Sonntag"
    }
    day_de  = weekdays.get(now.strftime("%A"), now.strftime("%A"))
    date_str = now.strftime(f"{day_de}, %d.%m.%Y")

    msg  = f"📅 *Wirtschaftskalender – {date_str}*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━\n\n"

    if not events:
        msg += "✅ Keine High-Impact Events heute – ruhiger Tag!\n"
    else:
        for e in events:
            emoji = IMPACT_EMOJI.get(e["impact"], "⚫")
            flag  = FLAG_EMOJI.get(e["currency"], "🌐")
            msg  += f"{emoji} `{e['time']}` {flag} *{e['currency']}* – {e['title']}\n"

    msg += "\n━━━━━━━━━━━━━━━━━━━━━\n"

    high_count = sum(1 for e in events if e["impact"] == "High")
    if high_count >= 3:
        msg += "⚠️ *Viele News heute – ggf. SL absichern, klein traden!*\n"
    elif high_count > 0:
        msg += "⚠️ *News beachten – ggf. vor Release aus Trades raus!*\n"
    else:
        msg += "📊 *Saubere Chartarbeit möglich – viel Erfolg!*\n"

    msg += "\n🔗 [mentor4trading.netlify.app](https://mentor4trading.netlify.app)"
    msg += "\n\n🤖 *Jarvis wünscht euch einen erfolgreichen Tag & perfekte Setups!* 💰"
    return msg


def build_homepage_message():
    msg  = "🌐 *Mehr von Mentor4Trading*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "📊 Gratis Ressourcen & Guides\n"
    msg += "📈 ORB Ebook · SMC Basics · Setups\n"
    msg += "🔗 [mentor4trading.netlify.app](https://mentor4trading.netlify.app)\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "@mentor4trading\\_signals"
    msg += "\n\n🤖 *Jarvis & Mentor4Trading wünschen euch einen schönen Abend* 💰"
    return msg


def build_indicator_message():
    msg  = "🎯 *SMC Entry Finder V6*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "Der Indikator den ich für alle\n"
    msg += "meine Signale nutze – jetzt\n"
    msg += "noch kostenlos verfügbar!\n\n"
    msg += "✅ Live Dashboard · Session & Bias\n"
    msg += "✅ Entry Zone Visualisierung\n"
    msg += "✅ Signal Filter mit Alerts\n\n"
    msg += "⚠️ *Ab Juni nur noch paid*\n"
    msg += "🔗 [Jetzt sichern](https://mentor4trading.netlify.app/indikator.html)\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "Link in Bio · @mentor4trading\\_signals"
    return msg


def build_live_message():
    msg  = "📺 *Verpasst? Kein Problem\\!*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "Alle Strategien & Live-Sessions\n"
    msg += "gibt es kostenlos bei mir!\n\n"
    msg += "🎮 *Twitch:* twitch.tv/mentor4trading\n"
    msg += "📱 *TikTok:* @mentor4trading\n\n"
    msg += "🎯 SMC · MNQ & MES Futures\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "Reinschauen & von echten\n"
    msg += "Trades lernen!\n"
    msg += "@mentor4trading\\_signals"
    return msg


def build_community_message():
    msg  = "💬 *Mentor4Trading Community*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "Du hast Fragen zu den Signalen,\n"
    msg += "dem Indikator oder der Strategie?\n\n"
    msg += "👉 Komm in unsere Community Gruppe!\n\n"
    msg += "🔗 [t.me/mentor4trading\\_community](https://t.me/mentor4trading_community)\n"
    msg += "📌 Dort beantwortet Jarvis deine Fragen\n"
    msg += "zu SMC, ICT, MNQ & MES automatisch!\n"
    msg += "Einfach @JarvisCommunityBot anschreiben!\n\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "🤖 Jarvis | @mentor4trading\\_signals"
    return msg


def main():
    tz_berlin  = pytz.timezone(TIMEZONE)
    now        = datetime.now(tz_berlin)
    weekday    = now.weekday()  # 0=Mo, 6=So
    hour       = now.hour

    print(f"[{now.strftime('%Y-%m-%d %H:%M')}] Bot startet...")

    if not BOT_TOKEN:
        print("[ERROR] BOT_TOKEN fehlt!")
        sys.exit(1)

    # 1. Wirtschaftskalender → Mo–Fr um 07:00
    if weekday < 5 and hour == 7:
        print("[INFO] Posting: Wirtschaftskalender")
        xml_data = fetch_calendar()
        if xml_data:
            events  = parse_events(xml_data)
            message = build_calendar_message(events)
            send_to_telegram(message)

    # 2. Community Hinweis → täglich um 12:00
    if hour == 12:
        print("[INFO] Posting: Community Hinweis")
        send_to_telegram(build_community_message())

    # 3. Täglicher Homepage Hinweis → täglich um 20:00
    if hour == 20:
        print("[INFO] Posting: Homepage Hinweis")
        send_to_telegram(build_homepage_message())

    # 4. Indikator Post → Montag um 08:00
    if weekday == 0 and hour == 8:
        print("[INFO] Posting: Indikator Post")
        send_to_telegram(build_indicator_message())

    # 5. Twitch/TikTok Hinweis → Sonntag um 18:00
    if weekday == 6 and hour == 18:
        print("[INFO] Posting: Live/Social Hinweis")
        send_to_telegram(build_live_message())

    print("[DONE] Fertig.")


if __name__ == "__main__":
    main()
