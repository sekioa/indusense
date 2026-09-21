# Exécution des entraînements : CPU et GPU

## Définition et objectif

Le **CPU** est le processeur généraliste de l'ordinateur. Le **GPU** est un processeur conçu pour effectuer beaucoup de calculs semblables en parallèle. Un entraînement de modèle s'exécute sur l'un ou l'autre selon la bibliothèque employée et sa configuration, pas automatiquement selon le matériel installé.

## Cas Indusense B5

Le notebook `01-maintenance-ml-regression.ipynb` utilise `scikit-learn` et une `LogisticRegression`. Dans sa configuration actuelle, l'entraînement s'exécute sur le CPU ; aucun import CUDA/GPU ni choix de périphérique n'est présent.

## À retenir

- Les modèles classiques de scikit-learn sont normalement entraînés sur CPU.
- Un GPU est surtout pertinent pour des réseaux de neurones ou de très grands volumes de calcul matriciel, avec une bibliothèque et des pilotes compatibles, par exemple PyTorch ou TensorFlow configurés pour CUDA.
- Un GPU disponible ne rend pas un notebook plus rapide par lui-même : le code doit explicitement le prendre en charge.

## Taille d'un modèle et mémoire d'exécution

La **taille sur disque** correspond au fichier de poids téléchargé. La **RAM** (mémoire vive du système) ou la **VRAM** (mémoire du GPU) nécessaire pendant l'**inférence**, c'est-à-dire l'utilisation d'un modèle déjà entraîné pour produire un résultat, est généralement plus élevée.

Exemple avec `faster-whisper` pour transcrire de l'audio :

- `base` occupe environ 148 Mo sur disque ;
- `small` occupe environ 486 Mo sur disque et constitue un bon compromis local pour le français ;
- `medium` occupe environ 1,53 Go sur disque, mais demande davantage de mémoire et de temps de calcul.

La **quantification** réduit la précision numérique des poids, par exemple de 32 bits à 8 bits (`int8`), afin de diminuer la mémoire consommée et souvent d'accélérer l'inférence sur CPU, avec un éventuel compromis sur la précision.

## Mise en pratique : transcription locale

Une installation locale reproductible de `faster-whisper` consiste à :

1. installer une version compatible de Python ;
2. créer un **environnement virtuel**, c'est-à-dire un dossier isolant les dépendances Python de l'outil ;
3. installer `faster-whisper` dans cet environnement ;
4. télécharger une fois le modèle retenu, par exemple `small` ;
5. exécuter l'inférence sur CPU avec la quantification `int8` ;
6. vérifier le résultat sur un fichier audio en contrôlant la création du texte et, si nécessaire, des sous-titres horodatés.

L'exécution locale évite d'envoyer l'enregistrement à un service de transcription tiers. Elle améliore donc la maîtrise de la confidentialité, mais laisse à l'utilisateur la responsabilité du stockage, des mises à jour et du temps de calcul.

## Points examen

À l'oral, justifier le choix de l'environnement d'entraînement par la taille des données, le type de modèle, le temps de calcul, le coût et la reproductibilité. Pour le baseline B5, le CPU est cohérent avec une régression logistique sur des données tabulaires.
