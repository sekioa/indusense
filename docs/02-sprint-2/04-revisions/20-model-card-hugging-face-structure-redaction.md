# Model card Hugging Face : structure et rédaction

## Objectif concret et point de départ

Cette fiche explique à quoi sert une **model card**, la structure du **template officiel Hugging Face**,
et comment la remplir honnêtement à partir d'un modèle déjà entraîné et évalué. Exemple réel :
[`docs/02-sprint-2/06-modelcard/README.md`](../06-modelcard/README.md), rédigée pour le RandomForest de
maintenance prédictive (TP B7/B8).

**Point de départ observable.** Le modèle est entraîné, évalué (PR-AUC, F2), mesuré (CodeCarbon) et
expliqué (SHAP) — tout le contenu nécessaire existe déjà dans `indusense.fault` et les fiches 17/18/19. La
model card **assemble** ces éléments dans un format standard, elle ne recalcule rien.

## 1. Pourquoi une model card, et pourquoi un template standard

Un modèle validé mais non documenté pose un problème concret : personne d'autre que son auteur ne sait à
quoi il sert, ce qu'il vaut, ni ce qu'il ne faut pas lui faire faire. Une **model card** répond, sur une
page, aux questions : *que fait ce modèle ? sur quelles données ? avec quelle performance ? dans quelles
limites ? comment l'utiliser ?*

Utiliser le **template officiel Hugging Face** plutôt qu'un format maison a un avantage direct : c'est un
format que la communauté ML reconnaît déjà (sections identiques d'un modèle à l'autre sur le Hub), ce qui
facilite la lecture par un tiers — client, auditeur, futur mainteneur — sans qu'il ait à apprendre une
nouvelle convention.

## 2. Structure du template et rôle de chaque section

Le template (`modelcard_template.md`, chargé dynamiquement par `huggingface_hub`) est un fichier Markdown
avec des champs `{{ variable }}` à remplacer. Sections principales :

| Section | Répond à |
| --- | --- |
| **Model Details** | Qui a entraîné le modèle, quel type de modèle, quelle licence ? |
| **Uses** (Direct / Downstream / Out-of-Scope) | Pour qui et pour quoi ce modèle a-t-il été pensé — et pour quoi surtout **pas** ? |
| **Bias, Risks, and Limitations** + **Recommendations** | Qu'est-ce qui peut mal tourner, et que doit faire un utilisateur pour s'en prémunir ? |
| **How to Get Started** | Comment charger et appeler le modèle, concrètement ? |
| **Training Details** (Training Data, Training Procedure, Speeds/Sizes/Times) | Sur quoi et comment le modèle a-t-il été entraîné ? |
| **Evaluation** (Testing Data/Factors/Metrics, Results, Summary) | Quelle performance, mesurée comment, et que retenir en une phrase ? |
| **Model Examination** | Que peut-on dire de ce que le modèle a appris (explicabilité) ? |
| **Environmental Impact** | Combien ce modèle a-t-il coûté en énergie et en émissions ? |
| **Technical Specifications** | Quelle architecture, quelle infrastructure de calcul ? |
| **Citation, Glossary, More Information, Model Card Authors/Contact** | Où creuser, à qui s'adresser ? |

Les sections marquées **[optional]** peuvent rester à `[More Information Needed]` pour une v1 ; les
sections obligatoires (Model Details, Uses, Bias/Risks/Limitations, Training Details, Evaluation) doivent
être renseignées.

`huggingface_hub` peut générer ce squelette automatiquement :

```python
from huggingface_hub import ModelCard
card = ModelCard.from_template(card_data=..., model_id="mon-modele")
```

## 3. Les trois usages : Direct, Downstream, Out-of-Scope

C'est la distinction la plus souvent bâclée, alors qu'elle est centrale pour un lecteur non technique :

- **Direct Use** : ce que le modèle fait tel quel, sans autre traitement — ici, produire un score de
  risque de panne à 24h à partir de features télémétriques.
- **Downstream Use** *(optionnel)* : comment ce modèle peut être réutilisé dans un système plus large —
  ici, alimenter un tableau de bord ou un système d'alerte combiné à d'autres signaux.
- **Out-of-Scope Use** : ce que le modèle **ne doit pas** faire — la section la plus importante en
  pratique. Exemple concret (voir la model card) : pas de décision automatique d'arrêt machine sans
  validation humaine (précision ~32-35 % seulement), pas de généralisation présumée à un autre site
  industriel, pas d'usage comme preuve de causalité.

🔎 **Point de réflexion.** Un lecteur non technique comprend-il, à la lecture de ces trois sections, *quand
faire confiance au modèle et quand s'en méfier* ? Si la réponse est non, la section Out-of-Scope Use n'est
pas assez concrète.

