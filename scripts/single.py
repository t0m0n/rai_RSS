import sys
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from feedendum import Feed, Item
from urllib.parse import urljoin
import re
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"
}

def fetch_html(url):
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.text

def resolve_final_mp3_url(url):
    try:
        resp = requests.get(url, headers=HEADERS, allow_redirects=True, timeout=10)
        if resp.status_code == 200 and ".mp3" in resp.url:
            return resp.url
    except Exception:
        pass
    return url

def parse_audio_items(program_url):
    html = fetch_html(program_url)
    soup = BeautifulSoup(html, "lxml")

    script_tag = soup.find("script", text=re.compile("__PRELOADED_STATE__"))
    if not script_tag:
        raise ValueError("Script with __PRELOADED_STATE__ not found.")

    raw_json = re.search(r"__PRELOADED_STATE__ = (.*?);
", script_tag.string).group(1)
    import json
    data = json.loads(raw_json)

    episodes = data["audio"]["items"]
    program_data = data["audio"]["program"]

    items = []
    for item in episodes:
        title = item.get("name") or item.get("title")
        summary = item.get("subtitle") or item.get("description", "")
        pub_date = datetime.strptime(item["datePublished"], "%Y-%m-%dT%H:%M:%S.%fZ")
        page_url = urljoin("https://www.raiplaysound.it/", item["pathId"])

        enclosure_url = item.get("downloadable_audio", {}).get("url") or item.get("audio", {}).get("url")
        if enclosure_url:
            enclosure_url = resolve_final_mp3_url(enclosure_url)

        items.append(Item(
            title=title,
            guid=f"timendum-raiplaysound-{item['id']}",
            pubDate=pub_date,
            link=page_url,
            description=summary,
            enclosure={"type": "audio/mpeg", "url": enclosure_url},
            itunes_title=title,
            itunes_summary=summary,
            itunes_duration=item.get("duration"),
            image={"url": program_data.get("image", "")}
        ))
    return items, program_data

def generate_feed(program_slug, program_url, output_path):
    try:
        items, program_data = parse_audio_items(program_url)

        feed = Feed(
            title=program_data.get("title", program_slug),
            description=program_data.get("description", ""),
            pubDate=datetime.utcnow(),
            link=f"https://www.raiplaysound.it/programmi/{program_slug}",
            image={"url": program_data.get("image", "")},
            itunes_author="RaiPlaySound",
            language="it-it",
            itunes_owner={"email": "timedum@gmail.com"},
            itunes_category=[
                {"text": "Programmiradio"},
                {"text": "Tecnologia"},
                {"text": "Digitale"},
                {"text": "Tecnologico"},
                {"text": "Messa in onda Radio"},
                {"text": "Biotecnologie"},
            ],
            items=items
        )

        feed_xml = feed.to_string(pretty=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(feed_xml)
    except Exception as e:
        print(f"Errore nell'esecuzione di single.py per {program_slug}: {e}", file=sys.stderr)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: single.py <program_slug> <program_url> <output_path>")
        sys.exit(1)

    slug = sys.argv[1]
    url = sys.argv[2]
    output = sys.argv[3]
    generate_feed(slug, url, output)
