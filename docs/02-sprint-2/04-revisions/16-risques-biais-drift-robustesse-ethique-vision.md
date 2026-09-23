# Risques et robustesse d'un projet de vision industrielle : biais, drift, confidentialité, attaques adversariales

## Définition et objectif

Cette fiche synthétise le cours magistral sur les risques spécifiques à un projet de **computer
vision industrielle** (détection de défauts qualité) une fois le modèle envisagé en production :
**biais** de dataset, **dérive** (drift) du modèle ou des données, **confidentialité/RGPD** sur les
images, **robustesse** face aux données hors distribution et aux **attaques adversariales**, et les
**garde-fous** à mettre en place. Objectif : savoir identifier ces risques et les expliquer à l'oral
pour un projet de contrôle qualité par image, au-delà de la seule performance du modèle mesurée sur
un jeu de test.

## Notions essentielles

- **Biais de dataset** : un modèle apprend uniquement ce qu'on lui montre. Si le jeu d'entraînement
  n'est pas représentatif des conditions réelles de production (type de pièce, éclairage, angle,
  ligne de production), le modèle donne de bonnes performances sur les données préparées
  (entraînement/validation/test) mais se dégrade fortement en conditions réelles. Cas typiques :
  photos prises dans un environnement bien éclairé puis caméra en bout de ligne avec un éclairage
  plus faible ; une ligne de production surreprésentée dans le dataset (ex. 80 % des photos issues
  d'une seule ligne sur dix) fait que les particularités des autres lignes (angle, éclairage
  légèrement différents) sont vues comme anormales par le modèle.
- **Data drift** : les images de production évoluent progressivement (nouvelle caméra, usure du
  matériel, changement de lot, nouvelle façon de faire) et le modèle entraîné sur des données plus
  anciennes devient de moins en moins valable. Contrairement au biais (mauvaise performance dès la
  mise en production), le drift se traduit par une dégradation **progressive** des performances dans
  le temps.
- **Concept drift** : la définition même de ce qui est normal ou défaut change dans le temps (ex. un
  défaut auparavant rejeté devient toléré). Illustration hors imagerie : les modèles de prédiction de
  prix immobilier pendant le Covid, où les contraintes et les attentes des clients ont changé
  indépendamment du prix des matériaux. Un détecteur d'objets (ex. YOLO) peut aussi se dégrader si le
  contexte d'usage change progressivement (ex. véhicule autonome passant d'un usage majoritairement
  rural à un usage majoritairement urbain).
- **Confidentialité et RGPD** : les images peuvent contenir des données sensibles (visages, plaques
  d'immatriculation, informations propriétaires). Toute personne identifiable relève du RGPD.
  Mesures usuelles : anonymisation (flouter les visages, retirer nom/âge/ville), minimisation des
  données collectées (ex. ne pas conserver une image dès qu'un visage y apparaît), accès restreint
  aux données, et sécurisation du stockage/des échanges — y compris pour le **secret industriel**
  (un modèle et ses données d'entraînement révèlent beaucoup d'informations sur une ligne de
  production).
- **Donnée hors distribution (OOD)** : donnée très différente de tout ce que le modèle a vu à
  l'entraînement (ex. un modèle entraîné sur des `metal_nut` qui reçoit une noisette). Le
  comportement du modèle sur une donnée OOD ne peut pas être anticipé — ce n'est pas une erreur du
  modèle au sens propre, mais une situation hors de son domaine de validité.
- **Prédiction confiante mais fausse** : le risque principal sur donnée OOD ou image corrompue est
  qu'un modèle de classification produit souvent une prédiction avec un score de confiance élevé
  *même quand il se trompe*, ce qui est dangereux en décision automatique. **Avantage propre à
  l'auto-encodeur par reconstruction** : une entrée hors distribution devrait, en théorie, être mal
  reconstruite, donc générer une erreur de reconstruction élevée et être détectée comme anomalie —
  contrairement à d'autres architectures qui n'ont pas ce garde-fou intégré.
- **Qualité d'acquisition** : la donnée étant au cœur du projet, la qualité des capteurs/caméras en
  production est une source fréquente d'échec (mise au point défectueuse, poussière sur l'objectif)
  qui peut créer de **faux positifs** même avec un bon modèle. D'où l'intérêt de définir la chaîne
  d'acquisition (caméra, position) dès la conception du projet, de standardiser l'éclairage et le
  cadrage, et de planifier une maintenance régulière du matériel.
- **Attaques adversariales** : perturbations minimes, parfois invisibles à l'œil nu (quelques pixels
  modifiés), qui trompent le modèle sans que l'image semble altérée pour un humain — à distinguer
  d'une image franchement dégradée (flou, poussière), visible et donc plus facile à filtrer en amont.
  Un motif ou autocollant ajouté sur une pièce peut aussi déclencher massivement de fausses alertes.

## Démarche : garde-fous à mettre en place

1. **Auditer le dataset et le besoin métier en amont** : vérifier avec les utilisateurs métier que la
   composition du dataset correspond aux conditions réelles de production, et documenter les
   conditions de collecte (date, provenance, méthode de prise de vue) pour pouvoir investiguer plus
   tard en cas de problème.
2. **Monitorer les performances en continu** pour détecter un drift progressif, et prévoir un
   réentraînement périodique — avec une étape de vérification des nouvelles données avant de les
   remontrer au modèle (ne pas réinjecter des données de mauvaise qualité ou mal étiquetées).
3. **Calibrer les seuils de décision** (percentile, `moyenne + k·écart-type`) en arbitrant
   explicitement le coût des faux positifs contre celui des faux négatifs selon l'enjeu métier — en
   contrôle qualité, mieux vaut souvent détecter trop de défauts (à vérifier ensuite manuellement)
   que d'en laisser passer.