## 4. Bias, Risks, and Limitations : documenter honnêtement, pas rassurer

Cette section ne sert pas à défendre le modèle, mais à informer un futur utilisateur. Exemple réel tiré de
la model card Indusense : l'étude Optuna bornée améliore l'AP en validation croisée interne (0,5657 contre
0,5575) mais **ne se confirme pas sur le test** (AP 0,6026 contre 0,6151 pour la baseline manuelle) — ce
qui a conduit à retenir la baseline, plus simple, plutôt que la variante « optimisée ». Documenter cet
écart honnêtement vaut mieux que ne présenter que le résultat qui flatte le modèle : voir aussi le
biais de confirmation évoqué dans la [fiche Optuna](08-optimisation-hyperparametres-et-validation-croisee.md).

Les **Recommendations** qui suivent doivent être actionnables : pas « soyez prudents », mais par exemple
« toute alerte doit être confirmée par un technicien avant action sur la machine ».

## 5. Réutiliser un travail déjà fait, ne rien recalculer

Une model card ne doit contenir aucun résultat qui n'existe pas déjà ailleurs :

- **Evaluation** reprend les métriques déjà calculées par `indusense.fault.evaluate` (PR-AUC, ROC-AUC,
  précision/rappel/F2 au seuil retenu) — jamais un nouveau calcul ad hoc.
- **Environmental Impact** reprend la mesure CodeCarbon déjà produite par `indusense.fault.carbon` (voir
  [fiche 17](17-codecarbon-eco-conception-entrainements-ml.md)) : durée, kWh, gCO2eq, matériel utilisé.
- **Model Examination** reprend l'analyse SHAP déjà produite par `indusense.fault.explain` (voir
  [fiche 18](18-explicabilite-shap-treeexplainer.md)) : top features, direction, diagnostic diffus/concentré.

Cette réutilisation illustre directement la valeur de l'industrialisation du Chantier 2 du TP B7 (voir
[fiche 19](19-architecture-notebook-src-scripts-industrialisation.md)) : une fois la logique dans `src/`,
rédiger un livrable de documentation devient un exercice d'assemblage, pas de recalcul.

## 6. Erreurs fréquentes et bonnes pratiques

- **Ne remplir que Model Details et Evaluation** en laissant Out-of-Scope Use et Bias/Risks/Limitations
  vides : c'est l'inverse de la priorité attendue (ces sections protègent l'utilisateur, pas l'auteur).
- **Confondre le modèle finalement retenu avec le modèle « le plus tuné »** : documenter le modèle qui
  performe réellement le mieux sur données non vues, même si un autre a un meilleur score en validation
  croisée interne (voir section 4).
- **Citer un chiffre de performance sans préciser le jeu et le seuil** : toujours associer une métrique à
  son jeu (validation/test) et, pour précision/rappel/F2, au seuil utilisé.
- **Oublier que le test a déjà été consulté** si c'est le cas : le signaler explicitement plutôt que de
  présenter la métrique de test comme une mesure de généralisation vierge.
- **Improviser la mesure d'impact carbone** au moment de rédiger la fiche plutôt que de réutiliser une
  mesure déjà faite pendant l'entraînement (CodeCarbon doit tourner **pendant** l'entraînement, pas après).

## 7. Points à retenir pour le QCM

- Une model card répond à : usage, données, performance, limites, comment l'utiliser.
- Les trois usages du template HF sont Direct Use, Downstream Use (optionnel) et Out-of-Scope Use.
- Bias, Risks, and Limitations doit être honnête, y compris sur un résultat qui ne va pas dans le sens du
  modèle finalement retenu.
- Les sections marquées [optional] peuvent rester `[More Information Needed]` pour une v1 ; les autres non.

## 8. Points à savoir expliquer lors de la soutenance

- Pourquoi Out-of-Scope Use est souvent la section la plus importante en pratique.
- Comment la model card Indusense justifie de retenir la baseline plutôt que la variante tunée par Optuna.
- Pourquoi une model card ne doit contenir aucun calcul qu'on ne retrouve pas déjà dans le code source ou
  les runs MLflow/CodeCarbon/SHAP.
- Ce qui distingue une model card d'une documentation technique classique (README de code).

## Sources officielles

- [Template officiel Hugging Face — modelcard_template.md](https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/templates/modelcard_template.md)
- [Hugging Face — Model Cards (guide)](https://huggingface.co/docs/hub/model-cards)
- [Mitchell et al. — Model Cards for Model Reporting](https://arxiv.org/abs/1810.03993)
- [Lacoste et al. — Quantifying the Carbon Emissions of Machine Learning](https://arxiv.org/abs/1910.09700)

Correspondance exacte avec le référentiel C1 à C9 : à confirmer avec le Kit candidat local.
