import os
import subprocess

SCRIPT_PATH = os.path.abspath("scripts/single.py")


PROGRAMS = {
    "ungiornodapecora": "https://www.raiplaysound.it/programmi/ungiornodapecora",
    "zapping": "https://www.raiplaysound.it/programmi/zapping",
    "radioanchio": "https://www.raiplaysound.it/programmi/radioanchio",
    "trapocoinedicola": "https://www.raiplaysound.it/programmi/trapocoinedicola",
    "radio3scienza": "https://www.raiplaysound.it/programmi/radio3scienza",
    "etabeta": "https://www.raiplaysound.it/programmi/etabeta",
    "ledicoladiradio1": "https://www.raiplaysound.it/programmi/ledicoladiradio1"
}

for name, url in PROGRAMS.items():
    print(f"Generazione feed per {name}...")

    try:
        result = subprocess.run(
            ["python3", SCRIPT_PATH, "--programma", url],
            capture_output=True,
            text=True,
            check=True
        )

        original_file = f"{name}.xml"

        if not os.path.exists(original_file):
            print(f"Errore: Il file {original_file} non è stato generato correttamente!")
            continue  
            
        new_file = f"feed_{name}.xml"
        os.rename(original_file, new_file)
        print(f"Feed XML salvato correttamente: {new_file}")

    except subprocess.CalledProcessError as e:
        print(f"Errore nell'esecuzione di single.py per {name}: {e.stderr}")
    except Exception as e:
        print(f"Errore generico per {name}: {e}")
