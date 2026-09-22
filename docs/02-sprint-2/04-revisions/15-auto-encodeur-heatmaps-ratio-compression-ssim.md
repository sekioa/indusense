# Auto-encodeur : ratio de compression, heatmaps, AUROC pixel, SSIM, objet vs texture, PatchCore

## Définition et objectif

Cette fiche complète [la fiche TensorFlow vs PyTorch, CPU vs GPU](11-autoencodeur-anomalies-tensorflow-pytorch-cpu-gpu.md)
avec les notions propres au TP « B6 partie 2 — partie modèle »
(consigne : `docs/02-sprint-2/05-consignes/b6_deep_learning_auto_encodeur.md`) : le **ratio de
compression** du goulot d'étranglement, les **heatmaps de reconstruction** (localisation pixel du
défaut), l'**AUROC pixel** (par opposition à l'AUROC image), la perte **SSIM** comme alternative à la
MSE, l'effet **objet vs texture** sur un auto-encodeur par reconstruction, une confrontation mesurée
à **PatchCore** (bibliothèque `anomalib`), et la traduction d'une **décision métier** (maximiser le
rappel) en un choix de modèle et de seuil. Notebooks associés :
[`tp_deep_learning.ipynb`](../../../notebooks/02-sprint-2/02-deep-learning-donnees/tp_deep_learning.ipynb),
[`03-choix-final-detection-maximale-wood.ipynb`](../../../notebooks/02-sprint-2/02-deep-learning-donnees/03-choix-final-detection-maximale-wood.ipynb).

## Notions essentielles

