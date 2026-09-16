# Revue du TP Sprint 2 — corrections et explications

## Objectif concret

Cette note rend exploitable la revue orale du TP B5 : elle isole les consignes de l'intervenante, corrige les termes mal reconnus ou imprécis, et explique la partie centrale du TP sans modifier le notebook existant.

## Point de départ vérifié

La transcription locale horodatée est disponible dans [`04-revue-tp.txt`](../02-transcriptions/04-revue-tp.txt). Elle couvre environ 18 minutes, avec une interruption sans parole entre `00:15:06` et `00:17:56`. Les termes techniques qui suivent sont vérifiés par rapport à la consigne B5 et au notebook déjà validé.

## Ce que la revue demande effectivement

Les instructions suivantes sont attribuées à l'intervenante. Elles ne sont pas de nouvelles actions demandées par l'utilisateur dans ce document.

1. Choisir **un seul label cible**, par exemple `label_failure_next_24h`, comme sortie `y` du modèle.
2. Retirer des **features** (les colonnes d'entrée `X`) les identifiants, `split_set`, tous les labels `label_failure_next_*` et tous les `future_incident_count_*`.
3. Conserver les mesures et agrégats historiques : capteurs sur les dernières 6, 12 ou 24 heures, tendances calculées sur le passé, incidents passés, charge sur les dernières 24 heures et jours depuis la maintenance.
4. Réaliser le découpage train / validation / test avant les transformations. Ajuster l'imputation et la standardisation sur le train seulement, puis appliquer les transformations apprises à validation et test.
5. Mesurer le déséquilibre des classes et utiliser `class_weight="balanced"` pour la régression logistique de référence.
6. Proposer deux autres **classifieurs** compatibles avec une cible binaire, en indiquant brièvement pourquoi ils sont comparés à la baseline.

La dernière instruction est bien une demande de l'intervenante à la classe ; elle n'a pas été exécutée ici. Elle appartient à la prochaine étape du TP.

## La partie à comprendre : éviter la fuite de données

Une **feature** est une information disponible au modèle au moment où il doit prédire. La **cible** est la réponse à prédire. Ici, à l'instant `window_end`, le modèle doit déterminer si une panne aura lieu dans l'horizon choisi.

Une **fuite de données** (*data leakage*) apparaît lorsqu'une feature contient une information que le modèle n'aurait pas à cet instant en production. Par exemple, `future_incident_count_6h = 3` renseigne déjà sur les six heures futures. Si cette colonne restait dans `X` alors que la cible est « panne dans les six prochaines heures », le modèle apprendrait une relation presque évidente. Ses métriques seraient artificiellement excellentes, puis sa performance s'effondrerait en production : cette colonne future n'y existe pas encore.

En revanche, `incident_count_1h` ou une moyenne de capteur calculée sur les dernières 24 heures est acceptable : l'information provient du passé ou du présent au moment de la décision.

| Colonne ou type | Dans `X` ? | Raison |
| --- | --- | --- |
| `label_failure_next_24h` | Non, c'est `y` | C'est la sortie unique à apprendre. |
| Autres `label_failure_next_*` | Non | Elles décrivent aussi un résultat futur. |
| `future_incident_count_*` | Non | Elles utilisent le futur. |
| `machine_id_std`, timestamps bruts, `split_set` | Non | Métadonnées ou risque de mémorisation / fuite de protocole. |
| Capteurs et tendances sur fenêtres passées | Oui | Disponibles à l'instant de prédiction. |
| Incidents passés et jours depuis maintenance | Oui | Historique disponible en production. |

## Pourquoi `fit` ne doit concerner que le train

L'**imputation** remplace une valeur manquante ; la **standardisation** centre et réduit une variable à partir de sa moyenne et de son écart-type. Ces deux opérations peuvent elles-mêmes créer une fuite si elles sont calculées avec validation ou test.

Dans scikit-learn, `fit` signifie « apprendre les paramètres de la transformation » et `transform` signifie « appliquer les paramètres déjà appris ». La séquence correcte est donc :

1. prendre le train, la validation et le test déjà séparés dans l'ordre temporel ;
2. faire `fit` de l'imputeur et du `StandardScaler` sur le train uniquement ;
3. faire `transform` sur train, validation et test avec ces mêmes paramètres ;
4. entraîner le classifieur sur le train transformé ; choisir le seuil et les hyperparamètres sur la validation ; lire le test seulement à la fin.

Le `Pipeline` du notebook respecte cette règle lorsque son `fit(X_train, y_train)` est appelé : il apprend médianes, moyenne, écart-type et coefficients uniquement avec le train.

## Corrections de la transcription et précisions techniques

La transcription automatique conserve les hésitations. Les corrections ci-dessous améliorent sa lecture ; elles ne réattribuent pas de parole à l'intervenante.

| Passage de la transcription | Lecture corrigée / précision |
| --- | --- |
| « instant-terre » (`00:00:00`) | **instant T** : moment précis où la prédiction doit être réalisable. |
| « la belle est colonne » (`00:00:24`) | Passage peu intelligible. Le sens confirmé ensuite est : retirer les colonnes futures et les labels non retenus. |
| « 3 pans » (`00:01:41`) | Probablement **3 pannes** ou, dans le contexte immédiat, **3 incidents** dans les six heures futures. |
| « file de données » (`00:03:12`, `00:07:28`) | **fuite de données** (*data leakage*). |
| « split 7 7 » (`00:05:09`) | `split_set`. |
| « curatie » (`00:12:09`) | **accuracy** (exactitude) : proportion globale de prédictions correctes. |
| « extrêmes et tests » (`00:08:35`) | **train, validation et test**. |
| « régression linéaire » (`00:14:04`) | Correction importante : la baseline B5 est une **régression logistique**, donc un classifieur binaire, pas une régression linéaire de valeur continue. |
| Explication de `class_weight="balanced"` (`00:12:02`) | Nuance : ce paramètre pondère les erreurs dans la fonction de coût **pendant l'entraînement**. Il ne modifie pas le calcul de l'accuracy, de la PR-AUC ou des autres métriques d'évaluation. |

Une valeur manquante peut être remplacée directement par zéro sur tous les jeux uniquement si zéro a une signification métier certaine et si cette règle est définie sans observer validation ou test. Pour les autres colonnes du B5, la médiane doit être apprise sur le train, comme le fait le notebook.

## À savoir expliquer à l'oral

- La question métier est : « avec les informations connues maintenant, une panne surviendra-t-elle dans les 24 heures ? »
- Une colonne future fait obtenir une évaluation trompeuse : elle doit être retirée de `X` dans le train, la validation et le test.
- Le découpage doit précéder l'imputation et la standardisation ; sinon le passé apprend indirectement le futur.
- `class_weight="balanced"` rend l'apprentissage plus attentif aux pannes rares, mais ne remplace pas le choix d'une métrique et d'un seuil métier.
- Comparer des modèles ne change jamais le protocole : mêmes features autorisées, même découpage temporel et même validation.

## Validation et périmètre

Validé : la transcription a été créée localement, les concepts ont été recoupés avec la consigne B5 et les corrections ci-dessus sont cohérentes avec le notebook existant. Non exécuté : le choix et l'entraînement de deux modèles supplémentaires, qui restent une étape distincte à définir par l'utilisateur.