4. **Mettre en place un human-in-the-loop** : au-delà d'un seuil binaire, définir une zone
   d'incertitude (ex. probabilité de défaut entre deux seuils) où le modèle ne décide pas seul et
   demande une vérification humaine, plutôt qu'une seule frontière normal/anomalie.
5. **Documenter les limites du modèle** (dans une fiche/carte de modèle) : les cas exclus du
   périmètre d'entraînement (ex. plage de tailles ou de types de pièces couverte), pas une liste
   exhaustive de tout ce que le modèle ne sait pas faire.
6. **Prévoir un comportement de repli** si le modèle est indisponible ou peu sûr : arrêt de la
   production, bascule en défaut systématique, etc. — une décision à adapter aux enjeux métier, pas
   un détail technique secondaire.
7. **Tracer les alertes et chercher un minimum d'explicabilité** sur les décisions du modèle, même si
   les méthodes d'explicabilité restent imparfaites et non déterministes à 100 %.
8. **Définir la gouvernance** : qui décide en dernier ressort, qui est responsable et garant du
   système en cas de dysfonctionnement (ex. surcharge d'alertes sans personnel disponible pour les
   vérifier).

## Exemple concret

Une chaîne de contrôle qualité entraîne un auto-encodeur sur des pièces photographiées dans un poste
d'essai bien éclairé. En production, la caméra en bout de ligne capte des images moins lumineuses :
le modèle, biaisé par un éclairage d'entraînement non représentatif, dégrade ses performances dès la
mise en service (biais), *avant même* toute évolution ultérieure de la ligne. Si, ensuite, une
caméra s'encrasse progressivement ou qu'une pièce d'usure change la texture des pièces produites, les
performances se dégradent en plus **petit à petit** dans le temps (drift) — un phénomène distinct,
détectable uniquement par un monitoring continu, pas par la seule évaluation initiale sur le jeu de
test.

## Erreurs fréquentes et bonnes pratiques

- Valider un modèle uniquement sur des métriques de test flatteuses sans vérifier que le dataset est
  représentatif des conditions réelles de production (risque de biais non détecté avant la mise en
  service).
- Confondre biais et drift : le biais donne de mauvaises performances *dès* la mise en production, le
  drift dégrade les performances *progressivement* après coup.
- Réentraîner un modèle en réinjectant des données de production sans étape de vérification de leur
  qualité, ce qui peut renforcer une dérive plutôt que la corriger.
- Croire qu'un score de confiance élevé garantit une prédiction correcte : sur une donnée hors
  distribution ou corrompue, un modèle peut être confiant et faux.
- Négliger la chaîne d'acquisition (caméra, éclairage, cadrage) en pensant que seule la qualité du
  modèle compte : une caméra mal calibrée peut générer des faux positifs indépendamment du modèle.
- Oublier le volet confidentialité/RGPD sur des images industrielles qui peuvent contenir des visages,
  plaques ou informations propriétaires.
- Fixer un seuil de décision unique et binaire sans zone d'incertitude pour la supervision humaine sur
  les cas limites.
- Ne pas documenter les limites explicites du modèle (cas exclus du périmètre d'entraînement) ni le
  comportement de repli en cas d'indisponibilité.

## Points à retenir pour le QCM

- Le biais de dataset provient d'un jeu d'entraînement non représentatif des conditions réelles
  (type de pièce, éclairage, ligne de production surreprésentée).
- Data drift = dérive progressive des données de production ; concept drift = la définition même du
  normal/défaut change dans le temps.
- Le RGPD s'applique à toute image contenant une personne identifiable ; anonymisation et
  minimisation des données sont les mesures usuelles.
- Une donnée hors distribution (OOD) est très différente de tout ce que le modèle a vu à
  l'entraînement ; son comportement dessus n'est pas prévisible.
- Un modèle peut produire une prédiction confiante mais fausse sur une donnée hors distribution ;
  l'auto-encodeur par reconstruction a un garde-fou naturel (mauvaise reconstruction) que d'autres
  architectures n'ont pas.
- Les attaques adversariales modifient parfois seulement quelques pixels, de façon invisible à l'œil
  nu, mais peuvent tromper fortement le modèle.
- Un human-in-the-loop repose sur plusieurs seuils (zone de certitude / zone d'incertitude à vérifier
  manuellement), pas uniquement sur un seuil binaire.

## Points à savoir expliquer lors de la soutenance

- La différence entre biais, data drift et concept drift, avec un exemple pour chacun.
- Pourquoi un score de confiance élevé ne garantit pas une prédiction correcte, et en quoi
  l'auto-encodeur par reconstruction offre un garde-fou différent des modèles de classification
  classiques face aux données hors distribution.
- Comment une caméra mal calibrée peut augmenter le taux de faux positifs indépendamment de la
  qualité du modèle, et quelles mesures de maintenance/standardisation limitent ce risque.
- Les mesures de confidentialité applicables à un dataset d'images industrielles (RGPD, anonymisation,
  minimisation, accès restreint, secret industriel).
- Comment un dispositif human-in-the-loop à seuils multiples réduit le risque d'une décision
  automatique erronée sur un cas incertain.
- Ce que doit couvrir la documentation des limites d'un modèle (cas exclus, comportement de repli) et
  pourquoi la question de la gouvernance (qui est responsable) fait partie intégrante du projet.

## Sources du cours

- [Transcription du cours magistral « risques éthiques et robustesse »](../02-transcriptions/13-risques-ethiques-robustesse.txt),
  support : [`15_Risques_ethiques_robustesse.pdf`](../01-cours/15_Risques_ethiques_robustesse.pdf).
