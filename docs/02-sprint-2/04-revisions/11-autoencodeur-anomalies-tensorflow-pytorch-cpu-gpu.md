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
- **Reproductibilité selon le framework** : à seed fixée, **PyTorch (CPU et GPU) est bit-reproductible**
  d'une exécution à l'autre — poids, pertes et métriques de qualité identiques au chiffre près sur la
  même machine. **TensorFlow/Keras CPU ne l'est pas** dans ce projet : les opérations parallèles oneDNN
  qu'il utilise sur CPU ne sont pas déterministes à ce niveau de précision, donc deux exécutions du même
  notebook TensorFlow produisent des poids et des métriques légèrement différents, même code et même
  seed. Une comparaison chiffrée entre frameworks doit tenir compte de cette asymétrie.
- **Persistance du cache de noyaux GPU (MIOpen/ROCm)** : la recherche du meilleur algorithme de
  convolution pour une forme de tenseur inédite (nouvelle résolution, nouvelle taille de noyau) est mise
  en cache **sur disque**, pas seulement en mémoire du process. Le surcoût de première époque qu'elle
  cause n'apparaît donc qu'une seule fois **par forme et par machine** : ré-exécuter le même notebook
  plus tard, une fois la forme déjà rencontrée, ne reproduit pas ce surcoût.

## Démarche

1. Construire la même architecture dans chaque framework (mêmes couches, canaux, strides) et vérifier
   l'égalité du nombre de paramètres entraînables.
2. Entraîner sur les saines d'entraînement augmentées (une version augmentée différente régénérée à
   chaque époque), mesurer séparément le temps de la première époque et la vitesse de croisière.
3. Calibrer le seuil sur la validation saine.
4. Évaluer sur le test (saines + défauts) : ROC-AUC, PR-AUC (indépendants du seuil), puis
   précision/rappel/F1/FP/FN **au seuil choisi**.
5. Comparer les executions (framework, device) sur le temps et sur la qualité, séparément.
6. **Inspecter visuellement quelques détections au seuil retenu** (conseil de la formatrice) : afficher
   original + reconstruction pour quelques **vrais positifs** (défauts correctement détectés) et quelques
   **faux négatifs** (défauts classés à tort comme sains). Dans ce projet, les faux positifs sont toujours
   à 0 (précision = 1,00 partout) : ce sont donc les faux négatifs qui sont l'angle mort réellement
   instructif à visualiser, pas les faux positifs.

## Exemple concret : catégorie `wood`, 60 époques, 741 379 paramètres

Notebooks : [`02a` (TensorFlow CPU)](../../../notebooks/02-sprint-2/02-deep-learning-donnees/02a-autoencoder-tensorflow-cpu.ipynb), [`02b` (PyTorch CPU)](../../../notebooks/02-sprint-2/02-deep-learning-donnees/02b-autoencoder-pytorch-cpu.ipynb), [`02c` (PyTorch GPU)](../../../notebooks/02-sprint-2/02-deep-learning-donnees/02c-autoencoder-pytorch-gpu.ipynb), [`02d` (comparaison)](../../../notebooks/02-sprint-2/02-deep-learning-donnees/02d-comparaison-frameworks-devices.ipynb). Modules réutilisables : [`autoencoder_torch.py`](../../../src/indusense/vision/autoencoder_torch.py), [`autoencoder_keras.py`](../../../src/indusense/vision/autoencoder_keras.py), [`anomaly.py`](../../../src/indusense/vision/anomaly.py).

Architecture : encodeur `Conv 3×3 stride 2` ×3 (canaux `3→64→128→256`), goulot `32×32×256`, décodeur
symétrique par `ConvTranspose`, sortie `Sigmoid`. Images `256×256×3`, lot de 32, 60 époques, Adam
(`lr=1e-3`), perte MSE.

### Temps d'entraînement mesuré

| Exécution | Paramètres | 1ère époque (s) | Croisière (ms/époque) | Temps total (s) |
|---|---:|---:|---:|---:|
| TensorFlow — CPU | 741 379 | 3,03 | 2 390,1 | 144,05 |
| PyTorch — CPU | 741 379 | 3,80 | 3 512,5 | 211,04 |
| PyTorch — GPU (AMD RX 9070 XT, ROCm 7.2.1) | 741 379 | 1,38 | 786,4 | 47,78 |

