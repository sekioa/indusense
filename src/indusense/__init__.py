"""Paquet racine du projet Indusense."""

__all__ = ["main"]


def __getattr__(name: str):
    # Import paresseux : les sous-modules comme `indusense.vision` ne doivent pas
    # exiger les dépendances de la CLI (SQLAlchemy, etc.), absentes des environnements
    # Deep Learning dédiés (`.venv-py313`, `.venv-py312-rocm`).
    if name == "main":
        from indusense.cli import main

        return main
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
