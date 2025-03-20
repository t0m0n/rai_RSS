import requests
import json

# URL del programma che vuoi monitorare (cambia questo con qualsiasi altro programma)
PROGRAM_URL = "https://www.raiplaysound.it/programmi/ungiornodapecora"

# URL per generare il JSON tramite timendum.github.io
API_URL = f"https://timendum.github.io/raiplaysound/diy?url={PROGRAM_URL}"

try:
    response = requests.get(API_URL)
    response.raise_for_status()
    data = response.json()

    # Creazione del file XML
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0">\n<channel>\n'
    xml_content += f"<title>{data['title']}</title>\n"

    for item in data['episodes']:
        xml_content += f"<item>\n<title>{item['title']}</title>\n"
        xml_content += f"<link>{item['url']}</link>\n</item>\n"

    xml_content += "</channel>\n</rss>"

    # Salva il file XML
    with open("feed.xml", "w", encoding="utf-8") as f:
        f.write(xml_content)

    print("✅ Feed XML generato con successo!")

except Exception as e:
    print(f"❌ Errore: {e}")
