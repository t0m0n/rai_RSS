
import os
import tempfile
from datetime import datetime as dt
from datetime import timedelta
from itertools import chain
from os.path import join as pathjoin
from urllib.parse import urljoin

import requests
from feedendum import Feed, FeedItem, to_rss_string
from bs4 import BeautifulSoup
import re

NSITUNES = "{http://www.itunes.com/dtds/podcast-1.0.dtd}"

def resolve_final_mp3_url(indirect_url):
    try:
        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; RaiFeedBot/1.0)"
        }
        response = session.get(indirect_url, timeout=10, headers=headers, allow_redirects=True)

        if response.history and response.url.endswith(".mp3"):
            return response.url

        soup = BeautifulSoup(response.content, 'html.parser')
        for audio_tag in soup.find_all("audio"):
            src = audio_tag.get("src")
            if src and src.endswith(".mp3"):
                return src

        match = re.search(r'https?://[^\s"]+\.mp3', response.text)
        if match:
            return match.group(0)

        return indirect_url
    except Exception as e:
        print(f"[resolve_final_mp3_url] Failed to resolve {indirect_url}: {e}")
        return indirect_url

def url_to_filename(url: str) -> str:
    return url.split("/")[-1] + ".xml"

def _datetime_parser(s: str) -> dt | None:
    if not s:
        return None
    for fmt in ("%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M", "%Y-%m-%d"):
        try:
            return dt.strptime(s, fmt)
        except ValueError:
            continue
    return None

class RaiParser:
    def __init__(self, url: str, folderPath: str) -> None:
        self.url = url
        self.folderPath = folderPath
        self.inner: list[Feed] = []

    def extend(self, url: str) -> None:
        url = urljoin(self.url, url)
        if url == self.url or url in (f.url for f in self.inner):
            return
        parser = RaiParser(url, self.folderPath)
        self.inner.extend(parser.process())

    def _json_to_feed(self, feed: Feed, rdata) -> None:
        feed.title = rdata["title"]
        feed.description = rdata["podcast_info"].get("description", "") or rdata["title"]
        feed.url = self.url
        feed._data["image"] = {"url": urljoin(self.url, rdata["podcast_info"]["image"])}
        feed._data[f"{NSITUNES}author"] = "RaiPlaySound"
        feed._data["language"] = "it-it"
        feed._data[f"{NSITUNES}owner"] = {f"{NSITUNES}email": "timedum@gmail.com"}

        categories = set()
        for c in chain(
            rdata["podcast_info"].get("genres", []),
            rdata["podcast_info"].get("subgenres", []),
            rdata["podcast_info"].get("dfp", {}).get("escaped_genres", []),
            rdata["podcast_info"].get("dfp", {}).get("escaped_typology", []),
        ):
            categories.add(c["name"])
        for c in rdata["podcast_info"].get("metadata", {}).get("product_sources", []):
            categories.add(c["name"])
        feed._data[f"{NSITUNES}category"] = [{"@text": c} for c in categories]

        feed.update = _datetime_parser(rdata.get("block", {}).get("update_date")) or _datetime_parser(rdata["track_info"]["date"])
        cards = rdata.get("block", {}).get("cards", [])

        for item in cards:
            if "/playlist/" in item.get("weblink", ""):
                self.extend(item["weblink"])
            if not item.get("audio"):
                continue
            fitem = FeedItem()
            fitem.title = item["toptitle"]
            fitem.id = "timendum-raiplaysound-" + item["uniquename"]
            fitem.update = _datetime_parser(item["create_date"] + " " + item["create_time"])
            fitem.url = urljoin(self.url, item["track_info"]["page_url"])
            fitem.content = item.get("description", item["title"])
            fitem._data = {
                "enclosure": {
                    "@type": "audio/mpeg",
                    "@url": resolve_final_mp3_url(urljoin(self.url, item["downloadable_audio"]["url"]).replace("http:", "https:"))
                    if item.get("downloadable_audio", {}).get("url") else urljoin(self.url, item["audio"]["url"])
                },
                f"{NSITUNES}title": fitem.title,
                f"{NSITUNES}summary": fitem.content,
                f"{NSITUNES}duration": item["audio"]["duration"],
                "image": {"url": urljoin(self.url, item["image"])},
            }
            if item.get("season") and item.get("episode"):
                fitem._data[f"{NSITUNES}season"] = item["season"]
                fitem._data[f"{NSITUNES}episode"] = item["episode"]
            feed.items.append(fitem)

    def process(self, skip_programmi=True, skip_film=True, date_ok=False, reverse=False) -> list[Feed]:
        try:
            result = requests.get(self.url + ".json")
            result.raise_for_status()
            rdata = result.json()
        except Exception as e:
            print(f"Errore durante la richiesta di {self.url}: {e}")
            return []

        typology = rdata["podcast_info"].get("typology", "").lower()
        if skip_programmi and typology in ("programmi radio", "informazione notiziari"):
            print(f"Skipped programmi: {self.url} ({typology})")
            return []
        if skip_film and typology in ("film", "fiction"):
            print(f"Skipped film: {self.url} ({typology})")
            return []

        for tab in rdata.get("tab_menu", []):
            if tab["content_type"] == "playlist":
                self.extend(tab["weblink"])

        feed = Feed()
        self._json_to_feed(feed, rdata)

        if feed.items:
            feed.sort_items(reverse=reverse)
            filename = pathjoin(self.folderPath, url_to_filename(self.url))
            atomic_write(filename, to_rss_string(feed))
            print(f"Written {filename}")

        return [feed] + self.inner

def atomic_write(filename, content: str):
    tmp = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf8", delete=False,
        dir=os.path.dirname(filename), prefix=".tmp-single-", suffix=".xml"
    )
    tmp.write(content)
    tmp.close()
    os.replace(tmp.name, filename)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Genera un RSS da un programma di RaiPlaySound.")
    parser.add_argument("url", help="URL di un podcast (o playlist) su raiplaysound.")
    parser.add_argument("-f", "--folder", help="Cartella in cui scrivere il RSS podcast.", default=".")
    parser.add_argument("--film", help="Elabora anche se è un film.", action="store_true")
    parser.add_argument("--programma", help="Elabora anche se è un programma.", action="store_true")
    parser.add_argument("--dateok", help="Lascia inalterate le date.", action="store_true")
    parser.add_argument("--reverse", help="Ordina gli episodi dal più recente.", action="store_true")
    args = parser.parse_args()
    parser = RaiParser(args.url, args.folder)
    parser.process(
        skip_programmi=not args.programma,
        skip_film=not args.film,
        date_ok=args.dateok,
        reverse=args.reverse,
    )

if __name__ == "__main__":
    main()
