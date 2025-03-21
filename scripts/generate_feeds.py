import os
import subprocess

programs = [
    "etabeta",
    "ungiornodapecora",
    "zapping",
    "radioanchio",
    "trapocoinedicola",
    "radio3scienza",
    "ledicoladiradio1",
]

for program in programs:
    print(f"Generazione feed per {program}...")
    try:
        subprocess.run(["python", "scripts/single.py", program], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Errore nell'esecuzione di single.py per {program}: {e}")
