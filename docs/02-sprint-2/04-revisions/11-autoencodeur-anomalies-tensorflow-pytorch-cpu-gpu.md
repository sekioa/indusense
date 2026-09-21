# Auto-encodeur de détection d'anomalies : TensorFlow vs PyTorch, CPU vs GPU

## Définition et objectif

Un **auto-encodeur convolutif** apprend à reconstruire des images en passant par un goulot
d'étranglement (une représentation compressée). Entraîné **uniquement sur des images saines**, il
reconstruit mal ce qu'il n'a jamais vu : l'**erreur de reconstruction** (MSE entre image et
reconstruction) sert de **score d'anomalie**. Voir aussi
[la fiche sur la préparation des données](10-preparation-donnees-images-mvtec-ad.md) pour la
préparation des données en amont.

L'objectif de cette fiche est double : documenter la méthode d'entraînement/évaluation d'un tel
modèle, et consigner une comparaison chiffrée entre deux frameworks (TensorFlow, PyTorch) et deux
types de matériel (CPU, GPU) sur un même problème.

## Notions essentielles

- **Score d'anomalie par reconstruction** : plus l'erreur de reconstruction d'une image est grande,
  plus elle est jugée suspecte. Ce score ne dépend d'aucun seuil : il permet de calculer un **ROC-AUC**
  et un **PR-AUC** (qualité du *classement*, indépendante de toute décision).
- **Seuil de décision** : transforme le score continu en décision binaire (sain/anormal). Calibré sur
  la **validation saine** (jamais vue à l'entraînement), par exemple `moyenne + k écarts-types` des
  erreurs de validation. **Un excellent ROC-AUC/PR-AUC n'implique pas une bonne précision/rappel** au
  seuil choisi : ce sont deux évaluations différentes (classement vs décision).
- **Première époque vs vitesse de croisière** : la première époque d'entraînement inclut un coût
  d'initialisation (trace du graphe `tf.function` côté Keras, compilation/mise en cache des noyaux de
  calcul GPU côté PyTorch+ROCm) qui n'existe plus ensuite. Comparer des temps d'entraînement sans
  isoler ce coût fausse la mesure, surtout sur peu d'époques.
- **Comparaison équitable entre frameworks** : exige une architecture strictement identique — se
  vérifie simplement en comparant le nombre de paramètres entraînables (identique ⇒ même architecture).

## Démarche

1. Construire la même architecture dans chaque framework (mêmes couches, canaux, strides) et vérifier
   l'égalité du nombre de paramètres entraînables.
2. Entraîner sur les saines d'entraînement augmentées (une version augmentée différente régénérée à
   chaque époque), mesurer séparément le temps de la première époque et la vitesse de croisière.
3. Calibrer le seuil sur la validation saine.
4. Évaluer sur le test (saines + défauts) : ROC-AUC, PR-AUC (indépendants du seuil), puis
   précision/rappel/F1/FP/FN **au seuil choisi**.
5. Comparer les executions (framework, device) sur le temps et sur la qualité, séparément.

## Exemple concret : catégorie `wood`, 60 époques, 741 379 paramètres

Notebooks : [`02a` (TensorFlow CPU)](../../../notebooks/02-sprint-2/02-deep-learning-donnees/02a-autoencoder-tensorflow-cpu.ipynb), [`02b` (PyTorch CPU)](../../../notebooks/02-sprint-2/02-deep-learning-donnees/02b-autoencoder-pytorch-cpu.ipynb), [`02c` (PyTorch GPU)](../../../notebooks/02-sprint-2/02-deep-learning-donnees/02c-autoencoder-pytorch-gpu.ipynb), [`02d` (comparaison)](../../../notebooks/02-sprint-2/02-deep-learning-donnees/02d-comparaison-frameworks-devices.ipynb). Modules réutilisables : [`autoencoder_torch.py`](../../../src/indusense/vision/autoencoder_torch.py), [`autoencoder_keras.py`](../../../src/indusense/vision/autoencoder_keras.py), [`anomaly.py`](../../../src/indusense/vision/anomaly.py).

Architecture : encodeur `Conv 3×3 stride 2` ×3 (canaux `3→64→128→256`), goulot `32×32×256`, décodeur
symétrique par `ConvTranspose`, sortie `Sigmoid`. Images `256×256×3`, lot de 32, 60 époques, Adam
(`lr=1e-3`), perte MSE.

### Temps d'entraînement mesuré