- **Ratio de compression** = (valeurs en entrée) ÷ (valeurs dans le goulot d'étranglement). S'il est
  **proche de 1 ou inférieur** (goulot aussi grand, voire plus grand, que l'entrée), le modèle peut
  apprendre une **quasi-identité** : il reconstruit fidèlement à peu près n'importe quelle image, y
  compris des défauts jamais vus à l'entraînement — ce qui **détruit le signal d'anomalie**. C'est le
  piège central du TP.
- **Heatmap de reconstruction** : carte d'erreur **par pixel** (MSE moyennée sur les canaux couleur,
  pas moyennée sur toute l'image comme le score d'anomalie). Elle localise *où* le modèle échoue à
  reconstruire, à comparer visuellement au masque de vérité terrain (jamais utilisé pour l'entraînement
  ni pour le seuil, uniquement pour l'évaluation).
- **AUROC image vs AUROC pixel** : deux questions différentes. L'AUROC **image** évalue si le modèle
  classe correctement des *images entières* (sain vs défaut) à partir d'un score scalaire. L'AUROC
  **pixel** évalue si la heatmap désigne les *bons pixels* comme anormaux, en comparant chaque pixel de
  chaque image de test à son masque de vérité terrain (mask à zéro partout pour une image saine). Un bon
  AUROC image n'implique pas un bon AUROC pixel : un modèle peut savoir qu'une image contient un défaut
  sans bien savoir où.
- **Perte SSIM (Structural Similarity)** : alternative à la MSE, comparée par fenêtre glissante
  gaussienne (luminance, contraste, structure locale) plutôt que pixel à pixel. Plus sensible aux
  altérations de **texture/structure** ; utilisée ici comme perte d'entraînement (`1 - SSIM`), le score
  d'anomalie final restant la MSE pour rester comparable entre modèles.
- **MLflow pour un entraînement Deep Learning** : mêmes briques que pour le Machine Learning classique
  (`mlflow.log_params`, `mlflow.log_metric(..., step=epoch)` pour suivre une courbe époque par époque,
  `mlflow.log_figure` pour un artefact graphique) — un run par modèle entraîné.
- **Hypothèse implicite de l'auto-encodeur par reconstruction** : une erreur de reconstruction élevée
  signale un défaut. Cette hypothèse suppose que les seules sources de variation notable entre images
  saines sont les défauts eux-mêmes. Elle tient sur une **texture homogène** (`wood`) et peut **casser
  totalement** sur un **objet réfléchissant** (`metal_nut`), où l'éclairage et les reflets spéculaires
  varient d'une image saine à l'autre plus que certains défauts eux-mêmes.
- **PatchCore** (Roth et al., 2022, bibliothèque `anomalib`) : n'entraîne aucun réseau par
  rétropropagation. Il extrait des *features* d'un réseau **pré-entraîné sur ImageNet** sur les images
  saines, les stocke dans une **mémoire de patchs** (sous-échantillonnée par *coreset*), puis score
  chaque patch de test par sa distance au plus proche voisin dans cette mémoire. Ne compare jamais deux
  images pixel à pixel : robuste aux variations photométriques qui font échouer un auto-encodeur par
  reconstruction.

## Démarche

1. Construire l'auto-encodeur (3 conv + 3 déconv, sortie `Sigmoid`), afficher son résumé et calculer le
   ratio de compression **avant** tout entraînement — un ratio défavorable prévient d'un problème futur.
2. Entraîner avec perte MSE, cible = entrée, en suivant **train et validation** (pas seulement le train)
   pour détecter un éventuel sur-apprentissage ; logger dans MLflow.
3. Calibrer un seuil sur la validation saine (percentile ou `moyenne + k·écart-type`).
4. Calculer les heatmaps par pixel sur des défauts réels, les comparer aux masques de vérité terrain.
5. Évaluer : AUROC image, AUROC pixel, matrice de confusion au seuil retenu.
6. Comparer à des variantes (goulot resserré, perte SSIM, catégorie objet plutôt que texture, PatchCore)
   pour tester empiriquement les pistes d'amélioration de la consigne, plutôt que de les affirmer sans
   les mesurer.

## Exemple concret : catégorie `wood`, 3 modèles comparés

| Modèle | Paramètres | Ratio compression | AUROC image | AUROC pixel | Rappel @ seuil (99ᵉ centile) |
|---|---:|---:|---:|---:|---:|
| Référence (MSE, `base_channels=64`) | 741 379 | 0,75 | 0,9158 | 0,6375 | 0,217 |
| Goulot resserré (MSE, `base_channels=16`) | 47 107 | 3,00 | 0,9202 | 0,6544 | 0,100 |
| Perte SSIM (`base_channels=64`) | 741 379 | 0,75 | 0,8579 | 0,7651 | 0,200 |

Le modèle de référence a un ratio de compression de **0,75** (< 1 : le goulot `32×32×256` contient
262 144 valeurs, *plus* que les 196 608 valeurs de l'image d'entrée `256×256×3`) — le piège annoncé par
la consigne, vérifié numériquement avant même d'entraîner quoi que ce soit.

**Goulot resserré** (`base_channels` réduit de 64 à 16, ratio porté à 3,0, une vraie compression 3:1) :
contrairement à l'intuition qu'un goulot plus large favoriserait la quasi-identité, forcer une vraie
compression **améliore légèrement** le classement (AUROC image et pixel tous deux en hausse), avec
15,7x moins de paramètres. Le rappel au seuil choisi baisse en revanche (0,100 contre 0,217) : la
validation, reconstruite avec moins de fidélité, produit une distribution d'erreur différente qui
déplace le seuil du 99ᵉ centile — un effet de **politique de seuil**, pas une perte de capacité de
détection (le classement, lui, s'améliore).

**Perte SSIM** : compromis net. L'AUROC **image** se dégrade (0,8579 contre 0,9158) mais l'AUROC
**pixel** devient le meilleur des trois (0,7651 contre 0,6375) : la perte SSIM, plus sensible aux
ruptures de structure locale, pousse le modèle à mieux localiser l'altération, au prix d'un score par
image moins discriminant (toujours calculé en MSE, pour rester comparable entre les 3 modèles).
Illustration concrète : SSIM aide la **localisation**, pas nécessairement la **détection** globale.

Sur les heatmaps du modèle de référence : les défauts nets et localisés (`hole`) produisent un point
chaud net et bien positionné par rapport au masque ; les défauts diffus (`liquid`, déjà le plus discret
dans toutes les exécutions précédentes de ce projet) sont presque aussi bien reconstruits que les images
saines — la heatmap reste un bruit diffus, sans hotspot net — ce qui explique l'essentiel de l'écart
entre AUROC image (bon) et AUROC pixel (faible).

## Objet vs texture, et confrontation à PatchCore

| Modèle | AUROC image | AUROC pixel | Rappel @ seuil |
|---|---:|---:|---:|
| Auto-encodeur (MSE, `wood` — texture) | 0,9158 | 0,6375 | 0,217 |
| Auto-encodeur (MSE, `metal_nut` — objet) | **0,2556** | 0,7175 | 0,011 |
| PatchCore (`wide_resnet50_2`, `wood`) | 0,9860 | 0,9304 | 1,000 |
| PatchCore (`wide_resnet50_2`, `metal_nut`) | 0,9985 | 0,9866 | 0,989 |

**L'auto-encodeur échoue totalement sur `metal_nut`** : AUROC image = 0,2556, **inférieur à 0,5** (le
hasard) — le score de reconstruction classe en moyenne les images **saines** comme plus suspectes que
les défauts. Les heatmaps expliquent pourquoi : `metal_nut` est un objet métallique réfléchissant, dont
les contours et le pourtour du trou central produisent des reflets spéculaires à haute fréquence,
présents sur **toutes** les images (saines ou non). La heatmap se concentre sur ces contours brillants,
pas sur la zone du défaut (ex. `bent` : le pan tordu de l'écrou est lissé et reconstruit comme normal).
Cette variation photométrique, sans rapport avec un défaut, peut produire une erreur de reconstruction
plus grande que celle causée par le défaut lui-même — d'où un classement pire que le hasard. `wood`, une
texture mate sans reflet, ne souffre pas de ce problème.

**PatchCore résout ce problème précis** : passant de 0,9860 (`wood`) à 0,9985 (`metal_nut`) — quasiment
insensible au changement de catégorie qui fait s'effondrer l'auto-encodeur. La raison tient à sa
méthode : il compare des *features* d'un réseau pré-entraîné (déjà robuste aux variations
photométriques naturelles) par plus proche voisin dans une mémoire de patchs saines, jamais une image
entière pixel à pixel. Un reflet spéculaire inhabituel mais déjà rencontré quelque part dans les images
d'entraînement ne perturbe donc pas le score, contrairement à la MSE globale de l'auto-encodeur.

**Nuance sur le rappel** : PatchCore obtient un rappel de 1,000 sur `wood` mais une précision de 0,882
(quelques fausses alertes) — profil inverse de l'auto-encodeur (toujours précision = 1,00 dans ce
projet, rappel plus faible). Les scores de plus proche voisin n'ont pas la même distribution que les
erreurs de reconstruction : un seuil au même centile ne place donc pas les deux méthodes au même point
du compromis précision/rappel.

**Remarque orale (non quantifiée dans ce dépôt)** : la formatrice signale, sans le chiffrer, que
l'auto-encodeur par reconstruction se comporte différemment selon le **type de défaut**, y compris au
sein d'une même catégorie — sur `wood`, trous et rayures seraient mieux détectés que les taches de
couleur (déjà présentes comme variation naturelle dans les échantillons sains) ; sur `metal_nut`, un
défaut de déformation serait plus visible qu'un scratch. Piste à vérifier par une évaluation par
sous-type de défaut si le temps le permet, plutôt qu'à tenir pour acquis.

## Traduire une décision métier en choix de seuil (maximiser le rappel)

Décision métier testée : *« mieux vaut provoquer trop d'inspections que de laisser passer trop de
défauts »* — le rappel prime explicitement sur la précision. Démarche : balayer un grand nombre de
politiques de seuil (percentiles bas à hauts, `moyenne + k·écart-type`), **calibrées uniquement sur la
validation saine**, pour l'auto-encodeur et pour PatchCore ; retenir, par une règle **fixée avant de
lire les résultats de test**, la politique qui maximise le rappel puis minimise le taux de fausses
alertes en cas d'égalité — jamais en cherchant après coup la meilleure ligne du tableau de résultats
(biais déjà signalé dans `02e`).

| Modèle | Politique retenue | Fausses alertes (validation) | Précision (test) | Rappel (test) |
|---|---|---:|---:|---:|
| Auto-encodeur | percentile 50 (la plus permissive testée) | 51,4 % | 0,98 | **0,817** |
| PatchCore | percentile 99 | 2,7 % | 0,882 | **1,000** |

**Résultat clé : l'auto-encodeur plafonne à un rappel de 0,817, quel que soit le seuil.** Même au seuil
le plus permissif testé (la moitié des pièces saines de validation dépassent déjà ce seuil), 11 défauts
sur 60 restent non détectés — les erreurs de reconstruction des défauts les plus discrets (`liquid`)
sont **structurellement** trop proches de celles des images saines pour qu'un seuil, quel qu'il soit,
les sépare. C'est une limite du **score** lui-même (donc du modèle), pas de la politique de seuil : au
contraire de la limite de seuil des fiches précédentes (trop conservateur, mais contournable en
choisissant une politique plus permissive), celle-ci ne se contourne pas en changeant seulement le
seuil. PatchCore, dont le score sépare beaucoup mieux saines et défauts, atteint un rappel de 1,000 sur
la quasi-totalité des politiques testées, à un coût de fausses alertes bien moindre.

## Erreurs fréquentes et bonnes pratiques

- Ne pas calculer le ratio de compression avant d'entraîner : le diagnostic (goulot trop large) est
  disponible **avant** tout entraînement, pas besoin d'attendre des résultats de détection décevants.
- Confondre AUROC image et AUROC pixel : un modèle peut avoir un excellent AUROC image et un AUROC pixel
  proche du hasard — deux tâches différentes (détection vs localisation), deux métriques différentes.
- Juger la qualité de la détection uniquement sur les heatmaps affichées (2-3 exemples) sans les
  quantifier par un AUROC pixel sur l'ensemble du test : le visuel peut être trompeur sur un échantillon
  favorable choisi au hasard.
- Croire qu'un goulot plus resserré dégrade nécessairement la détection : ici, il l'améliore légèrement
  (mais peut la dégrader dans un autre contexte — un goulot trop étroit finit par ne plus reconstruire
  correctement même les images saines).
- Comparer deux modèles entraînés avec des pertes différentes (MSE vs SSIM) en gardant le score
  d'anomalie cohérent (ici, toujours la MSE) : sinon, la comparaison mélange l'effet de la perte
  d'entraînement et l'effet du score d'évaluation.
- Affirmer une amélioration ou une comparaison sans disposer des données ou de la bibliothèque
  nécessaires : mieux vaut documenter explicitement la limite que fabriquer un résultat non mesuré (ici,
  la comparaison objet vs texture et la confrontation à PatchCore ont ensuite été réalisées dès que les
  données et la bibliothèque ont été disponibles).
- Juger la qualité d'un auto-encodeur par reconstruction sur une seule catégorie : un AUROC correct sur
  une texture (`wood`) ne dit rien de son comportement sur un objet réfléchissant (`metal_nut`), où il
  peut devenir pire que le hasard.
- Comparer deux méthodes de score (reconstruction MSE, distance de plus proche voisin) au même seuil en
  *centile* en supposant qu'elles seront au même point du compromis précision/rappel : leurs
  distributions de score n'ont aucune raison de se ressembler.
- Choisir un seuil en cherchant, après coup, la politique qui obtient le meilleur résultat sur le test :
  la règle de sélection doit être fixée **avant** de lire les métriques de test, sous peine de
  sur-ajuster la décision à un petit échantillon.
- Croire qu'un rappel insuffisant se corrige toujours en abaissant le seuil : si les défauts les plus
  discrets ont un score aussi bas que les images saines, aucun seuil ne les distingue — le problème est
  dans le score (donc le modèle), pas dans la politique de décision.

## Points à retenir pour le QCM

- Le ratio de compression se calcule `valeurs_entrée / valeurs_latent` ; un ratio ≤ 1 signale un risque
  de quasi-identité (le goulot n'est pas un vrai goulot).
- L'AUROC pixel utilise les masques de vérité terrain (jamais l'entraînement) ; l'AUROC image utilise un
  score scalaire par image.
- La heatmap de reconstruction est une carte d'erreur par pixel, pas une valeur unique par image.
- La perte SSIM compare luminance/contraste/structure locale par fenêtre glissante, pas simplement la
  différence de valeur de chaque pixel comme la MSE.
- Un goulot plus resserré (moins de canaux) réduit le nombre de paramètres au carré du facteur de
  réduction des canaux, mais son effet sur la qualité de détection n'est pas prévisible a priori — il
  se mesure.
- Un AUROC image inférieur à 0,5 signifie que le score est **anti-corrélé** avec le label (les images
  saines obtiennent un score plus élevé que les défauts en moyenne), pas simplement « mauvais ».
- PatchCore n'entraîne aucun poids par rétropropagation : il construit une mémoire de features
  pré-entraînées (coreset) et score par distance au plus proche voisin.
- Un rappel qui plafonne quel que soit le seuil signale une limite du score (le modèle ne sépare pas
  assez bien saines et défauts), distincte d'un seuil mal calibré (qui se corrige en changeant de
  politique).

