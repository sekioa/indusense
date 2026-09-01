# Analyse temporelle des incidents et des maintenances

## Définition et objectif

Une **analyse temporelle** étudie des événements en tenant compte de leur ordre et de leur date. Dans le TP Indusense, l'objectif est de rapprocher les incidents signalés et les opérations de maintenance d'une même machine afin de retracer leur histoire commune.

L'**alignement temporel** consiste à placer plusieurs sources sur les mêmes entités et les mêmes périodes. Comparer directement deux colonnes sans aligner les machines, les fuseaux et les fenêtres produirait des associations trompeuses.

Une **corrélation** mesure l'association entre deux variables. Elle ne prouve pas qu'une variable cause l'autre.

## Notions essentielles

- Une **granularité temporelle** est la durée d'une période d'agrégation : jour, semaine ou mois.
- Une **fenêtre temporelle** délimite la période observée autour d'un événement, par exemple 30 jours avant et 30 jours après une maintenance.
- Une donnée **timezone-aware** contient un fuseau ou un décalage UTC ; une donnée **timezone-naive** n'en contient pas.
- Le coefficient de **Pearson** mesure surtout une relation linéaire entre deux variables numériques.
- Le coefficient de **Spearman** compare le rang des valeurs. Il est adapté à une relation monotone et résiste mieux qu'une corrélation linéaire aux distributions asymétriques.
- Le **test exact de Fisher** mesure l'association entre deux variables catégorielles dans un petit tableau d'effectifs. Une valeur `p` très faible fournit un argument contre leur indépendance, mais ne prouve pas une causalité.
- Le **V de Cramér** mesure l'intensité d'une association entre deux variables catégorielles. Avec peu de lignes et beaucoup de catégories, sa valeur peut sembler élevée par hasard ; un test par permutations permet alors de comparer le résultat à des réaffectations aléatoires conservant les mêmes catégories.
- Une **corrélation décalée** compare une série au temps `t` avec l'autre série avant ou après `t`.
- Une **analyse événementielle** replace chaque événement de référence au temps zéro et observe ce qui se passe avant et après.

## Méthode retenue dans le TP

### 1. Qualifier les deux sources

Les données observées contiennent :

- 1 245 incidents répartis sur 15 machines ;
- 115 opérations de maintenance sur les mêmes 15 machines ;
- 90 maintenances proactives et 25 maintenances réactives ;
- une période temporelle commune d'environ 350 jours.

`machine_code` et `machine_id` utilisent les mêmes 15 codes. Cette correspondance permet un rapprochement par machine.

### 2. Harmoniser les fuseaux

`maintenance_at` contient le décalage `+00` et est donc explicitement en UTC. La date et l'heure des incidents ne précisent aucun fuseau dans le CSV, mais l'information métier confirme que toutes les données temporelles Indusense sont en UTC. Les timestamps sans offset doivent donc être interprétés directement en UTC, sans localisation préalable en `Europe/Paris` et sans décalage de leur heure affichée.

Le notebook exploratoire comparait initialement un scénario UTC et un scénario `Europe/Paris` parce que cette information métier n'était pas encore disponible. Cette comparaison reste une analyse de sensibilité historique ; le scénario UTC est désormais le seul référentiel canonique pour Silver.

### 3. Construire un panel mensuel complet

Un **panel** est un tableau qui suit plusieurs entités au fil du temps. Le panel du TP possède une ligne pour chaque couple `machine × mois` et deux comptes principaux : incidents et maintenances.

Toutes les combinaisons machine-mois sont créées, y compris les mois sans événement. Les absences sont remplacées par zéro afin de ne pas supprimer silencieusement les périodes calmes.

Le mois est retenu pour la vue annuelle : le jour produisait 97,8 % de périodes sans maintenance et la semaine 85,1 %. Une analyse uniquement mensuelle masquerait cependant l'ordre de deux événements proches d'un changement de mois.

### 4. Ajouter une fenêtre de 30 jours

Pour chaque maintenance, les incidents de la même machine sont comptés :

- pendant les 30 jours précédents ;
- pendant les 30 jours suivants.

Cette analyse événementielle complète l'agrégation mensuelle. Le choix de 30 jours est une hypothèse métier qui peut être testée avec d'autres fenêtres, par exemple 15 ou 60 jours.

## Résultats observés et limites

- L'analyse exploratoire comparait UTC et `Europe/Paris` et obtenait la même corrélation mensuelle de Spearman, environ `0,0723`. L'information métier désormais disponible impose de retenir uniquement le résultat UTC dans le pipeline Silver.
- La différence observée sur le compte avant/après de 3 maintenances illustre le risque d'inventer un fuseau local pour des données métier UTC.
- Pour les maintenances proactives, les moyennes sont proches : environ 6,3 incidents avant et après.
- Pour les maintenances réactives, environ 10 incidents sont observés avant et 4,6 après.
- Cette baisse descriptive ne prouve pas que la maintenance est l'unique cause. La production, l'âge, la criticité, la saison ou l'utilisation peuvent également intervenir.

