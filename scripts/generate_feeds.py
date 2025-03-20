import requests
import json

# Lista dei programmi e relativi file XML
PROGRAMS = {
    "ungiornodapecora": "https://www.raiplaysound.it/programmi/ungiornodapecora",
    "zapping": "https://www.raiplaysound.it/programmi/zapping",
    "radioanchio": "https://www.raiplaysound.it/programmi/radioanchio"
}

for name, url in PROGRAMS.items():
    api_url = f"https://timendum.github.io/raiplaysound/diy?url={url}"

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()

        # Creazione del file XML
        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0">\n<channel>\n'
        xml_content += f"<title>{data['title']}</title>\n"

        for item in data['episodes']:
            xml_content += f"<item>\n<title>{item['title']}</title>\n"
            xml_content += f"<link>{item['url']}</link>\n</item>\n"

        xml_content += "</channel>\n</rss>"

        # Salva il file XML con il nome del programma
        file_name = f"feed_{name}.xml"
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(xml_content)

        print(f"✅ Feed XML generato per {name}!")

    except Exception as e:
        print(f"❌ Errore per {name}: {e}")
