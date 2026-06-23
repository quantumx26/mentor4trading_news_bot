#!/usr/bin/env python3
"""
Mentor4Trading – ForexFactory Kalender Bot
+ Täglicher Homepage Hinweis (20:00)
+ Wöchentlicher Indikator Post (Sonntag 20:00)
+ Wöchentlicher Twitch/TikTok Hinweis (Sonntag 18:00)
+ Täglicher Community Hinweis (19:00)
+ Trading Mindset Post (Montag 09:00)
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import pytz
import os
import sys
import random
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
BOT_TOKEN   = os.environ.get("BOT_TOKEN", "")
CHANNEL_ID  = os.environ.get("CHANNEL_ID", "")
CURRENCIES  = ["USD"]
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

MINDSET_MESSAGES = [
    ("Revenge Trading", "Nach einem Loss sofort wieder rein zu gehen ist der schnellste Weg ein Konto zu ruinieren.\n\n✅ Regel: Nach 2 Losses am Tag → Trading Stop\n✅ 30 Minuten Pause nach jedem Loss\n✅ Emotionen raus, Prozess rein"),
    ("FOMO – Fear of Missing Out", "Du siehst einen Trade der ohne dich läuft und springst rein. Das endet fast immer mit einem Loss.\n\n✅ Regel: Kein Setup = kein Trade\n✅ Es gibt immer den nächsten Move\n✅ Geduld ist die profitabelste Fähigkeit"),
    ("Stop Loss Disziplin", "Den SL zu verschieben weil du hoffst der Markt dreht noch – das ist keine Strategie, das ist Gambling.\n\n✅ SL setzen = SL respektieren\n✅ Kein SL = kein professionelles Trading\n✅ Ein kontrollierter Loss ist besser als ein geblasenes Konto"),
    ("Overtrading", "Mehr Trades bedeuten nicht mehr Gewinn. Die besten Trader machen wenige, aber hochwertige Trades.\n\n✅ Qualität über Quantität\n✅ Warte auf A+ Setups\n✅ Kein Setup da? Nicht traden!"),
    ("Drawdown Mentalität", "Jeder Trader hat Drawdown-Phasen. Was dich unterscheidet ist wie du damit umgehst.\n\n✅ Drawdown ist normal – kein Grund zur Panik\n✅ Reduziere die Positionsgröße in schwachen Phasen\n✅ Analysiere was nicht funktioniert"),
    ("Journaling", "Die meisten Trader wissen nicht warum sie verlieren – weil sie kein Journal führen.\n\n✅ Jeden Trade dokumentieren\n✅ Entry, SL, TP, Begründung notieren\n✅ Wöchentlich auswerten und lernen"),
    ("Erwartungsmanagement", "Trading ist kein schnelles Geld. Es ist ein Handwerk das Jahre braucht.\n\n✅ Realistische Erwartungen setzen\n✅ Fokus auf den Prozess, nicht den Profit\n✅ Konsistenz über 6 Monate schlägt jeden Glückstreffer"),
    ("Positionsgröße", "Zu groß zu traden ist der Hauptgrund warum Trader Konten verbrennen.\n\n✅ Max 1-2% Risiko pro Trade\n✅ Kleinere Größe = klarer Kopf\n✅ Mit kleinem Risiko kommen große Gewinne langfristig"),
    ("Verluste akzeptieren", "Losses gehören zum Trading wie Regen zum Wetter. Du kannst sie nicht vermeiden – nur managen.\n\n✅ Ein Loss ist kein Versagen\n✅ 50% Win Rate kann profitabel sein\n✅ RR und Konsistenz zählen mehr"),
    ("Gier kontrollieren", "Wenn ein Trade gut läuft und du den TP verschiebst aus Gier – oft endet das mit BE oder Loss.\n\n✅ Plan den Trade, trade den Plan\n✅ TP setzen und respektieren\n✅ Partial profits nehmen und Rest laufen lassen"),
    ("Routine & Vorbereitung", "Profis gehen nicht zufällig an den Markt. Sie haben eine Routine.\n\n✅ Täglich Kalender checken\n✅ Bias vor dem Trade festlegen\n✅ Nur traden wenn der Markt dein Setup gibt"),
    ("Bildschirmzeit reduzieren", "Je mehr du den Chart anstarrst, desto mehr siehst du Setups die keine sind.\n\n✅ Alerts setzen statt starren\n✅ Setze deine Zonen und warte\n✅ Weniger Chart = bessere Entscheidungen"),
    ("Vertrauen in die Strategie", "Nach 3 Losses zweifelt man an der Strategie – das ist menschlich aber gefährlich.\n\n✅ Backteste deine Strategie\n✅ Vertraue dem System über mindestens 50 Trades\n✅ Ein schlechter Tag ändert keine gute Strategie"),
    ("Morgenroutine", "Wie du den Tag startest beeinflusst wie du tradest.\n\n✅ Nicht direkt nach dem Aufwachen traden\n✅ Kalender und News checken\n✅ Klaren Kopf haben bevor der erste Trade kommt"),
    ("Das Ego loslassen", "Der Markt schuldet dir nichts. Dein Ego ist dein größter Feind.\n\n✅ Der Markt hat immer Recht\n✅ Falsch liegen ist okay – spät zugeben ist teuer\n✅ Flexibel bleiben und anpassen"),
    ("Konsistenz schlägt alles", "Ein Trader mit 55% Win Rate und gutem RR schlägt langfristig jeden der auf Glück setzt.\n\n✅ Jeden Tag dieselbe Routine\n✅ Dieselben Regeln für jeden Trade\n✅ Konsistenz ist das Einzige was zählt"),
    ("Break nehmen", "Manchmal ist der beste Trade kein Trade.\n\n✅ Wenn nichts klappt → Pause machen\n✅ 1-2 Tage weg vom Chart können Wunder wirken\n✅ Erholung ist Teil des Prozesses"),
    ("News und Volatilität", "Viele Trader verlieren bei News weil sie impulsiv reagieren.\n\n✅ Vor High-Impact News aus offenen Trades raus\n✅ Warte bis die Volatilität sich legt\n✅ Der beste Move kommt oft nach der ersten Reaktion"),
    ("Realistische Ziele", "5% pro Tag ist kein Ziel – das ist ein Wunsch der zu Overtrading führt.\n\n✅ 1-3% pro Woche ist ein professionelles Ziel\n✅ Fokus auf R-Multiple, nicht auf Geldbeträge\n✅ Langfristig denken"),
    ("Der Prozess ist das Ziel", "Wer nur auf den Profit fokussiert ist, verliert meistens. Wer den Prozess perfektioniert, gewinnt langfristig.\n\n✅ Jeder Trade muss dem System folgen\n✅ Gutes Ergebnis durch schlechten Prozess zählt nicht\n✅ Schlechtes Ergebnis durch guten Prozess ist okay"),
    ("Verliere nie mehr als geplant", "Definiere vor dem Trade: Wie viel bin ich bereit zu verlieren?\n\n✅ Max Loss pro Tag festlegen\n✅ Bei Erreichen sofort aufhören\n✅ Kapital schützen ist Priorität 1"),
    ("Backtest deine Strategie", "Du weißt nicht ob deine Strategie funktioniert wenn du sie nicht getestet hast.\n\n✅ Mindestens 100 historische Trades analysieren\n✅ Win Rate und RR berechnen\n✅ Dann live mit kleiner Größe starten"),
    ("Emotionen erkennen", "Angst und Gier sind die zwei größten Feinde des Traders.\n\n✅ Lerne deine emotionalen Trigger kennen\n✅ Schreibe auf wie du dich beim Traden fühlst\n✅ Entscheidungen nie aus Emotionen treffen"),
    ("Die 3 Säulen", "Erfolgreiches Trading basiert auf 3 Dingen:\n\n✅ Eine bewährte Strategie\n✅ Konsequentes Risikomanagement\n✅ Emotionale Kontrolle\n\nFehlt eine Säule, wackelt alles."),
    ("Keine heilige Gralssuche", "Es gibt keine perfekte Strategie die immer funktioniert.\n\n✅ Jede Strategie hat Verlustphasen\n✅ Wichtig ist wie du damit umgehst\n✅ Simpel und konsistent schlägt komplex"),
    ("Der Unterschied zwischen Profis und Anfängern", "Anfänger fokussieren sich auf Gewinne. Profis fokussieren sich auf Verluste.\n\n✅ Wie viel verlierst du pro Trade?\n✅ Wie viel verlierst du pro Woche?\n✅ Wer Verluste kontrolliert, kontrolliert alles"),
    ("Geduld als Edge", "Die meisten Verluste kommen durch Trades die man erzwungen hat.\n\n✅ Warte auf den perfekten Entry\n✅ Kein Trade ist auch eine Position\n✅ Geduld ist dein stärkster Edge"),
    ("Risiko vs Reward", "Ein Trade mit 1:1 RR muss 60%+ Win Rate haben um profitabel zu sein.\n\n✅ Minimum 1:2 RR anstreben\n✅ Bei 1:3 RR reicht 35% Win Rate\n✅ RR ist wichtiger als Win Rate"),
    ("Nach dem Loss", "Was du nach einem Loss tust entscheidet über deinen langfristigen Erfolg.\n\n✅ Pause machen\n✅ Trade analysieren – war der Prozess korrekt?\n✅ Weiter machen – nicht aufgeben"),
    ("Wochenstart Ritual", "Wie startest du in die Handelswoche?\n\n✅ Sonntag Abend: Kalender checken\n✅ Wichtige Level markieren\n✅ Bias festlegen bevor der Markt öffnet"),
    ("Keine Ausreden", "Der Markt war manipuliert. Der Broker hat mich rausgestoppt. Das war Pech.\n\n✅ Nimm Verantwortung für deine Trades\n✅ Analysiere was du besser machen kannst\n✅ Ausreden machen dich nicht besser"),
    ("Kleiner anfangen", "Viele Anfänger starten mit zu viel Kapital und zu großen Positionen.\n\n✅ Starte mit Micro Lots oder Mini Kontrakte\n✅ Lerne den Prozess bevor du skalierst\n✅ Größe erhöhen erst nach 3 profitablen Monaten"),
    ("Der beste Trade", "Oft ist der beste Trade der Trade den du NICHT gemacht hast.\n\n✅ Nicht jede Bewegung ist ein Setup\n✅ Wählerisch sein ist eine Fähigkeit\n✅ Weniger ist mehr"),
    ("Markstruktur verstehen", "Ohne Marktstruktur zu verstehen tradest du blind.\n\n✅ Lerne CHoCH und BOS\n✅ Verstehe Trends und Ranges\n✅ Struktur gibt dir den Kontext für jeden Trade"),
    ("Dein Warum", "Warum tradest du? Wenn die Antwort nur Geld ist, wirst du scheitern.\n\n✅ Finde dein tieferes Warum\n✅ Freiheit? Unabhängigkeit? Selbstentwicklung?\n✅ Das Warum hält dich durch schwierige Phasen"),
    ("Vergleiche dich nicht", "Andere posten ihre Wins auf Social Media – du siehst nie ihre Losses.\n\n✅ Fokus auf deinen eigenen Weg\n✅ Vergleiche dich nur mit dir gestern\n✅ Trading ist individuell"),
    ("Wochenendrückblick", "Die besten Trader analysieren jede Woche ihre Performance.\n\n✅ Was lief gut diese Woche?\n✅ Was kann ich verbessern?\n✅ Welche Trades hätte ich nicht nehmen sollen?"),
    ("Liquidität verstehen", "Der Markt bewegt sich dorthin wo Liquidität liegt.\n\n✅ Lerne wo Stop Loss Cluster liegen\n✅ Verstehe warum Highs und Lows genommen werden\n✅ Smart Money jagt Liquidität bevor es dreht"),
    ("Session Timing", "Nicht jede Tageszeit ist gleich gut zum Traden.\n\n✅ London Open 08:00-12:00 für Bewegung\n✅ New York Open 14:30-16:30 für Volatilität\n✅ Mittags und Abends oft choppy"),
    ("Dein Trading System", "Ein System das du nicht 100% verstehst wirst du nicht 100% ausführen können.\n\n✅ Verstehe jeden Aspekt deiner Strategie\n✅ Sei in der Lage es anderen zu erklären\n✅ Nur dann kannst du ihm vertrauen"),
    ("Kontoführung", "Wie du dein Konto führst ist genauso wichtig wie deine Strategie.\n\n✅ Nie mehr als 2% pro Trade riskieren\n✅ Bei 10% Drawdown Pause einlegen\n✅ Gewinne regelmäßig auszahlen"),
    ("Fehler wiederholen", "Den gleichen Fehler zweimal zu machen ist kein Pech – es ist ein Muster.\n\n✅ Erkenne deine häufigsten Fehler\n✅ Schreibe sie auf und lies sie vor dem Trading\n✅ Bewusstsein ist der erste Schritt zur Verbesserung"),
    ("Long term thinking", "Trading ist ein Marathon, kein Sprint.\n\n✅ Denke in Monaten und Jahren, nicht in Tagen\n✅ Ein schlechter Monat ruiniert kein gutes Jahr\n✅ Bleib im Spiel – das ist die wichtigste Regel"),
    ("Selbstvertrauen aufbauen", "Selbstvertrauen im Trading kommt durch Vorbereitung und Konsistenz – nicht durch Glück.\n\n✅ Backteste deine Strategie\n✅ Führe ein Journal\n✅ Vertrauen kommt durch Beweise, nicht durch Hoffnung"),
    ("Accepting Uncertainty", "Niemand weiß was der Markt als nächstes macht – nicht mal die Profis.\n\n✅ Akzeptiere Unsicherheit\n✅ Manage das Risiko – kontrolliere nicht den Outcome\n✅ Wahrscheinlichkeiten spielen, nicht Sicherheiten suchen"),
    ("Die 1% Regel", "Werde jeden Tag 1% besser als Trader.\n\n✅ Lerne täglich etwas Neues\n✅ Analysiere deine Trades\n✅ Nach einem Jahr bist du 365% besser"),
    ("Erfolg neu definieren", "Erfolg im Trading bedeutet nicht immer Gewinn.\n\n✅ Dem System gefolgt? Erfolg.\n✅ SL respektiert? Erfolg.\n✅ Keine Revenge Trades? Erfolg."),
    ("Die Macht der Pause", "Eine Pause ist keine Niederlage – sie ist eine strategische Entscheidung.\n\n✅ Nach einer Verlustserie: Stop\n✅ Bei emotionalem Trading: Stop\n✅ Frischer Kopf = bessere Entscheidungen"),
    ("Sei dein eigener Coach", "Niemand kennt dein Trading besser als du selbst.\n\n✅ Analysiere dich selbst kritisch\n✅ Was würdest du einem Freund raten?\n✅ Behandle dich selbst wie einen professionellen Athleten"),
    ("Der Weg zum profitablen Trader", "Es gibt keine Abkürzung. Aber es gibt einen klaren Weg.\n\n✅ Lerne die Basics\n✅ Entwickle ein System\n✅ Teste es, passe es an\n✅ Führe es konsequent aus\n✅ Skaliere wenn es funktioniert"),
]


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


def build_mindset_message():
    titel, inhalt = random.choice(MINDSET_MESSAGES)
    msg  = f"🧠 *Trading Mindset – {titel}*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"{inhalt}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "🤖 Jarvis | @mentor4trading\\_signals"
    return msg


def build_community_message():
    msg  = "📊 *Mentor4Trading Marktanalyse*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "Willst du verstehen *warum* sich der Markt\n"
    msg += "bewegt – nicht nur *wann*?\n\n"
    msg += "📌 In meinem Marktanalyse Kanal erkläre ich:\n"
    msg += "• Warum ich in einen Trade gehe\n"
    msg += "• Warum ich einen Trade ablehne\n"
    msg += "• Marktstruktur & Trading-Konzepte\n\n"
    msg += "👉 Jetzt beitreten!\n"
    msg += "🔗 [t.me/mentor4trading\\_community](https://t.me/mentor4trading_community)\n"
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

    # 2. Trading Mindset → Montag um 19:00
    if weekday == 0 and hour == 19:
        print("[INFO] Posting: Trading Mindset")
        send_to_telegram(build_mindset_message())

    # 3. Marktanalyse Hinweis → täglich um 19:00
    if weekday == 1 and hour == 20:
        print("[INFO] Posting: Marktanalyse Hinweis")
        send_to_telegram(build_community_message())

    print("[DONE] Fertig.")


if __name__ == "__main__":
    main()