`related_incident_id` porte une relation structurelle forte : il est renseigné pour les 25 maintenances réactives et absent pour les 90 maintenances proactives. Le test exact de Fisher donne `p ≈ 7,88 × 10⁻²⁶`. Les identifiants et les dates des incidents référencés suivent exactement l'ordre des maintenances réactives selon Spearman (`ρ = 1`) et les 25 incidents précèdent leur maintenance.

Cette structure ne démontre toutefois pas que chaque identifiant désigne l'incident déclencheur précis. Un seul lien concerne la même machine ; aucun incident référencé n'est l'incident global immédiatement antérieur à sa maintenance. Le délai varie de 1,7 à 102,7 jours, avec une médiane de 35,7 jours, et augmente presque parfaitement avec l'ordre des maintenances (`ρ ≈ 0,9915`). L'association composant remplacé–type d'incident n'est pas concluante au test par permutations (`p ≈ 0,265`), pas plus que l'association entre les deux machines (`p ≈ 0,848`) ou une différence de gravité (`p ≈ 0,103`).

Conclusion initiale sur le CSV : le lien semblait devoir être conservé comme une relation fournie par la source, avec une signification causale et une éventuelle propagation inter-machine restant à confirmer avec le métier. Le formateur a depuis confirmé que `machine.csv` résulte d'une création de données défectueuse et que la table `machine` de `machine.sql` fait foi pour les identifiants machine. Le contrôle de cette source SQL montre que 503 des 1 472 maintenances réactives reliées, soit 34,17 %, référencent un incident porté par une autre machine. Les 1 472 identifiants existent tous dans le fichier incidents. La décision retenue conserve `machine.sql` et le Bronze inchangés, puis reporte en Silver l'identifiant machine de l'incident sur la maintenance correspondante par `related_incident_id`.

Le croisement avec le commentaire Bronze renforce la réalité sémantique du lien. Les 25 descriptions de maintenance mentionnent explicitement l'identifiant associé sous la forme d'une intervention corrective réalisée après cet incident. La similarité lexicale entre le composant remplacé et le commentaire de l'incident est supérieure aux appariements aléatoires (`p ≈ 0,0004`). Une grille de compatibilité métier volontairement prudente reconnaît 12 couples composant–symptôme sur 25, contre 6,66 en moyenne après permutation (`p ≈ 0,0094`). Par exemple, des capteurs de température sont associés à des symptômes thermiques ou à des alarmes de capteur, un roulement à un bruit mécanique et une courroie à des vibrations.

Les commentaires d'incident ne nomment toutefois aucune machine : sur les 1 245 commentaires, dont les 25 incidents reliés, aucun ne contient un code `MACH-xx`, un modèle de machine (`InduPress-X1` à `InduPress-Z1`) ni les termes génériques recherchés « machine », « presse », « équipement » ou « ligne ». Le commentaire décrit donc un symptôme, mais ne permet pas d'identifier une machine destinataire différente ni d'expliquer directement les 24 relations inter-machine.

Ces deux tests ciblés ne contredisent pas le test global composant–type non concluant (`p ≈ 0,265`) : le test global compare toutes les catégories exactes dans un tableau très clairsemé, tandis que les tests ciblés recherchent une proximité textuelle ou une compatibilité regroupée. Ils restent exploratoires, car les règles de rapprochement n'ont pas été définies à l'avance avec le métier.

Les machines reliées dans le CSV ne partageaient pas plus souvent que le hasard leur modèle (`p ≈ 0,637`), leur ligne de production (`p ≈ 0,376`), leur atelier (`p ≈ 0,849`) ou leur criticité (`p ≈ 0,922`). Ces statistiques restent utiles comme exemple de détection d'une incohérence, mais pas comme connaissance métier à intégrer au Silver. La valeur reçue reste disponible dans Bronze et dans `source_machine_code`, tandis que `machine_code` porte la valeur alignée dans Silver.

Le sens de la correction ne peut pas être inversé sans ambiguïté : 363 incidents sont référencés par des maintenances portant deux ou trois codes machine différents. Reporter ces codes vers l'incident imposerait un choix arbitraire. Reporter le code de l'incident vers chaque maintenance liée fournit au contraire une machine unique par couple incident-maintenance.

Le commentaire a servi ici à qualifier la relation dans le Bronze. Il reste exclu du Silver par minimisation : la conclusion agrégée peut être conservée sans recopier le texte libre ni les informations relatives aux opérateurs.

### Mise en pratique reproductible

