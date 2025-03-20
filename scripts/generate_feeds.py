import os
import json
import subprocess

# Percorso dello script single.py
SCRIPT_PATH = os.path.abspath("scripts/single.py")

# Lista dei programmi da generare
PROGRAMS = {
    "ungiornodapecora": "https://www.raiplaysound.it/programmi/ungiornodapecora",
    "zapping": "https://www.raiplaysound.it/programmi/zapping",
    "radioanchio": "https://www.raiplaysound.it/programmi/radioanchio"
}

for name, url in PROGRAMS.items():
    print(f"📡 Generazione feed per {name}...")

    try:
        # Esegui lo script single.py per ottenere il JSON del programma
        result = subprocess.run(
            ["python3", SCRIPT_PATH, url],
            capture_output=True,
            text=True,
            check=True
        )

        # Converte l'output JSON in un dizionario Python
        data = json.loads(result.stdout)

        # Controlliamo che ci siano episodi
        if "episodes" not in data or not data["episodes"]:
            print(f"⚠ Nessun episodio trovato per {name}, salto...")
            continue  # Passiamo al prossimo programma

        # Creazione del file XML
        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0">\n<channel>\n'
        xml_content += f"<title>{data.get('title', 'Senza titolo')}</title>\n"

        for item in data['episodes']:
            xml_content += f"<item>\n<title>{item['title']}</title>\n"
            xml_content += f"<link>{item['url']}</link>\n</item>\n"

        xml_content += "</channel>\n</rss>"

        # Salva il file XML
        file_name = f"feed_{name}.xml"
        file_path = os.path.abspath(file_name)
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(xml_content)

        print(f"✅ Feed XML salvato: {file_path}")

    except subprocess.CalledProcessError as e:
        print(f"❌ Errore nell'esecuzione di single.py per {name}: {e.stderr}")
    except json.JSONDecodeError:
        print(f"❌ Errore nella conversione JSON per {name}, output ricevuto:\n{result.stdout}")
    except Exception as e:
        print(f"❌ Errore generico per {name}: {e}")
