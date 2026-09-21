# MLflow et optimisation reproductible

## Objectif et prérequis

Tracer une optimisation de Random Forest et expliquer ce qui a réellement été validé. Point de départ : CSV Gold Indusense disponible, Python du projet installé avec `uv sync --dev`. Le notebook [06 — optimisation et MLflow](../../notebooks/02-sprint-2/01-maintenance-predictive/06-maintenance-optimisation-mlflow.ipynb) contient la procédure complète et les résultats exécutés.

## Définitions essentielles

- **Hyperparamètre** : réglage choisi avant l'entraînement (`max_depth`, nombre d'arbres…). Les règles des arbres sont des paramètres appris.
- **MLflow** : outil de suivi ; une expérience regroupe des runs (exécutions), un run conserve paramètres, métriques et artefacts (fichiers, modèles).
- **Validation croisée** : plusieurs couples train/validation, appelés folds. Ici, trois périodes chronologiques internes au train.
- **Average Precision (AP)** : résumé de la précision aux niveaux de rappel, à maximiser ; ne signifie pas le pourcentage de bonnes prédictions. Elle diffère de l'aire trapézoïdale PR-AUC.
- **Refit** : nouvel apprentissage d'une configuration sur l'ensemble du train, sans test.

## Méthode et exemple Indusense

1. Dans PowerShell, ouvrir la racine `C:\source\indusense`, puis lancer `./scripts/start-mlflow.ps1`. Le terminal indique l'adresse locale ; le laisser ouvert.
2. Dans le navigateur, ouvrir `http://127.0.0.1:5000`. Dans VS Code, ouvrir le notebook 06 et choisir le noyau `.venv/Scripts/python.exe`, puis **Run All**. Le noyau exécute les cellules Python.
3. Exclure les labels et comptages futurs ; conserver les splits chronologiques. Purger les 24 heures aux frontières puisque la cible regarde 24 heures dans le futur. Tous les enregistrements d'un timestamp restent ensemble.
4. La famille de modèles Random Forest a été retenue dans les travaux précédents, mais aucune forêt déjà apprise n'est modifiée. Tirer 16 configurations parmi 64 avec une graine 42, puis entraîner une nouvelle forêt depuis zéro pour chaque configuration et chaque fold. Random Search fixe le budget ; Grid Search explore toutes les combinaisons ; Optuna adapte les propositions aux essais précédents. La consigne permet ces trois méthodes, même si le cours développe surtout Optuna.
5. Ajuster l'imputation dans chaque fold. Sélectionner sur la moyenne AP des trois validations internes, jamais sur le test.
6. Comparer une référence manuelle réentraînée et le gagnant. Fixer séparément leurs seuils F2 sur la validation dédiée ; F2 privilégie le rappel, sans constituer une fonction de coût métier.
7. Mesurer sur le test une fois les choix figés. Chaque ligne est une **machine-heure** : l'état d'une machine observée pendant une heure. La cible vaut 1 lorsque cette machine connaîtra une panne dans les 24 heures suivantes. Par exemple, si une panne survient mardi à 14 h, les observations de cette machine du lundi 14 h au mardi 13 h peuvent toutes être positives : cela représente jusqu'à 24 machine-heures positives, mais toujours une seule panne. Les métriques et la matrice de confusion comptent donc des observations horaires, pas des incidents distincts.
8. Dans MLflow, sélectionner **Model training**, ouvrir **Experiments**, sélectionner `indusense-random-search-pedagogique`, développer la campagne et comparer `cv_ap`, `cv_std`, `gap_ap` avec **Compare**. Le tag `role` distingue référence, recherche et sensibilité. Le modèle sauvegardé correspond au refit.

Résultat attendu : marqueur `NOTEBOOK_OPTIMISATION_MLFLOW_VALIDE`, scores expliqués, modèles rechargeables et artefacts dans la campagne. `Ctrl+C` dans le terminal arrête l'interface ; les résultats restent dans `.mlflow/`. La base et les modèles locaux sont exclus de Git ; copier ensemble la base et les artefacts pour une sauvegarde. Les chemins locaux absolus demandent une adaptation pour déplacer le stockage sur une autre machine.

## Analyser et éviter les erreurs

### Lire les matrices de confusion avant/après

Dans le notebook, les lignes représentent la classe réelle et les colonnes la prédiction. La matrice est `[[VN, FP], [FN, VP]]` : vrais négatifs, faux positifs (fausses alertes), faux négatifs (positifs manqués), vrais positifs (positifs détectés). Chaque case affiche le nombre de machine-heures et le pourcentage dans sa ligne. Les pourcentages d'une ligne totalisent 100 %. `VP / (VP + FN)` est le rappel ; `FP / (VN + FP)` est le taux de faux positifs, pas `1 - précision`, dont le dénominateur est l'ensemble des alertes. Les deux graphiques partagent l'échelle de couleur. Les seuils ont été choisis sur validation : on compare donc le modèle et son seuil, sans régler le seuil sur le test.