| Exécution | Paramètres | 1ère époque (s) | Croisière (ms/époque) | Temps total (s) |
|---|---:|---:|---:|---:|
| TensorFlow — CPU | 741 379 | 3,039 | 2 267,8 | 136,84 |
| PyTorch — CPU | 741 379 | 3,779 | 3 601,1 | 216,24 |
| PyTorch — GPU (AMD RX 9070 XT, ROCm 7.2.1) | 741 379 | 1,373 | 771,3 | 46,88 |

**PyTorch GPU vs CPU** (comparaison demandée) : **4,67x plus rapide** en régime de croisière, mais
seulement **2,75x** sur la première époque à cause du coût d'initialisation ROCm (compilation/mise en
cache des noyaux HIP), payé une seule fois. **Pour un modèle beaucoup plus petit, ce même GPU peut être
plus lent que le CPU** (vérifié séparément par un micro-benchmark : ratio CPU/GPU de 0,14x avant
mise en cache des noyaux, contre 2,4x à 5,7x en régime de croisière selon la taille du modèle) : le gain
GPU croît avec la taille du modèle/des lots et n'est jamais acquis d'avance.

Point secondaire : TensorFlow CPU s'est révélé ici **1,59x plus rapide que PyTorch CPU** sur cette
machine (optimisations oneDNN/AVX-512 signalées en console) — une différence d'implémentation CPU entre
frameworks, sans lien avec l'accélération matérielle.

### Qualité de détection mesurée

| Exécution | Seuil | ROC-AUC | PR-AUC | Précision | Rappel | F1 | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| TensorFlow — CPU | 0,00138 | 0,9825 | 0,9948 | 1,00 | 0,117 | 0,209 | 0 | 53 |
| PyTorch — CPU | 0,00106 | 0,9561 | 0,9861 | 1,00 | 0,100 | 0,182 | 0 | 54 |
| PyTorch — GPU | 0,00101 | 0,9632 | 0,9884 | 1,00 | 0,117 | 0,209 | 0 | 53 |

Le GPU n'a dégradé ni le classement ni la détection (résultats identiques ou légèrement meilleurs qu'en
CPU) : les petits écarts entre CPU et GPU proviennent des implémentations numériques différentes des
noyaux de convolution selon le device, pas d'une perte de qualité liée à la vitesse.

**Limite commune aux trois exécutions** : un ROC-AUC/PR-AUC élevé partout (> 0,95 / > 0,98) masque un
rappel très faible (10 à 12 %) au seuil `moyenne + 3 écarts-types`, trop conservateur pour cette
catégorie. Le classement des scores est excellent ; la règle de décision, elle, méritait d'être
retravaillée — voir la comparaison de politiques de seuil ci-dessous.

### Effet de la résolution d'image (GPU, expérience complémentaire)

Notebook : [`02c-...-512px`](../../../notebooks/02-sprint-2/02-deep-learning-donnees/02c-autoencoder-pytorch-gpu-512px.ipynb).
Même architecture et hyperparamètres, résolution portée de `256×256` à `512×512` (goulot
`64×64×256` au lieu de `32×32×256`).

| Résolution | 1ère époque (s) | Croisière (ms/époque) | Total (s) | ROC-AUC | PR-AUC |
|---|---:|---:|---:|---:|---:|
| 256×256 | 1,373 | 771,3 | 46,88 | 0,9632 | 0,9884 |
| 512×512 | 71,874 | 3 166,9 | 258,72 | 0,9482 | 0,9835 |

La vitesse de croisière suit le facteur ~4 attendu (4 fois plus de pixels), mais la **première époque**
explose (facteur 52, pas 4) : la bibliothèque de noyaux ROCm (MIOpen) effectue une recherche du meilleur
algorithme de convolution la première fois qu'elle rencontre une **forme de tenseur inédite** — un coût
d'auto-tuning ponctuel qui dépend de la forme des données, pas seulement du volume de calcul. Aucun gain
de qualité de détection observé : `256×256` offre ici un bien meilleur rapport temps/qualité.

### Comparer des politiques de seuil (GPU, même modèle)

Notebook : [`02e`](../../../notebooks/02-sprint-2/02-deep-learning-donnees/02e-autoencoder-pytorch-gpu-seuils.ipynb).
Reprend l'entraînement GPU `256×256` de `02c` (mêmes poids, ROC-AUC/PR-AUC identiques) et compare 7
politiques de seuil, toutes calibrées uniquement sur la validation saine (37 images) :

