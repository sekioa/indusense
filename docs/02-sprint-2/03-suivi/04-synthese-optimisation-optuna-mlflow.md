# Optimisation Indusense avec Optuna - synthèse

**Besoin.** Classer les machine-heures selon le risque de panne à 24 h. Chaque trial entraîne de nouvelles forêts ; aucune forêt existante n'est modifiée.

**Méthode.** Optuna avec TPESampler, graine 42, 20 trials dont 5 de démarrage, sans pruning. Trois folds chronologiques internes au train, gap de 24 h, imputation apprise dans chaque fold. Average Precision maximisée ; seuil F2 choisi sur validation ; test exclu de tout réglage.

**Gagnant.** Trial 12 : {'n_estimators': 450, 'max_depth': 6, 'min_samples_leaf': 30, 'min_samples_split': 2, 'max_features': 0.35}. AP CV 0.5575 -> 0.5657 ; écart train-CV 0.3563 -> 0.1712. Hyperparamètre fANOVA principal : max_depth (72.9%).

**Test.** AP 0.6151 -> 0.6026 (-0.0125) ; précision 34.74% -> 32.23% ; rappel 67.68% -> 68.34% ; F2 0.5689 -> 0.5583. FP 4423 -> 4999 ; FN 1124 -> 1101.

**Coût et limites.** 84 fits et 47.6 minutes pour cette exécution. Les importances dépendent de 20 trials. Le test avait déjà été consulté : confirmer sur une période future et avec des métriques par panne distincte. MLflow trace les trials, paramètres, métriques, modèles, versions et empreinte du CSV. Énergie et CO2 non mesurés.
