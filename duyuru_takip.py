import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
import json
from pathlib import Path
from urllib.parse import urljoin
import os

URL = "https://www.isikun.edu.tr/akademik/lisansustu/duyurular"
KEYWORD = "psikoloji"
SEEN_FILE = Path("seen_announcements.json")

SENDER_EMAIL = os.environ["SENDER_EMAIL"]
SENDER_APP_PASSWORD = os.environ["SENDER_APP_PASSWORD"]
RECEIVER_EMAIL = os.environ["RECEIVER_EMAIL"]


def load_seen():
    if not SEEN_FILE.exists():
        return set()

    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()

            if not content:
                return set()

            return set(json.loads(content))
    except Exception:
        return set()


def save_seen(seen):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f, ensure_ascii=False, indent=2)


def send_email(title, link):
    subject = "Yeni Psikoloji Duyurusu Yayınlandı"

    body = f"""Yeni bir psikoloji duyurusu bulundu:

Başlık:
{title}

Link:
{link}
"""

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    # Gmail SMTP
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
        server.send_message(msg)


def fetch_announcements():
    response = requests.get(
        URL,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=20
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    announcements = []

    for a in soup.find_all("a"):
        title = a.get_text(" ", strip=True)

        if not title:
            continue

        if KEYWORD.lower() in title.lower():
            href = a.get("href")
            link = urljoin(URL, href) if href else URL

            announcements.append({
                "title": title,
                "link": link
            })

    return announcements


def main():
    seen = load_seen()
    announcements = fetch_announcements()

    new_items = []

    for item in announcements:
        unique_key = item["link"]

        if unique_key not in seen:
            new_items.append(item)
            seen.add(unique_key)

    if new_items:
        for item in new_items:
            send_email(item["title"], item["link"])
            print("Mail atıldı:", item["title"])
    else:
        print("Yeni duyuru yok.")

    save_seen(seen)


if __name__ == "__main__":
    main()