Le notebook `indusense/data-exercice-3.ipynb` reproduit cette qualification depuis les deux CSV Bronze. Il contrôle l'association entre maintenance réactive et présence du lien avec Fisher, l'ordre temporel avec Pearson et Spearman, la proximité commentaire–composant avec des permutations, puis les attributs des machines reliées. Les commentaires sont utilisés seulement en mémoire et ne sont pas exportés. Les assertions finales vérifient également que les empreintes SHA-256 des fichiers Bronze restent inchangées.

## Exemple concret avec pandas

```python
panel = (
    incidents.groupby(["machine_id", "mois"])
    .size()
    .rename("incidents")
    .to_frame()
    .join(
        maintenances.groupby(["machine_id", "mois"])
        .size()
        .rename("maintenances"),
        how="outer",
    )
    .fillna(0)
)

spearman = panel["maintenances"].rank().corr(
    panel["incidents"].rank()
)
```

La corrélation est ici calculée sur les rangs. Pour une analyse rigoureuse, le panel doit auparavant être réindexé sur toutes les combinaisons machine-mois attendues.

## Graphiques utiles avec matplotlib

- courbe du nombre d'incidents par mois ;
- histogrammes ou diagrammes en barres par sévérité, type et machine ;
- nuage de points incidents-maintenance par machine et par mois ;
- courbe de corrélation selon plusieurs décalages temporels ;
- nuage de points incidents avant/après chaque maintenance ;
- chronologie commune des incidents et maintenances.

## Raconter l'histoire d'un graphique

Une analyse de graphe ne doit pas se limiter à décrire sa forme. Une restitution utile suit quatre niveaux :

1. **constat chiffré** : indiquer les valeurs, catégories ou périodes dominantes ;
2. **interprétation métier** : expliquer ce que cette structure peut signifier dans le contexte industriel ;
3. **limite** : identifier ce que les données ne permettent pas de conclure ;
4. **suite proposée** : nommer la donnée ou le contrôle qui permettrait d'approfondir l'hypothèse.

Exemple appliqué au TP : environ 10 incidents sont observés avant une maintenance réactive contre 4,6 après. Le graphe raconte une séquence plausible « hausse des incidents, intervention, période plus calme ». Il ne démontre pas à lui seul l'efficacité causale de l'intervention, car les maintenances réactives sont déclenchées après un problème et d'autres facteurs peuvent évoluer simultanément.

Toujours signaler les périodes incomplètes. Dans le fichier incidents, juin 2026 ne contient que les huit premiers jours ; son total ne peut pas être comparé directement à celui d'un mois complet.

## Erreurs fréquentes et bonnes pratiques

- Mélanger des horodatages UTC et locaux sans conversion.
- Comparer des événements appartenant à des machines différentes sans que le besoin métier ou la méthode d'analyse autorise ce rapprochement.
- Supprimer les périodes sans événement au lieu de les représenter par zéro.
- Choisir une granularité sans mesurer le nombre de périodes vides.
- Déduire une causalité d'une simple corrélation ou d'une baisse avant/après.
- Faire confiance à une clé de rapprochement sans vérifier sa présence et sa cohérence métier.
- Interpréter une compatibilité entre un symptôme et un composant comme la preuve que le commentaire désigne la machine maintenue, alors qu'aucun identifiant de machine n'y figure.
- Tester de nombreux décalages puis ne présenter que celui qui donne la corrélation la plus forte.
- Ignorer que des fenêtres autour de maintenances proches peuvent se chevaucher.

## Points à retenir pour le QCM

- Corrélation ne signifie pas causalité.
- Deux séries temporelles doivent partager la même clé métier, le même fuseau et les mêmes fenêtres.
- Spearman travaille sur les rangs et mesure une relation monotone.
- Les périodes sans événement font partie de l'information et doivent être conservées.
- Une analyse événementielle compare une période avant et une période après un événement de référence.

## Points à savoir expliquer lors de la soutenance

- Pourquoi le mois a été retenu pour la vue annuelle et complété par une fenêtre de 30 jours.
- Pourquoi deux scénarios horaires avaient été explorés avant la validation métier, puis pourquoi seul UTC est retenu dans Silver.
- Pourquoi Spearman a été privilégié et comment interpréter une valeur proche de zéro.
- Pourquoi la diminution observée après certaines maintenances ne démontre pas une causalité.
- Comment les liens inter-machine portés par `related_incident_id` ont permis de détecter un défaut de données, puis comment la table `machine` et la machine de l'incident servent à réaligner les maintenances correspondantes en Silver sans modifier le Bronze.
- Comment vérifier qu'un graphe raconte fidèlement l'ordre des événements.

La correspondance exacte avec les compétences C1 à C9 reste à confirmer avec le Kit candidat.

## Pour aller plus loin

- [scikit-learn — TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html) : séparation entraînement/test adaptée à des données ordonnées dans le temps.
- [pandas — Séries temporelles](https://pandas.pydata.org/docs/user_guide/timeseries.html) : manipulation des dates, fuseaux horaires et fréquences.