**PyTorch GPU vs CPU** (comparaison demandée) : **4,47x plus rapide** en régime de croisière, mais
seulement **2,76x** sur la première époque à cause du coût d'initialisation ROCm (compilation/mise en
cache des noyaux HIP), payé une seule fois. **Pour un modèle beaucoup plus petit, ce même GPU peut être
plus lent que le CPU** (vérifié séparément par un micro-benchmark : ratio CPU/GPU de 0,14x avant
mise en cache des noyaux, contre 2,4x à 5,7x en régime de croisière selon la taille du modèle) : le gain
GPU croît avec la taille du modèle/des lots et n'est jamais acquis d'avance.

Point secondaire : TensorFlow CPU s'est révélé ici **1,47x plus rapide que PyTorch CPU** sur cette
machine (optimisations oneDNN/AVX-512 signalées en console) — une différence d'implémentation CPU entre
frameworks, sans lien avec l'accélération matérielle. Ces chiffres (comme toute la ligne TensorFlow)
varient légèrement d'une exécution à l'autre du même notebook — voir la remarque sur la reproductibilité
ci-dessus ; les deux lignes PyTorch, elles, sont stables au chiffre près.

### Qualité de détection mesurée

| Exécution | Seuil | ROC-AUC | PR-AUC | Précision | Rappel | F1 | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| TensorFlow — CPU | 0,00132 | 0,9605 | 0,9877 | 1,00 | 0,117 | 0,209 | 0 | 53 |
| PyTorch — CPU | 0,00106 | 0,9561 | 0,9861 | 1,00 | 0,100 | 0,182 | 0 | 54 |
| PyTorch — GPU | 0,00101 | 0,9632 | 0,9884 | 1,00 | 0,117 | 0,209 | 0 | 53 |

Le GPU n'a dégradé ni le classement ni la détection (résultats identiques ou légèrement meilleurs qu'en
CPU) : les petits écarts entre CPU et GPU proviennent des implémentations numériques différentes des
noyaux de convolution selon le device, pas d'une perte de qualité liée à la vitesse. La ligne TensorFlow
diffère en revanche sensiblement de sa propre mesure lors d'une exécution antérieure du même notebook
(ROC-AUC alors 0,9825, seuil alors 0,00138) — conséquence directe de sa non-reproductibilité sur CPU, pas
d'un changement de code ou de données.

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
| 256×256 | 1,38 | 786,4 | 47,78 | 0,9632 | 0,9884 |
| 512×512 | 3,97 | 3 219,6 | 193,92 | 0,9482 | 0,9835 |

Une fois la forme `512×512` déjà connue de MIOpen (voir la remarque sur la persistance du cache
ci-dessus), la vitesse de croisière **et** la première époque suivent toutes deux le facteur ~4 attendu
(4 fois plus de pixels) : respectivement 4,09x et 2,88x ici. **Lors de la toute première exécution de
cette forme sur cette machine**, la première époque avait explosé à **71,874 s** (facteur **52x**, pas
4x) : la bibliothèque de noyaux ROCm (MIOpen) avait dû rechercher le meilleur algorithme de convolution
pour cette **forme de tenseur inédite** — un coût d'auto-tuning ponctuel, mis en cache sur disque, qui ne
s'est donc plus reproduit aux exécutions suivantes. Aucun gain de qualité de détection observé (ROC-AUC
et PR-AUC identiques d'une exécution à l'autre, PyTorch étant bit-reproductible) : `256×256` offre ici un
bien meilleur rapport temps/qualité.

### Effet de la taille du noyau de convolution (GPU, expérience complémentaire)

Notebooks : [`02c-...-noyau5x5`](../../../notebooks/02-sprint-2/02-deep-learning-donnees/02c-autoencoder-pytorch-gpu-noyau5x5.ipynb),
[`02f` (comparaison)](../../../notebooks/02-sprint-2/02-deep-learning-donnees/02f-comparaison-noyaux-convolution.ipynb).
Même résolution (`256×256`), mêmes hyperparamètres et device que `02c`, seule la taille du noyau de
convolution change (`3×3` → `5×5`) ; padding et `output_padding` sont recalculés dans
`ConvAutoencoder` (paramètre `kernel_size`) pour conserver un goulot d'étranglement identique
`32×32×256`.