### Limites méthodologiques

- L'écart-type entre folds est une dispersion, **pas un intervalle de confiance** (précision nécessaire au support `09_Optimisation.pdf`, p. 5). Les folds temporels ne sont pas indépendants.
- Un écart train-CV élevé signale un risque de surapprentissage ; son absence ne prouve pas une bonne généralisation universelle.
- Un test déjà consulté dans les exercices antérieurs ne redevient pas vierge. Confirmer avec une nouvelle période.
- Une sensibilité locale fait varier un seul hyperparamètre, les autres restant fixes. Son amplitude AP décrit l'influence dans cet espace ; elle ne mesure pas l'importance des variables et ne couvre pas toutes les interactions.
- La sensibilité ne doit pas changer silencieusement le gagnant après sélection. Consigner les sondes séparément et réutiliser les calculs identiques.
- Plus d'arbres coûte davantage sans garantir un progrès. Consigner temps CV, refit et journalisation ; ne pas convertir les secondes en CO₂ sans mesure.
- Une sortie brute mêlant scores, logs MLflow et avertissements répétés est difficile à interpréter. Afficher un tableau de classement, puis une comparaison courte entre référence et gagnant ; conserver le détail des runs dans MLflow. Ne masquer que les messages techniques connus et répétitifs : une véritable erreur doit rester visible et interrompre l'exécution.
- `ModuleNotFoundError` : vérifier le noyau ; interface vide : vérifier base et expérience ; assertion temporelle : vérifier les dates, ne pas retirer l'assertion.

## Résultats observés dans les deux campagnes

Les 16 configurations tirées ont donné un gagnant à 150 arbres, profondeur 6, 10 lignes minimum par feuille et 25 % de variables candidates. L'AP moyenne en validation croisée passe de 0,5575 à 0,5652, mais l'AP test baisse de 0,6151 à 0,5971. Les faux positifs passent de 4 423 à 4 499, pour un seul positif supplémentaire détecté (2 354 à 2 355). La réduction de l'écart train-CV (0,3563 à 0,1635) ne suffit donc pas à conclure à une amélioration du système. La profondeur est le réglage localement le plus sensible dans les valeurs testées. La campagne complète comporte 23 configurations distinctes et 92 entraînements, sensibilité et refits compris. Le test étant historique et déjà consulté, une nouvelle période reste nécessaire.

Le notebook 07 a ensuite exécuté une étude Optuna indépendante de 20 trials : 5 essais de démarrage exploratoires, puis 15 suggestions guidées par TPE. Le gagnant est le trial 12 : 450 arbres, profondeur 6, 30 lignes minimum par feuille, 2 lignes minimum pour une division et 35 % de variables candidates. L'AP CV atteint 0,5657. L'écart train-CV baisse de 0,3563 pour la référence à 0,1712, ce qui indique une régularisation plus forte, sans prouver à lui seul l'absence de surapprentissage.

Sur le test historique, Optuna obtient une AP de 0,6026 : meilleure que Random Search (0,5971), mais inférieure à la référence manuelle (0,6151). Son rappel monte de 67,68 % à 68,34 %, tandis que sa précision baisse de 34,74 % à 32,23 % et son F2 de 0,5689 à 0,5583. La matrice de confusion traduit ce compromis en `+23` machine-heures positives détectées et `+576` fausses alertes par rapport à la référence. Une ligne positive étant une machine observée pendant une heure avant une panne possible, ces 23 lignes ne représentent pas nécessairement 23 pannes distinctes.

L'importance fANOVA d'Optuna attribue 72,95 % de l'influence observée à `max_depth`, devant `min_samples_leaf` (13,61 %). Cette importance est conditionnelle aux 20 trials et à l'espace étudié ; ce n'est ni une importance de variable d'entrée, ni une vérité générale sur les Random Forest. La campagne Optuna totalise 84 fits et 47,6 minutes. L'expérience MLflow `indusense-optuna-pedagogique` contient 1 run parent, 20 trials et 1 référence, tous terminés.

## QCM et soutenance

Savoir distinguer paramètre/hyperparamètre, Grid/Random/Optuna, train/validation/test, métrique sans seuil et score au seuil. Expliquer pourquoi la recherche doit contenir les prétraitements et respecter le temps. Présenter méthode, budget total (y compris sondes et refits), résultats avant/après, limites et coût. L'installation de MLflow ne prouve ni l'absence de fuite ni la qualité du modèle. Correspondances C1–C9 à confirmer avec le Kit candidat.

## Références

- [Fiche détaillée sur l'optimisation](../02-sprint-2/04-revisions/08-optimisation-hyperparametres-et-validation-croisee.md)
- [Cours](../02-sprint-2/01-cours/09_Optimisation.pdf), p. 4–10 ; [transcription](../02-sprint-2/02-transcriptions/06-tuning-des-hyperparametres.txt).
- [MLflow, base locale](https://mlflow.org/docs/latest/ml/tracking/tutorials/local-database).
