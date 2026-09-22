# Réseaux de neurones : MLP, CNN et transfer learning — fondations

## Définition et objectif

Cette fiche pose les **fondations théoriques** du Deep Learning mobilisées par le cours : perceptron multicouche (MLP), entraînement par descente de gradient et rétropropagation, régularisation, réseaux convolutifs (CNN) et transfer learning. Elle complète la [fiche généralités IA/ML/DL/LLM](01-generalites-ia-ml-dl-llm.md) (qui situe le Deep Learning dans l'ensemble IA) et prépare la lecture de la [fiche auto-encodeurs pour la détection d'anomalies](11-autoencodeur-anomalies-tensorflow-pytorch-cpu-gpu.md), qui applique une partie de ces notions (CNN, entraînement, seuils) sur les données InduSense.

Objectif : savoir dessiner et justifier une architecture MLP simple, expliquer comment un réseau apprend (fonction de coût, gradient, rétropropagation, optimiseur), reconnaître le rôle d'une convolution et d'un pooling dans un CNN, et savoir quand réutiliser un modèle pré-entraîné plutôt que d'en entraîner un de zéro.

## Notions essentielles

### Machine Learning vs Deep Learning

En Machine Learning classique, l'**extraction de features** (caractéristiques) est faite manuellement avant la classification. En Deep Learning, le réseau apprend simultanément l'extraction de features **et** la classification, directement à partir des données brutes (ex. les pixels d'une image).

### MLP (Multi Layer Perceptron)

Un MLP est composé d'une couche d'entrée (*input layer*), d'une ou plusieurs couches cachées (*hidden layers*) et d'une couche de sortie (*output layer*), chacune comportant plusieurs neurones (sauf éventuellement la sortie).

- **Couche d'entrée** : un neurone par feature ; uniquement des features numériques, à la même échelle (normalisées/standardisées).
- **Neurone** : calcule une somme pondérée des entrées (`Σ xⱼwⱼ`), puis applique une **fonction d'activation** non linéaire pour produire sa sortie.
- **Fonctions d'activation** : sigmoïde et tangente hyperbolique (historiques) ; ReLU, Leaky ReLU, ELU (modernes, privilégiées en couche cachée car moins sujettes au *vanishing gradient*).
- **Couche de sortie** :
  - régression : 1 neurone, combinaison linéaire, **sans** fonction d'activation — la valeur brute est la prédiction ;
  - classification binaire : 1 neurone avec activation **sigmoïde** — la sortie est la probabilité d'appartenir à la classe positive ;
  - classification multiclasse : autant de neurones que de classes, activation **softmax**.

**Motif d'architecture courant (précision orale)** : plutôt qu'un nombre de neurones arbitraire par couche cachée, une pratique répandue consiste à faire d'abord **augmenter** le nombre de neurones d'une couche à l'autre, puis à le **redescendre** progressivement vers la sortie — comme si le réseau détaillait d'abord l'information, avant de la résumer. Ce n'est pas une règle absolue, mais un motif à connaître avant de choisir une architecture « au hasard ».

### Entraînement d'un réseau

- **Fonction de coût (loss)** : mesure l'écart entre prédiction et cible. MSE pour la régression, entropie croisée binaire (*binary_crossentropy*, ou log loss) pour la classification binaire, entropie croisée catégorielle pour le multiclasse. Entraîner = trouver les poids qui minimisent cette fonction.
- **Descente de gradient** : les poids sont mis à jour selon leur gradient (dérivée partielle du coût) et un **taux d'apprentissage**.
- **Rétropropagation (backpropagation)** : propagation avant (*feedforward*) pour obtenir les prédictions, calcul de l'erreur en sortie, puis propagation de cette erreur couche par couche vers l'entrée (règle de dérivation des fonctions composées) pour calculer le gradient de chaque poids.
- **Descente de gradient stochastique (SGD)** : calculer le coût sur l'ensemble des données à chaque mise à jour est trop coûteux à grande échelle. On met donc à jour les poids à partir d'une seule donnée (SGD stricte) ou d'un lot (*mini-batch gradient descent*).
- **Optimiseurs** :
  - **Momentum** : ajoute une fraction de la mise à jour précédente pour éviter les oscillations et accélérer la convergence.
  - **RMSProp** : taux d'apprentissage adapté par poids, en divisant le gradient par la racine de la moyenne mobile des carrés des gradients précédents — évite les plateaux.
  - **Adam** = Momentum + RMSProp. Fonctionne bien dans la grande majorité des cas. Réglages de départ usuels : β1 (momentum) = 0,9 ; β2 (RMSProp) = 0,999 ; taux d'apprentissage entre 0,0001 et 0,001.

### Surapprentissage et régularisation

- **Surapprentissage (overfitting)** : le modèle épouse le bruit du train et généralise mal ; à l'opposé, le **sous-apprentissage** (underfitting) ne capture pas assez la structure des données.
- **Dropout** : à chaque passe d'entraînement, certains neurones sont ignorés aléatoirement, ce qui force le réseau à ne pas dépendre de quelques neurones seulement → meilleure généralisation.
- **Early stopping** : on évalue le critère sur le jeu de validation à intervalles réguliers ; si celui-ci cesse de s'améliorer, on arrête et on revient aux poids de la meilleure itération.
- **Normalisation/standardisation des features** : des échelles très différentes entre features ralentissent fortement la convergence — la remarque s'applique aussi entre couches cachées.
- **Batch normalization** : normalise et standardise la sortie d'une couche (insérée entre la combinaison linéaire et la fonction d'activation). Stabilise l'entraînement, autorise un taux d'apprentissage plus élevé, rend les couches plus indépendantes entre elles, réduit l'overfitting. Dans Keras : `Dense(n, use_bias=False)` → `BatchNormalization()` → `Activation(...)`.

