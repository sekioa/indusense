# Explicabilité SHAP : TreeExplainer, summary, waterfall, dependence

## Objectif concret et point de départ

Cette fiche permet d'expliquer les décisions du RandomForest de maintenance prédictive avec **SHAP**, de
lire un summary plot et un waterfall, et de distinguer une lecture d'**importance** (corrélation) d'une
preuve de **causalité**. Le module de référence est
[`src/indusense/fault/explain.py`](../../../src/indusense/fault/explain.py) (TP B7).

**Prérequis.** Disposer d'un modèle à base d'arbres déjà entraîné (ici, le pipeline
`imputation + RandomForestClassifier`) et d'un échantillon de features dans le même espace que
l'entraînement.

## 1. Principe : une contribution par feature, par rapport à une valeur de base

SHAP (*SHapley Additive exPlanations*) attribue à chaque feature d'une prédiction une contribution signée :
la somme de la valeur de base (la prédiction moyenne sur l'échantillon de référence) et de toutes les
contributions égale la prédiction réelle pour cette observation. Une contribution positive pousse vers la
classe positive (panne), une contribution négative pousse vers l'absence de panne.

## 2. `TreeExplainer` : exact et rapide pour un modèle à base d'arbres

`shap.TreeExplainer` exploite la structure interne des arbres (chemins de décision, comptages par feuille)
pour calculer les valeurs SHAP **exactement**, sans les approximer par échantillonnage. C'est plus rapide et
plus fiable que `KernelExplainer` (agnostique à tout modèle, mais approximatif et coûteux) pour un
RandomForest ou un modèle de boosting.

```python
import shap

explainer = shap.TreeExplainer(pipeline.named_steps["model"])
explanation = explainer(X_imputed)  # shap.Explanation, shape (n_samples, n_features, n_classes)
```

**Point de vigilance : l'imputation.** `TreeExplainer` explique le modèle d'arbres, pas le `SimpleImputer`
qui le précède dans le pipeline. Il faut donc lui donner des features **déjà imputées**
(`pipeline.named_steps["imputation"].transform(X)`), dans le même espace que celui vu par `.fit()`.

**Point de vigilance : la classe expliquée.** Pour un classifieur binaire, `explainer(X)` renvoie une valeur
par classe (`shape[-1] == 2`). La classe qui intéresse le métier est la classe positive (panne, index `1`) :
`explanation.values[..., 1]`. Oublier cette sélection mélangerait les contributions des deux classes.

## 3. Vue globale : summary plot (beeswarm)

```python
shap.plots.beeswarm(explanation)
```

Chaque point est une observation ; sa position horizontale est sa contribution SHAP, sa couleur la valeur de
la feature (rouge = élevée, bleu = faible). Les features sont classées par impact moyen absolu décroissant.
Lecture réellement observée sur le TP B7 (section 8) : pour `incident_count_prev_24h`, les points bleus
(peu ou pas d'incident récent) se resserrent près de zéro tandis que les points rouges (plusieurs incidents
récents) s'étalent vers des SHAP positifs — un historique d'incidents récent pousse vers la panne. Pour
`hours_since_last_incident`, c'est l'inverse : les points bleus (incident très récent, valeur basse) sont
ceux qui s'étalent vers des SHAP positifs, les points rouges (dernier incident lointain) restent proches de
zéro — un incident récent pousse aussi vers la panne, cohérent avec la feature précédente.

`indusense.fault.explain.top_features` calcule un tableau (`impact` = moyenne des `|SHAP|`, `direction` =
signe de la **moyenne signée** sur tout l'échantillon). Cette colonne `direction` est un résumé grossier : sur
une cible rare (peu de pannes), la majorité des observations tire la moyenne du côté négatif même si la
feature pousse fortement vers la panne pour la minorité à risque — visible dans le tableau de la section 8,
où toutes les features affichent `direction = -1` alors que le beeswarm montre bien un étalement positif net
pour certaines valeurs. **Le beeswarm reste la lecture de référence** ; la colonne `direction` sert tout au
plus de repère rapide, pas de substitut.

## 4. Vue locale : waterfall

```python
shap.plots.waterfall(explanation[position])
```

Un waterfall décompose **une seule prédiction** : il part de la valeur de base, ajoute ou retranche la
contribution de chaque feature (les plus impactantes en premier), et arrive à la prédiction finale. C'est la
vue à confronter à l'intuition métier sur un cas précis (« pourquoi *cette* machine-heure a-t-elle été
flaguée ? »), pas sur l'ensemble du jeu de données.

## 5. Dependence plots : lire une seule feature en détail

```python
shap.plots.scatter(explanation[:, "incident_count_prev_24h"])
```

Un dependence plot trace, pour une feature donnée, sa valeur en abscisse et sa contribution SHAP en
ordonnée : il révèle si la relation est monotone, en seuil, ou plus complexe (SHAP capture des interactions
que la seule corrélation linéaire ne montre pas).

## 6. Importance ≠ causalité

SHAP décrit **ce que le modèle utilise** pour décider, pas la cause réelle d'une panne. Une feature très
corrélée à la cible peut résulter d'une fuite de données (elle encode indirectement le futur) plutôt que
d'un mécanisme causal réel. **Une feature anormalement dominante doit alerter**, pas rassurer : elle appelle
une vérification anti-fuite (la feature dépend-elle de données disponibles avant la fenêtre de prédiction ?),
à rapprocher de la checklist du Gold dataset.

## 7. Diagnostic concentré vs diffus

`indusense.fault.explain.top_features` permet de calculer la part de l'impact total portée par la feature
n°1 (`top.iloc[0]["impact"] / top["impact"].sum()`). Une valeur élevée (ex. > 35 %) signale un impact
**concentré** sur peu de features — un signal fort et localisé. Une valeur plus faible signale un impact
**diffus** sur de nombreuses features faibles — cohérent avec l'avertissement de la consigne B7 : sur ce
jeu de maintenance, les features sont globalement peu déterminantes.

## 8. Résultat réellement observé (TP B7, notebook `08-optimisation-carbone-explicabilite.ipynb`)

Sur un échantillon de 1000 lignes de validation, expliquant le modèle **tuné** (AP CV 0,5657, retenu car il
bat la baseline de +0,0081), le top 5 des features par impact SHAP moyen absolu était :

| Feature | Impact moyen \|SHAP\| | Direction (moyenne signée) |
| --- | --- | --- |
| `incident_count_prev_24h` | 0,0731 | -1 (voir nuance section 3 : le beeswarm montre un étalement positif net pour les valeurs hautes) |
| `hours_since_last_incident` | 0,0702 | -1 (idem : étalement positif net pour les valeurs basses) |
| `temp_mean_24h` | 0,0249 | -1 |
| `incident_count_prev_7d` | 0,0229 | -1 |
| `temp_max_24h` | 0,0205 | -1 |

Les features en tête (historique récent d'incidents, température) sont **plausibles métier** : une machine
qui a déjà eu des incidents récents ou une température élevée est un candidat raisonnable à une panne future.
Les deux premières features (0,0731 et 0,0702) dominent nettement les suivantes (0,0249, 0,0229...), mais la
feature n°1 ne pèse que **29,0 %** de la somme des dix impacts du tableau : le diagnostic calculé
(`top['impact'].iloc[0] / top['impact'].sum()`) va dans le sens d'un impact **diffus** plutôt que concentré
sur une seule feature, cohérent avec l'avertissement de la consigne sur ce jeu de données.

## 9. Erreurs fréquentes et bonnes pratiques

- **Expliquer le pipeline entier au lieu du modèle d'arbres** : passer l'imputeur à `TreeExplainer` échoue
  ou produit un résultat incohérent ; toujours extraire l'étape `model` et pré-imputer les features à la main.
- **Oublier la sélection de classe** : pour un classifieur binaire, ne pas indexer `[..., 1]` mélange les
  deux classes dans les figures.
- **Lire une feature dominante comme une confirmation** : elle doit au contraire déclencher une vérification
  anti-fuite.
- **Confondre importance SHAP et importance native du modèle** (`feature_importances_` d'un RandomForest,
  basée sur la réduction d'impureté) : les deux mesures peuvent diverger ; SHAP a l'avantage d'expliquer
  aussi des cas individuels (waterfall), pas seulement une moyenne globale.

## 10. Points à retenir pour le QCM

- `TreeExplainer` calcule des valeurs SHAP exactes pour un modèle à base d'arbres, contrairement à
  `KernelExplainer` (agnostique, approximatif).
- Un summary plot (beeswarm) donne une vue globale ; un waterfall explique une seule prédiction.
- SHAP mesure une contribution au score du modèle, pas une preuve de causalité métier.
- Une feature anormalement dominante doit faire suspecter une fuite de données.

## 11. Points à savoir expliquer lors de la soutenance

- Pourquoi `TreeExplainer` convient à un RandomForest et pas `KernelExplainer` par défaut.
- Comment lire un summary plot et un waterfall, et ce que chacun apporte que l'autre n'apporte pas.
- Pourquoi une feature dominante est un signal d'alerte, pas de confiance.
- Ce que signifie un diagnostic « impact diffus » pour la suite du projet (feature engineering, changement
  d'horizon, ou acceptation d'un modèle modeste).

## Sources officielles

- [SHAP — documentation](https://shap.readthedocs.io/en/latest/)
- [Lundberg & Lee — A Unified Approach to Interpreting Model Predictions](https://www.nature.com/articles/s42256-019-0138-9)

Correspondance exacte avec le référentiel C1 à C9 : à confirmer avec le Kit candidat local.
