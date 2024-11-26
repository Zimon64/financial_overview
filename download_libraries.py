import subprocess
import sys
import importlib


def install_library(library):
    try:
        importlib.import_module(library)
        print(f"{library} ist bereits installiert.")
    except ImportError:
        print(f"{library} wird installiert...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", library])
            print(f"{library} wurde erfolgreich installiert.")
        except subprocess.CalledProcessError:
            print(f"Fehler beim Installieren von {library}. Bitte prüfe die Bibliothek.")


def install_libraries(libraries):
    for library in libraries:
        install_library(library)


if __name__ == "__main__":
    required_libraries = [
        "PyQt6"
    ]

    install_libraries(required_libraries)