| Noyau | Paramètres | 1ère époque (s) | Croisière (ms/époque) | Total (s) | ROC-AUC | PR-AUC | Rappel (seuil `moy.+3σ`) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 3×3 | 741 379 | 1,38 | 786,4 | 47,78 | 0,9632 | 0,9884 | 0,117 |
| 5×5 | 2 058 243 | 1,85 | 1 171,7 | 70,98 | 0,9535 | 0,9858 | 0,033 |

Le nombre de paramètres suit exactement le ratio théorique des surfaces de noyau
(`(5×5)/(3×3) = 25/9 ≈ 2,78x`). La vitesse de croisière n'augmente en revanche que de **1,49x** — moins
que ce ratio théorique de calcul, signe que l'entraînement n'est pas purement limité par le volume de
calcul des convolutions à cette échelle. Une fois la forme `5×5` déjà connue de MIOpen, la **première
époque** suit ce même facteur (**1,34x**) ; **lors de la toute première exécution** de ce noyau sur cette
machine, elle avait explosé à **46,08 s** (facteur **33,6x**) — même cause que pour le passage à
`512×512` : MIOpen recherche le meilleur algorithme pour toute **forme de convolution inédite** avant de
la mettre en cache sur disque, un coût qui ne s'est donc pas reproduit à cette ré-exécution.

Aucun gain de qualité : classement légèrement inférieur, et rappel au seuil `moyenne + 3σ` qui chute
(0,033 contre 0,117). La cause n'est pas une perte de capacité à séparer sain/défaut — les ratios
erreur défaut / erreur saine sont quasi identiques entre les deux noyaux (ex. `scratch` : 2,37 vs
2,28) — mais une **validation saine proportionnellement plus dispersée** avec le noyau `5×5`
(`std/mean` = 0,411 contre 0,357) : le seuil `moyenne + 3σ`, calculé à partir de cet écart-type, est
poussé plus loin dans la distribution des erreurs et manque donc davantage de défauts. Autre indice
d'une convergence moins poussée à budget d'époques fixé : la perte MSE finale d'entraînement est plus
haute avec 2,78x plus de paramètres (0,00090 contre 0,00033) — plus de capacité n'implique pas une
perte plus basse si le nombre d'époques n'est pas ajusté en conséquence.

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
- Supposer qu'un noyau de convolution plus grand (donc plus de paramètres) améliore automatiquement la
  détection : à budget d'époques fixé, il peut au contraire moins bien converger et rendre le seuil
  `moyenne + n écarts-types` plus sensible à la dispersion de la validation.
- Chercher à illustrer des faux positifs quand ils sont toujours à 0 (précision = 1,00 partout ici) :
  l'angle mort réellement visible sur ce projet, ce sont les faux négatifs (défauts classés sains).
- Croire qu'une exécution TensorFlow/Keras CPU reproduira exactement les métriques d'une exécution
  précédente du même notebook : sur CPU, TensorFlow n'offre pas la même garantie de reproductibilité que
  PyTorch, même à seed, code et machine identiques.

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
- Un noyau de convolution plus grand augmente le nombre de paramètres proportionnellement au carré de
  sa taille (`(5×5)/(3×3) ≈ 2,78x`), mais pas nécessairement le temps de croisière dans la même
  proportion.
- PyTorch (CPU et GPU) est bit-reproductible à seed fixée ; TensorFlow/Keras CPU ne l'est pas dans ce
  projet (opérations parallèles oneDNN non déterministes).
- Le cache de noyaux GPU (MIOpen/ROCm) est persistant sur disque : le surcoût de première époque pour une
  forme de tenseur inédite ne se reproduit pas à la ré-exécution suivante du même notebook.

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
- Pourquoi un noyau de convolution plus grand (plus de paramètres) n'a pas amélioré la détection ici, et
  quel rôle joue la dispersion de la validation dans un seuil `moyenne + n écarts-types`.
- Pourquoi inspecter les faux négatifs (défauts classés sains) est plus instructif ici que d'inspecter les
  faux positifs, qui sont toujours nuls dans ce projet.
- Pourquoi une différence de résultat entre deux exécutions du même notebook TensorFlow ne remet pas en
  cause le code, alors que la même différence entre deux exécutions PyTorch le remettrait en cause.