## Points à savoir expliquer lors de la soutenance

- Pourquoi calculer le ratio de compression *avant* d'entraîner est un diagnostic utile.
- Pourquoi un bon AUROC image ne garantit pas un bon AUROC pixel, avec un exemple concret (`hole` vs
  `liquid`).
- Pourquoi la perte SSIM a dégradé l'AUROC image mais amélioré l'AUROC pixel ici, et ce que cela dit sur
  le choix d'une perte selon l'objectif (détecter vs localiser).
- Pourquoi resserrer le goulot d'étranglement a légèrement amélioré le classement tout en réduisant le
  rappel au seuil retenu — et pourquoi ce n'est pas contradictoire.
- Pourquoi l'auto-encodeur obtient un AUROC image inférieur à 0,5 sur `metal_nut`, et pourquoi ce n'est
  pas juste « un mauvais résultat » mais une inversion du signal (les saines jugées plus suspectes).
  Pourquoi les reflets spéculaires d'un objet métallique cassent l'hypothèse centrale de l'auto-encodeur
  par reconstruction, alors qu'une texture mate (`wood`) n'en souffre pas.
- Pourquoi PatchCore reste performant sur `metal_nut` là où l'auto-encodeur échoue : quel principe
  méthodologique (comparaison locale par plus proche voisin sur des features pré-entraînées, plutôt que
  reconstruction globale pixel à pixel) explique cette robustesse.
- Pourquoi l'auto-encodeur ne peut pas dépasser un rappel de 0,817 sur `wood`, quel que soit le seuil
  choisi — et pourquoi ce n'est pas un problème de politique de seuil mais de score.
- Comment une décision métier (« maximiser le rappel ») se traduit en une règle de choix de seuil fixée
  *avant* de regarder le test, et pourquoi choisir après coup la meilleure ligne d'un tableau de
  résultats serait une erreur méthodologique.

## Sources du cours

- [Transcription du cours auto-encodeurs du 22/09](../02-transcriptions/11-jour-4-cours-auto-encodeurs.txt) (session de questions-réponses en présentiel, sans support de slides déposé).

---

⬅️ Voir aussi : [Auto-encodeur — TensorFlow vs PyTorch, CPU vs GPU](11-autoencodeur-anomalies-tensorflow-pytorch-cpu-gpu.md).