| Politique | Fausses alertes attendues (validation) | Rappel réel (test) |
|---|---:|---:|
| moyenne + 1σ | 24,3 % | **0,35** |
| moyenne + 2σ | 2,7 % | 0,18 |
| moyenne + 3σ | 0,0 % | 0,12 |
| percentile 90 | 10,8 % | 0,25 |
| percentile 95 | 5,4 % | 0,20 |
| percentile 97 / 99 | 5,4 % / 2,7 % | 0,18 |

Résultat notable : **la précision reste à 1,00 pour les 7 politiques** — sur le test réel (19 images
saines), aucune n'a jamais produit de fausse alerte, y compris la plus permissive. Le taux de fausses
alertes estimé sur 37 images de validation ne s'est donc pas confirmé sur les 19 images de test : un
effet d'échantillonnage sur des petits jeux de données, pas une propriété du modèle. Dans ce cas précis
(aucun compromis précision/rappel observé), retenir la politique au meilleur rappel (`moyenne + 1σ`,
rappel 0,35 contre 0,12 pour `moyenne + 3σ`) ne sacrifie rien de mesurable — mais ce choix resterait à
reconfirmer sur un test plus large avant tout déploiement réel.

## Erreurs fréquentes et bonnes pratiques

- Comparer des temps d'entraînement sans isoler la première époque : surestime ou sous-estime l'écart
  selon le nombre total d'époques mesurées.
- Juger la qualité d'un détecteur d'anomalies uniquement sur ROC-AUC/PR-AUC : ces métriques ignorent le
  seuil réellement appliqué en production.
- Conclure qu'un GPU est toujours plus rapide qu'un CPU : dépend de la taille du modèle, des lots, et du
  coût d'initialisation à amortir.
- Comparer deux frameworks sans vérifier l'égalité du nombre de paramètres entraînables : une
  architecture subtilement différente invaliderait toute la comparaison de vitesse.
- Espérer une trajectoire de perte identique entre frameworks à seed fixée : les initialisations par
  défaut diffèrent (Glorot/Xavier chez Keras, Kaiming chez PyTorch), donc la convergence aussi.
- Extrapoler linéairement le coût GPU d'un changement de résolution : le calcul de croisière suit le
  volume de pixels, mais le coût de la première occurrence d'une nouvelle forme de tenseur (auto-tuning
  ROCm/MIOpen) peut être bien plus élevé que ce facteur.
- Faire confiance à un taux de fausses alertes estimé sur une très petite validation (ici 37 images) :
  il peut ne pas se retrouver sur un test tout aussi petit — les deux ne sont que des estimations
  bruitées d'un taux rare.

## Points à retenir pour le QCM

- Le score d'anomalie (erreur de reconstruction) et le seuil de décision sont deux étapes distinctes.
- ROC-AUC et PR-AUC ne dépendent pas du seuil ; précision, rappel et F1 en dépendent entièrement.
- La première époque d'un entraînement GPU inclut un coût d'initialisation non représentatif de la
  vitesse de croisière.
- L'avantage du GPU sur le CPU croît avec la taille du modèle et des lots ; il peut s'inverser sur un
  modèle très petit.
- Une architecture équivalente entre deux frameworks se vérifie par un nombre de paramètres identique.
- Un percentile de validation et une règle `moyenne + n écarts-types` sont deux façons de calibrer un
  seuil ; le percentile ne suppose pas une distribution gaussienne des erreurs.
- Le coût de la première occurrence d'une forme de tenseur inédite sur GPU (auto-tuning des noyaux)
  n'est pas proportionnel au volume de calcul.

## Points à savoir expliquer lors de la soutenance

- Pourquoi le seuil de calibration utilise uniquement des images saines de validation.
- Pourquoi isoler la première époque est nécessaire pour comparer des temps d'entraînement CPU/GPU.
- Pourquoi un excellent ROC-AUC/PR-AUC peut coexister avec un rappel très faible, et ce que cela implique
  pour le choix opérationnel du seuil.
- Pourquoi le gain mesuré du GPU (facteur ~4,7x ici) n'est pas une constante universelle.
- Comment vérifier qu'une comparaison entre deux implémentations d'un même modèle est équitable.
- Pourquoi un taux de fausses alertes mesuré sur une petite validation peut ne pas se reproduire sur un
  test tout aussi petit, et ce que cela implique pour la confiance à accorder au choix d'un seuil.
- Pourquoi doubler la résolution d'image ne double pas simplement le temps d'entraînement GPU.
