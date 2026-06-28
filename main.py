"""Monitor B17.ru forum for demo consultations with zero replies."""

from __future__ import annotations

import html
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
SEEN_RETENTION_DAYS = 7
CONSULTANT_RE = re.compile(r"\(Консультирует:\s*(.+?)\)")
FORUM_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.b17.ru/",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}
FETCH_RETRIES = 4
FETCH_RETRY_DELAYS = (5, 15, 30, 60)


@dataclass(frozen=True)
class Topic:
    topic_id: str
    title: str
    url: str
    author_line: str
    consultant: str | None


def fetch_forum_page(url: str) -> str:
    session = requests.Session()
    session.headers.update(FORUM_HEADERS)

    try:
        session.get("https://www.b17.ru/", timeout=30)
        time.sleep(1)
    except requests.RequestException as exc:
        print(f"Warning: warmup request failed: {exc}", file=sys.stderr)

    last_error: requests.RequestException | None = None

    for attempt in range(FETCH_RETRIES):
        try:
            response = session.get(url, timeout=30)
        except requests.RequestException as exc:
            last_error = exc
            delay = FETCH_RETRY_DELAYS[min(attempt, len(FETCH_RETRY_DELAYS) - 1)]
            print(f"Request failed: {exc}, retry in {delay}s", file=sys.stderr)
            time.sleep(delay)
            continue

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "")
            if retry_after.isdigit():
                delay = int(retry_after)
            else:
                delay = FETCH_RETRY_DELAYS[min(attempt, len(FETCH_RETRY_DELAYS) - 1)]
            print(
                f"Rate limited (429), retry in {delay}s "
                f"(attempt {attempt + 1}/{FETCH_RETRIES})",
                file=sys.stderr,
            )
            time.sleep(delay)
            continue

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            last_error = exc
            if attempt < FETCH_RETRIES - 1:
                delay = FETCH_RETRY_DELAYS[min(attempt, len(FETCH_RETRY_DELAYS) - 1)]
                print(f"HTTP error: {exc}, retry in {delay}s", file=sys.stderr)
                time.sleep(delay)
                continue
            raise

        response.encoding = response.apparent_encoding or "utf-8"
        return response.text

    if last_error is not None:
        raise last_error

    raise RuntimeError("Failed to fetch forum page after retries")


def parse_topics(page_html: str) -> list[Topic]:
    soup = BeautifulSoup(page_html, "html.parser")
    topics: list[Topic] = []

    for row in soup.select('tr.list[id^="topic_"]'):
        if not row.select_one("td.i .ico_svg_f2"):
            continue

        replies_span = row.select_one("td.n span")
        if replies_span is None or replies_span.get_text(strip=True) != "0":
            continue

        row_id = row.get("id", "")
        if not row_id.startswith("topic_"):
            continue
        topic_id = row_id.removeprefix("topic_")

        title_link = row.select_one("td.t a")
        title = title_link.get_text(strip=True) if title_link else "Без названия"

        fio_el = row.select_one("td.t .fio")
        author_line = fio_el.get_text(" ", strip=True) if fio_el else ""
        consultant = None
        if fio_el:
            match = CONSULTANT_RE.search(fio_el.get_text(" ", strip=True))
            if match:
                consultant = match.group(1).strip()

        topics.append(
            Topic(
                topic_id=topic_id,
                title=title,
                url=f"https://www.b17.ru/forum/topic.php?id={topic_id}",
                author_line=author_line,
                consultant=consultant,
            )
        )

    return topics


def load_seen(data_dir: Path) -> dict[str, str]:
    seen_file = data_dir / "seen_topics.json"
    if not seen_file.exists():
        return {}

    try:
        data = json.loads(seen_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Warning: could not read {seen_file}: {exc}", file=sys.stderr)
        return {}

    if not isinstance(data, dict):
        return {}

    return {str(k): str(v) for k, v in data.items()}


def prune_seen(seen: dict[str, str], retention_days: int = SEEN_RETENTION_DAYS) -> dict[str, str]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    pruned: dict[str, str] = {}

    for topic_id, notified_at in seen.items():
        try:
            notified_dt = datetime.fromisoformat(notified_at)
            if notified_dt.tzinfo is None:
                notified_dt = notified_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if notified_dt >= cutoff:
            pruned[topic_id] = notified_at

    return pruned


def save_seen(data_dir: Path, seen: dict[str, str]) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    seen_file = data_dir / "seen_topics.json"
    seen_file.write_text(
        json.dumps(seen, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def format_telegram_message(topic: Topic) -> str:
    safe_url = html.escape(topic.url, quote=True)
    safe_title = html.escape(topic.title)
    lines = [
        "Новая демо-консультация без ответов",
        "",
        f'<a href="{safe_url}"><b>{safe_title}</b></a>',
    ]
    if topic.author_line:
        lines.append(html.escape(topic.author_line))
    if topic.consultant and topic.consultant not in topic.author_line:
        lines.append(f"Консультирует: {html.escape(topic.consultant)}")
    lines.append(f'\n<a href="{safe_url}">Открыть тему на B17.ru</a>')
    return "\n".join(lines)


def send_telegram_message(token: str, chat_id: str, text: str) -> None:
    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if not payload.get("ok"):
        raise RuntimeError(f"Telegram API error: {payload}")


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def main() -> int:
    forum_url = os.environ.get("FORUM_URL", "https://www.b17.ru/forum/").strip()
    data_dir = Path(os.environ.get("DATA_DIR", "./data"))

    try:
        token = require_env("TELEGRAM_BOT_TOKEN")
        chat_id = require_env("TELEGRAM_CHAT_ID")
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1

    try:
        page_html = fetch_forum_page(forum_url)
    except requests.RequestException as exc:
        print(f"Failed to fetch forum page: {exc}", file=sys.stderr)
        return 1

    topics = parse_topics(page_html)
    seen = prune_seen(load_seen(data_dir))
    new_topics = [topic for topic in topics if topic.topic_id not in seen]

    if not new_topics:
        print("No new matching topics.")
        save_seen(data_dir, seen)
        return 0

    print(f"Found {len(new_topics)} new topic(s).")

    successfully_notified: list[Topic] = []
    for topic in new_topics:
        message = format_telegram_message(topic)
        try:
            send_telegram_message(token, chat_id, message)
        except (requests.RequestException, RuntimeError) as exc:
            print(
                f"Failed to notify about topic {topic.topic_id}: {exc}",
                file=sys.stderr,
            )
            continue
        successfully_notified.append(topic)
        print(f"Notified: {topic.topic_id} — {topic.title}")

    now = datetime.now(timezone.utc).isoformat()
    for topic in successfully_notified:
        seen[topic.topic_id] = now

    save_seen(data_dir, seen)
    return 0 if successfully_notified else 1


if __name__ == "__main__":
    raise SystemExit(main())