### CNN (Convolutional Neural Network)

- **Convolution** : une image est une matrice de pixels (H × L × canaux ; 1 canal en niveaux de gris, 3 en RVB). Un **filtre** (masque de convolution, ex. 3×3 ou 5×5) glisse sur l'image et calcule, à chaque position, une multiplication élément par élément puis une somme — c'est un détecteur de caractéristique (ex. traits horizontaux/verticaux). Sur une image couleur, le filtre a une profondeur égale au nombre de canaux.
- **Couche de convolution complète** : plusieurs filtres en parallèle, suivis d'une fonction d'activation (souvent ReLU).
- **Couche d'aplatissement (Flatten)** : en fin de partie convolutive, les cartes de features (plusieurs matrices) sont transformées en un seul vecteur, qui devient l'entrée d'un réseau *fully-connected* (couches Dense) chargé de la classification finale.
- **Principe d'architecture général** : le nombre de filtres augmente avec la profondeur (features de plus en plus complexes), la taille spatiale de l'image diminue progressivement (via le pooling ou le *stride*) jusqu'à une caractérisation unique.

### Architectures CNN classiques (repères historiques)

| Architecture | Idée clé |
|---|---|
| AlexNet | Une des premières architectures profondes à grande échelle (convolutions + max pooling + couches fully-connected). |
| VGG | Empilement homogène de convolutions 3×3 et de max pooling, profondeur croissante. |
| Inception | Plusieurs tailles de filtres en parallèle sur la même entrée (1×1, 3×3, 5×5, max-pool), concaténées ; les filtres 1×1 contrôlent la profondeur. Inception v1 ajoute des fonctions de coût intermédiaires (*auxiliary loss*) pour limiter le *vanishing gradient* sur un réseau profond. |
| ResNet | Ajoute des **connexions résiduelles** (« saute-couches ») qui permettent d'empiler beaucoup plus de couches : si une couche n'est pas utile, le réseau peut la faire converger vers la fonction identité plutôt que de dégrader la performance. |
| DenseNet | Chaque couche reçoit en entrée les sorties de **toutes** les couches précédentes du même bloc (réutilisation maximale des features) → moins de filtres nécessaires par couche pour une performance comparable. |

Ces architectures ne sont pas ré-implémentées dans ce dépôt ; elles servent surtout de repère de culture générale et de socle pour le transfer learning (section suivante).

### Transfer learning

**Principe** : réutiliser les couches convolutives d'un réseau déjà entraîné sur un grand jeu de données (ex. ImageNet) comme extracteur de features, plutôt que de tout réentraîner à partir de zéro.

Deux méthodes :

