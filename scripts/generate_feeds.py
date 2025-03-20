import os
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
        # Esegui lo script single.py con il flag --programma
        result = subprocess.run(
            ["python3", SCRIPT_PATH, "--programma", url],
            capture_output=True,
            text=True,
            check=True
        )

        # Il vero file XML è stato salvato con il nome originale
        original_file = f"{name}.xml"

        # Verifica se il file originale esiste
        if not os.path.exists(original_file):
            print(f"❌ Errore: Il file {original_file} non è stato generato correttamente!")
            continue  # Passa al prossimo programma

        # Rinominiamo il file corretto con il prefisso "feed_"
        new_file = f"feed_{name}.xml"
        os.rename(original_file, new_file)
        print(f"✅ Feed XML salvato correttamente: {new_file}")

    except subprocess.CalledProcessError as e:
        print(f"❌ Errore nell'esecuzione di single.py per {name}: {e.stderr}")
    except Exception as e:
        print(f"❌ Errore generico per {name}: {e}")
