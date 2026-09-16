# Exécution des entraînements : CPU et GPU

## Définition et objectif

Le **CPU** est le processeur généraliste de l'ordinateur. Le **GPU** est un processeur conçu pour effectuer beaucoup de calculs semblables en parallèle. Un entraînement de modèle s'exécute sur l'un ou l'autre selon la bibliothèque employée et sa configuration, pas automatiquement selon le matériel installé.

## Cas Indusense B5

Le notebook `01-maintenance-ml-regression.ipynb` utilise `scikit-learn` et une `LogisticRegression`. Dans sa configuration actuelle, l'entraînement s'exécute sur le CPU ; aucun import CUDA/GPU ni choix de périphérique n'est présent.

## À retenir

- Les modèles classiques de scikit-learn sont normalement entraînés sur CPU.
- Un GPU est surtout pertinent pour des réseaux de neurones ou de très grands volumes de calcul matriciel, avec une bibliothèque et des pilotes compatibles, par exemple PyTorch ou TensorFlow configurés pour CUDA.
- Un GPU disponible ne rend pas un notebook plus rapide par lui-même : le code doit explicitement le prendre en charge.

## Points examen

À l'oral, justifier le choix de l'environnement d'entraînement par la taille des données, le type de modèle, le temps de calcul, le coût et la reproductibilité. Pour le baseline B5, le CPU est cohérent avec une régression logistique sur des données tabulaires.
