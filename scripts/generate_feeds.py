import os
from single import RaiParser

SCRIPT_PATH = os.path.abspath("scripts/single.py")
PROGRAMS = {
    "lacittadamianto": "https://www.raiplaysound.it/programmi/lacittadamianto",
    "ilcolpodellostato": "https://www.raiplaysound.it/programmi/ilcolpodellostato",
    "lostatoparallelo": "https://www.raiplaysound.it/programmi/lostatoparallelo",
    "archividellafolliaincercadifrancobasaglia": "https://www.raiplaysound.it/programmi/archividellafolliaincercadifrancobasaglia",
    "14-18grandeguerra100annidopo": "https://www.raiplaysound.it/programmi/14-18grandeguerra100annidopo",
    "nonapriteicassettidelpoteremanipuliteeloscandalodelletangenti": "https://www.raiplaysound.it/programmi/nonapriteicassettidelpoteremanipuliteeloscandalodelletangenti",
    "vivalitalialemortidifaustoeiaio": "https://www.raiplaysound.it/programmi/vivalitalialemortidifaustoeiaio",
    "25aprile-dietrolelineenemiche": "https://www.raiplaysound.it/programmi/25aprile-dietrolelineenemiche"
}
for name, url in PROGRAMS.items():
    print(f"Generazione feed per {name}...")
    try:
        rai_parser = RaiParser(url, ".")
        rai_parser.process()
        original_file = f"{name}.xml"
        if not os.path.exists(original_file):
            print(f"Errore: Il file {original_file} non è stato generato correttamente!")
            continue
        new_file = f"feed_{name}.xml"
        os.rename(original_file, new_file)
        print(f"Feed XML salvato correttamente: {new_file}")
    except Exception as e:
        print(f"Errore generico per {name}: {e}")
