import os
import tempfile
import requests
import re
from datetime import datetime as dt, timedelta
from urllib.parse import urljoin
from feedendum import Feed, FeedItem, to_rss_string
from itertools import chain

NSITUNES = "{http://www.itunes.com/dtds/podcast-1.0.dtd}"

def resolve_final_mp3_url(indirect_url):
    try:
        session = requests.Session()
        response = session.get(indirect_url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            for audio_tag in soup.find_all('audio'):
                src = audio_tag.get('src')
                if src and src.endswith(".mp3"):
                    return src
            match = re.search(r'https?://[^\s"]+\.mp3', response.text)
            if match:
                return match.group(0)
        return indirect_url
    except Exception:
        return indirect_url

def url_to_filename(url: str) -> str:
    return url.split("/")[-1] + ".xml"

def _datetime_parser(s: str) -> dt:
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%d/%m/%Y",
        "%d %b %Y",
        "%d-%m-%Y %H:%M:%S",
        "%Y-%m-%d"
    ]
    for fmt in formats:
        try:
            return dt.strptime(s, fmt)
        except ValueError:
            continue
    return dt.now()

class RaiParser:
    def __init__(self, url: str, folderPath: str) -> None:
        self.url = url
        self.folderPath = folderPath

    def process(self) -> None:
        response = requests.get(self.url + ".json")
        response.raise_for_status()
        rdata = response.json()

        feed = Feed()
        feed.title = rdata["title"]
        feed.description = rdata["podcast_info"].get("description", rdata["title"])
        feed.url = self.url
        feed._data["image"] = {"url": urljoin(self.url, rdata["podcast_info"]["image"])}
        feed._data[f"{NSITUNES}author"] = "RaiPlaySound"
        feed._data["language"] = "it-it"
        feed._data[f"{NSITUNES}owner"] = {f"{NSITUNES}email": "giuliomagnifico@gmail.com"}

        categories = {c["name"] for c in chain(
            rdata["podcast_info"]["genres"],
            rdata["podcast_info"]["subgenres"],
            rdata["podcast_info"]["dfp"].get("escaped_genres", []),
            rdata["podcast_info"]["dfp"].get("escaped_typology", []),
        )}

        feed._data[f"{NSITUNES}category"] = [{"@text": c} for c in sorted(categories)]

        cards = rdata["block"].get("cards", [])
        feed.items = []

        for item in cards:
            if not item.get("audio"):
                continue

            fitem = FeedItem()
            fitem.title = item["toptitle"]
            fitem.id = "giuliomagnifico-raiplay-feed-" + item["uniquename"]
            fitem.update = _datetime_parser(item["track_info"].get("date", dt.now().isoformat()))
            fitem.url = urljoin(self.url, item["track_info"]["page_url"])
            fitem.content = item.get("description", item["title"])

            enclosure_url = item["audio"].get("url")
            if item.get("downloadable_audio", {}).get("url"):
                enclosure_url = item["downloadable_audio"]["url"].replace("http:", "https:")

            fitem._data = {
                "enclosure": {
                    "@type": "audio/mpeg",
                    "@url": urljoin(self.url, enclosure_url),
                },
                f"{NSITUNES}title": fitem.title,
                f"{NSITUNES}summary": fitem.content,
                f"{NSITUNES}duration": item["audio"]["duration"],
                "image": {"url": urljoin(self.url, item["image"])},
            }

            feed.items.append(fitem)

        feed.items.sort(key=lambda x: x.update, reverse=True)

        filename = os.path.join(self.folderPath, url_to_filename(self.url))
        atomic_write(filename, to_rss_string(feed))

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

    parser = argparse.ArgumentParser(
        description="Genera RSS da RaiPlaySound",
        epilog="Info su https://github.com/giuliomagnifico/raiplay-feed/"
    )

    parser.add_argument("url", help="URL podcast RaiPlaySound")
    parser.add_argument("-f", "--folder", default=".", help="Cartella output")

    args = parser.parse_args()

    rai_parser = RaiParser(args.url, args.folder)
    rai_parser.process()

if __name__ == "__main__":
    main()
