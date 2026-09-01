# Suivi de formation — 25 août 2026 — Matinée, partie 1

## Contexte

- Début de matinée consacré principalement à l’installation et à la mise en place des outils.
- Progression ralentie par les difficultés d’installation rencontrées par plusieurs participants peu familiers avec l’environnement technique.

## Déroulé

1. Présentation d’UV pour installer plusieurs versions de Python, gérer les environnements et les dépendances.
2. Mention d’autres outils ou approches : `pyenv`, Poetry, `requirements.txt` et `pip`.
3. Ouverture d’un terminal : PowerShell ou équivalent sous Windows, Terminal sous macOS ou Linux.
4. Présentation des premières commandes :

   ```text
   uv --version
   uv python list
   uv run python --version
   uv init <nom-du-projet>
   ```

5. Exemple d’initialisation donné par le formateur : `uv init indusense`.

## Travail réalisé de notre côté

- Utilisation de Codex Desktop comme assistant pédagogique et technique pour accompagner les installations, expliquer les commandes et conserver une trace structurée du travail.
- Initialisation de premiers projets Python avec UV, dont `indusense`.
- Création et utilisation de premiers notebooks JupyterLab dans l’interface ouverte dans le navigateur.
- Dans `exercices/premier-notebook/Untitled.ipynb`, sélection du kernel `formation-ia-premier-notebook` puis exécution d’une cellule affichant le chemin de l’interpréteur Python. Le résultat pointe bien vers le dossier `.venv` du projet.
- Ajout à ce projet de `numpy`, `pandas`, `matplotlib`, `scikit-learn` et `ipykernel` avec gestion des dépendances par UV.
- Création d’un second notebook dans le projet `indusense` ; il est encore vide et son exécution reste à réaliser.
- Première exploration de la structure d’un programme Python avec le fichier `indusense/main.py` et sa fonction `main()`.
- Constitution progressive de la documentation locale pour conserver les procédures et les notions rencontrées pendant la formation.

## État à la fin de cette première partie

- Les notions et commandes de base ont été présentées.
- La séquence a surtout porté sur l’installation et la préparation des environnements.
- Aucun exercice réalisé ni résultat technique commun à tous les participants n’est mentionné dans les notes disponibles.
- De notre côté, le premier environnement Jupyter est opérationnel et son interpréteur a été vérifié depuis un notebook.
- Le second notebook existe, mais il n’a pas encore été exécuté.
- La suite du déroulé reste à compléter.

## Source

Notes visuelles du formateur communiquées le 25 août 2026.
