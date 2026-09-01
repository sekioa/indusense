# Point d'entrée d'un programme Python

## Définition et objectif

Le **point d'entrée** est l'endroit où commence l'exécution d'un programme. En Python, on regroupe souvent le comportement principal dans une fonction `main()`, puis on utilise une garde pour décider quand l'appeler.

```python
def main():
    print("Hello from indusense!")


if __name__ == "__main__":
    main()
```

## Déroulement de l'exécution

1. `def main():` définit la fonction sans encore l'exécuter.
2. Les quatre espaces devant `print(...)` indiquent que cette instruction appartient à la fonction. Python utilise l'indentation pour délimiter les blocs.
3. Python attribue une valeur à la variable spéciale `__name__`.
4. Lorsque le fichier est lancé directement, `__name__` vaut `"__main__"`.
5. La condition devient vraie et `main()` est appelée.

Le résultat visible attendu est :

```text
Hello from indusense!
```

## Exécution et vérification

Depuis le dossier `indusense` :

```powershell
uv run python main.py
```

`uv run` exécute la commande avec l'environnement Python du projet. `python main.py` demande à Python d'exécuter le fichier.

## Pourquoi utiliser cette garde ?

Si un autre fichier importe `main.py`, sa variable `__name__` contient le nom du module et non `"__main__"`. La fonction reste alors disponible sans être lancée automatiquement. Cela facilite la réutilisation et les tests.

## Erreurs fréquentes et bonnes pratiques

- `name` n'est pas équivalent à `__name__` : les doubles tirets bas font partie du nom spécial.
- `"main"` n'est pas équivalent à `"__main__"`.
- Une instruction non indentée après `def main():` provoque une erreur d'indentation.
- Définir `main()` sépare le comportement principal des définitions réutilisables.

## Points à retenir pour le QCM

- Définir une fonction ne l'exécute pas.
- `__name__` vaut `"__main__"` lorsqu'un fichier est exécuté directement.
- L'indentation délimite les blocs en Python.

## Points à savoir expliquer lors de la soutenance

- La différence entre exécuter directement un fichier et l'importer comme module.
- L'intérêt d'un point d'entrée explicite pour structurer et tester une application.

## Pour aller plus loin

- [Python — `__main__` et environnement d’exécution principal](https://docs.python.org/fr/3/library/__main__.html) : comportement de `__name__` lors de l’exécution et de l’import.
- [Python — Modules](https://docs.python.org/fr/3/tutorial/modules.html) : organiser et réutiliser du code Python.