1. **CNN comme encodeur** : on prend la sortie d'une couche cachée du réseau pré-entraîné comme entrée d'un nouveau modèle (réseau de neurones, mais aussi Random Forest, boosting…).
2. **CNN comme point de départ (fine-tuning)** : les premières couches restent gelées (non entraînables), les dernières sont réentraînées sur les nouvelles données. Plus il y a de données disponibles, plus on peut se permettre de rendre de couches entraînables.

Domaines applicables : vision (de nombreux CNN pré-entraînés sur des millions d'images labellisées), son (modèles anglophones matures — DeepSpeech, WaveNet — mais peu de données françaises libres ; alternative : API cloud payantes Google/Amazon/Watson).

### Auto-encodeurs (aperçu)

Un **auto-encodeur** est un réseau entraîné à reconstruire sa propre entrée en sortie (apprentissage **non supervisé** : la cible est l'entrée elle-même). Il comporte un **encodeur** qui compresse l'entrée vers un **espace latent** de petite dimension, et un **décodeur** qui reconstruit l'entrée à partir de cette représentation compressée. Ce goulot d'étranglement force le réseau à n'apprendre que l'information essentielle.

- Fonction de coût : MSE (données continues) ou entropie croisée binaire (données dans [0, 1]) ; même optimisation qu'un réseau classique (Adam + rétropropagation).
- Hyperparamètre clé : la dimension de l'espace latent — trop grande, le réseau « recopie » sans rien apprendre ; trop petite, la reconstruction est de mauvaise qualité.
- Variantes : débruiteur (*denoising*, entrée bruitée → cible originale, à la base des modèles génératifs d'images par diffusion), parcimonieux (*sparse*, contrainte sur l'espace latent, features plus interprétables), **convolutif** (adapté aux images), **variationnel (VAE)** (espace latent probabiliste, modèle génératif).
- Applications : réduction de dimension (alternative non linéaire à l'ACP), débruitage (image ou signal, y compris audio), **détection d'anomalies** (une erreur de reconstruction élevée signale une donnée atypique), pré-entraînement et apprentissage de représentation (transfer learning), génération de données (VAE), compression.
- **Entrée et sortie de types différents** : l'encodeur et le décodeur n'ont pas à porter sur le même type de donnée. Exemple : encoder une image en vecteur, puis décoder ce vecteur en légende textuelle (*image captioning*) — c'est toujours un couple encodeur-décodeur, entraîné de bout en bout, même si l'entrée est une image et la sortie du texte.
- **Un modèle par type d'entrée** : un auto-encodeur entraîné sur un seul type d'objet (ex. des images) ne sait gérer que ce type et cette taille d'entrée à l'inférence. Pour prendre en entrée plusieurs types de données (ex. image et texte), deux options : soit entraîner un seul modèle qui encode les deux dès le départ, soit utiliser deux modèles séparés, chacun spécialisé, et aiguiller la donnée vers le bon.
- **Encodeur seul, décodeur seul, encodeur-décodeur** : un modèle « encodeur seul » comprend pourquoi il existe (produire une représentation, ex. features pour la classification). Un modèle qualifié de « décodeur seul » — le cas des LLM, qui prédisent le texte token par token — est un abus de langage courant selon la formatrice : décoder suppose qu'une représentation a d'abord été encodée quelque part (le passage du texte en entrée vers une représentation vectorielle interne). Il y a donc toujours un encodage implicite, même dans une architecture dite « decoder-only ».

**Dans ce dépôt**, l'application concrète « détection d'anomalies par auto-encodeur convolutif » sur les images InduSense (wood, MVTec AD) est détaillée dans la [fiche 11 — Auto-encodeur de détection d'anomalies](11-autoencodeur-anomalies-tensorflow-pytorch-cpu-gpu.md) et dans la [fiche 15 — heatmaps, ratio de compression, SSIM, PatchCore](15-auto-encodeur-heatmaps-ratio-compression-ssim.md) : implémentation TensorFlow et PyTorch, CPU et GPU, choix du seuil de reconstruction, localisation pixel du défaut. Cette fiche 14 n'y ajoute que le cadre théorique général.

## Démarche

1. Vérifier que les features d'entrée sont numériques et à la même échelle (normalisation/standardisation).
2. Choisir une architecture (nombre de couches cachées, neurones par couche, activations) adaptée à la nature du problème (régression, classification binaire, multiclasse, image).
3. Choisir la fonction de coût correspondante et un optimiseur (Adam par défaut).
4. Surveiller le sur/sous-apprentissage via le jeu de validation ; ajouter dropout, batch normalization ou early stopping si besoin.
5. Pour une image : privilégier un CNN plutôt qu'un MLP, ou réutiliser un CNN pré-entraîné par transfer learning si les données disponibles sont limitées.

## Erreurs fréquentes et bonnes pratiques

- Mettre une fonction d'activation sur la sortie d'un réseau de régression : la sortie doit être une combinaison linéaire sans activation.
- Oublier la sigmoïde/softmax en sortie d'un réseau de classification : sans cela, la sortie n'est pas une probabilité interprétable.
- Entraîner sur des features à des échelles très différentes sans normaliser : convergence lente, voire absente.
- Confondre paramètre appris (poids, biais) et hyperparamètre choisi avant l'entraînement (nombre de couches, taux d'apprentissage, taille de l'espace latent).
- Choisir un espace latent d'auto-encodeur trop grand « pour être sûr de bien reconstruire » : le réseau recopie l'entrée sans rien apprendre d'utile à la détection d'anomalies.
- Réentraîner un CNN pré-entraîné en entier avec peu de données : risque fort de surapprentissage ; préférer geler les premières couches.

## Points à retenir pour le QCM

- Un MLP a une couche d'entrée, une ou plusieurs couches cachées, une couche de sortie.
- La sortie d'un réseau de régression n'a pas de fonction d'activation ; celle d'une classification binaire utilise une sigmoïde.
- Adam combine Momentum et RMSProp.
- Le dropout et l'early stopping luttent contre le surapprentissage ; la batch normalization stabilise et accélère l'entraînement.
- Une convolution applique un filtre glissant sur l'image pour détecter des caractéristiques locales ; la couche Flatten transforme les cartes de features en vecteur avant les couches denses.
- ResNet ajoute des connexions résiduelles pour permettre des réseaux plus profonds ; DenseNet réutilise les features de toutes les couches précédentes d'un bloc.
- Le transfer learning réutilise un réseau pré-entraîné, soit comme extracteur de features figé, soit en fine-tuning partiel.
- Un auto-encodeur est un apprentissage non supervisé dont la cible est l'entrée elle-même.
- Un auto-encodeur entraîné sur un seul type d'entrée ne sait pas en traiter un autre à l'inférence : il faut soit l'entraîner conjointement sur les deux dès le départ, soit utiliser deux modèles séparés.
- Qualifier un LLM de « décodeur seul » est un abus de langage : il y a toujours une étape d'encodage implicite avant tout décodage.

## Points à savoir expliquer lors de la soutenance

- Pourquoi la couche de sortie diffère entre régression et classification.
- Ce qu'apporte la rétropropagation par rapport à un calcul naïf du gradient.
- Pourquoi Adam est un choix de défaut raisonnable, et ce qu'il combine.
- La différence entre dropout, early stopping et batch normalization, et quand utiliser chacun.
- Pourquoi le transfer learning est pertinent quand peu de données labellisées sont disponibles.
- Comment un auto-encodeur permet de détecter des anomalies sans exemples de défauts étiquetés (lien avec la fiche 11).
- Pourquoi un encodeur et un décodeur peuvent porter sur deux types de données différents (ex. image en entrée, texte en sortie), avec un exemple concret (légende d'image).
- Pourquoi une architecture LLM dite « decoder-only » comporte malgré tout un encodage implicite du texte d'entrée.

## Sources du cours

- `12_Deep_Learning.pdf`, support Aelion « Deep Learning » (Parcours IA), diapositives 1 à 61.
- [Transcription de la séance du 21/09](../02-transcriptions/09-jour-3-deep-learning-reseaux-de-neurones.txt).
- [Transcription du cours auto-encodeurs du 22/09](../02-transcriptions/11-jour-4-cours-auto-encodeurs.txt).

## Pour aller plus loin

- [Keras — Guide des couches](https://keras.io/api/layers/)
- [CS231n — Convolutional Neural Networks for Visual Recognition](https://cs231n.github.io/)
- [Distill.pub — visualisations pédagogiques de Deep Learning](https://distill.pub/)
