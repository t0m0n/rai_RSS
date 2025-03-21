import re
import sys
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from feedendum import Feed
from urllib.parse import urljoin

def resolve_final_mp3_url(original_url):
    try:
        response = requests.get(original_url, allow_redirects=True, timeout=10)
        response.raise_for_status()
        return response.url
    except Exception as e:
        print(f"Errore nel risolvere l'MP3 finale: {e}")
        return original_url

def create_feed(program_slug):
    base_url = f"https://www.raiplaysound.it/programmi/{program_slug}"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(base_url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    script_tag = soup.find("script", text=re.compile("__PRELOADED_STATE__"))
    if not script_tag:
        raise ValueError("Script con __PRELOADED_STATE__ non trovato.")

    raw_json = re.search(r"__PRELOADED_STATE__ = (.*?);", script_tag.string).group(1)
    data = eval(raw_json)

    episodes = data["programDetail"]["lastAudios"]
    if not episodes:
        raise ValueError("Nessun episodio trovato.")

    f = Feed(
        title=data["programDetail"]["programInfo"]["name"],
        description=data["programDetail"]["programInfo"]["description"],
        link=base_url,
        image_url=data["programDetail"]["programInfo"]["imageUrl"],
        language="it-it",
        author="RaiPlaySound",
        categories=[
            "Programmiradio",
            "Tecnologia",
            "Digitale",
            "Tecnologico",
            "Messa in onda Radio",
            "Biotecnologie"
        ],
        owner_email="timedum@gmail.com"
    )

    for episode in episodes:
        ep_url = episode["audio"]["url"]
        final_url = resolve_final_mp3_url(ep_url)

        f.add_item(
            title=episode["title"],
            link=f"https://www.raiplaysound.it/audio/{episode['seo_url']}",
            guid="timendum-raiplaysound-" + episode["id"],
            pub_date=episode["airedAt"],
            description=episode["subtitle"],
            enclosure_url=ep_url,
            enclosure_type="audio/mpeg",
            itunes_summary=episode["subtitle"],
            itunes_duration=episode["duration"],
            image_url=episode["image"],
            extra_tags=[
                {
                    "tag": "media:content",
                    "attrib": {
                        "url": final_url,
                        "type": "audio/mpeg"
                    }
                }
            ]
        )

    f.set_namespace("media", "http://search.yahoo.com/mrss/")
    output_file = f"feed_{program_slug}.xml"
    f.write(output_file)
    print(f"Feed scritto su {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python single.py <program_slug>")
        sys.exit(1)
    create_feed(sys.argv[1])
