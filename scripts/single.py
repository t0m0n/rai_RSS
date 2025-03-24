import datetime
import re
import requests
import xml.etree.ElementTree as ET

RAIPLAY_WORKER_URL = 'https://raiplay-proxy.giuliomagnifico.workers.dev/?url='

def extract_date_from_string(date_string):
    match = re.search(r'(\d{2})/(\d{2})/(\d{4})', date_string)
    if match:
        day, month, year = map(int, match.groups())
        try:
            return datetime.datetime(year, month, day, 8, 15, 0, tzinfo=datetime.timezone.utc)
        except ValueError:
            return None
    return None

def get_item_date(item):
    title = item.get('title', '')
    date_from_title = extract_date_from_string(title)
    if date_from_title:
        return date_from_title
    return datetime.datetime.now(datetime.timezone.utc)

def resolve_final_mp3_url(url):
    response = requests.get(f'{RAIPLAY_WORKER_URL}{url}')
    if response.status_code == 200:
        return response.text.strip()
    return url

def build_rss_item(item):
    title = item.get('title', 'No Title')
    description = item.get('description', '')
    pub_date = get_item_date(item)

    downloadable_audio = item.get('downloadable_audio', '')
    resolved_audio_url = resolve_final_mp3_url(downloadable_audio)

    rss_item = ET.Element('item')
    ET.SubElement(rss_item, 'title').text = title
    ET.SubElement(rss_item, 'description').text = description
    ET.SubElement(rss_item, 'pubDate').text = pub_date.strftime('%a, %d %b %Y %H:%M:%S %z')
    enclosure = ET.SubElement(rss_item, 'enclosure')
    enclosure.set('url', resolved_audio_url)
    enclosure.set('type', 'audio/mpeg')

    return rss_item

def generate_rss_feed(podcast_data, podcast_title, podcast_link):
    rss = ET.Element('rss')
    rss.set('version', '2.0')
    channel = ET.SubElement(rss, 'channel')
    ET.SubElement(channel, 'title').text = podcast_title
    ET.SubElement(channel, 'link').text = podcast_link
    ET.SubElement(channel, 'description').text = f'Feed RSS for {podcast_title}'

    for item in podcast_data:
        rss_item = build_rss_item(item)
        channel.append(rss_item)

    return ET.tostring(rss, encoding='utf-8', xml_declaration=True).decode('utf-8')

def main(podcast_data, podcast_title, podcast_link):
    rss_feed_xml = generate_rss_feed(podcast_data, podcast_title, podcast_link)
    print(rss_feed_xml)
