# RGPD, AI Act et données pour l’IA

## Statut de la fiche

Fiche initialisée le 26 août 2026 à partir du programme annoncé, puis enrichie avec les notes sur les principes du RGPD. La partie AI Act est développée dans la fiche dédiée [AI Act européen : approche par les risques et calendrier](ai-act-europeen-risques-et-calendrier.md), vérifiée à partir des sources officielles européennes disponibles au 26 août 2026.

## Définition et objectif

Le **RGPD** (Règlement général sur la protection des données) encadre le traitement des données à caractère personnel. Une donnée personnelle est une information se rapportant à une personne identifiée ou identifiable.

L’**AI Act européen** est un cadre réglementaire consacré aux systèmes d’intelligence artificielle. Pour un projet d’IA traitant des données personnelles, les deux cadres peuvent donc devoir être pris en compte : le RGPD concerne le traitement des données personnelles, tandis que l’AI Act encadre le système d’IA et les obligations associées à son niveau de risque.

## Les sept principes du RGPD

Ces principes encadrent tout le cycle de vie d’un traitement de données personnelles, y compris la constitution d’un dataset et l’utilisation d’un modèle prédictif.

| Principe | Signification | Application à un projet d’IA |
| --- | --- | --- |
| Licéité, loyauté et transparence | Le traitement doit avoir une base légale, ne pas tromper les personnes et leur être expliqué de manière compréhensible. | Informer sur l’utilisation des données pour entraîner ou exploiter le modèle et éviter un usage inattendu. |
| Limitation des finalités | Les objectifs doivent être déterminés, explicites et légitimes ; une réutilisation incompatible est interdite. | Définir précisément la prédiction recherchée avant de collecter ou de réutiliser les données. |
| Minimisation des données | Seules les données adéquates, pertinentes et nécessaires à la finalité sont traitées. | Écarter une colonne qui n’est pas utile au modèle, même si elle est disponible. |
| Exactitude | Les données doivent être exactes et, si nécessaire, tenues à jour ; les erreurs doivent être rectifiées ou supprimées. | Contrôler les valeurs erronées, les libellés incohérents et les données devenues obsolètes avant l’entraînement. |
| Limitation de la conservation | Les données identifiantes ne sont conservées que pendant une durée justifiée par la finalité. | Fixer une durée de conservation pour les sources, datasets intermédiaires et traces contenant des données personnelles. |
| Intégrité et confidentialité | Des mesures techniques et organisationnelles doivent protéger les données contre l’accès illicite, la perte ou l’altération. | Gérer les droits d’accès, sécuriser le stockage et protéger les exports de datasets. |
| Responsabilité (*accountability*) | Le responsable du traitement doit respecter ces principes et pouvoir démontrer cette conformité. | Documenter les finalités, choix de variables, transformations, accès, durées et contrôles réalisés. |

## Ne pas confondre principes et bases légales

Une **base légale** est le fondement juridique qui autorise un traitement de données personnelles. Elle répond à la question : « sur quel fondement avons-nous le droit d’effectuer ce traitement ? »

Le RGPD prévoit six bases légales :

1. le **consentement** de la personne ;
2. le **contrat**, lorsque le traitement est nécessaire à son exécution ou à sa préparation ;
3. l’**obligation légale**, lorsqu’un texte impose le traitement ;
4. la **sauvegarde des intérêts vitaux** d’une personne ;
5. la **mission d’intérêt public** ou l’exercice de l’autorité publique ;
6. l’**intérêt légitime**, sous réserve de ne pas faire prévaloir cet intérêt sur les droits et libertés des personnes.

Le consentement n’est donc pas toujours obligatoire et n’est pas supérieur aux autres bases. Pour une même finalité, il faut déterminer la base légale appropriée avant de commencer le traitement, et non cumuler plusieurs bases « par sécurité ».

Dans les notes manuscrites, l’obligation légale et la sauvegarde des intérêts vitaux sont réunies sous le numéro 3. Elles constituent juridiquement deux bases distinctes, ce qui explique le numéro 4 manquant sur l’image.

## Notions restant à compléter avec le cours

- Les exemples et précisions du formateur sur l’articulation entre le RGPD et l’AI Act.
- La détection et le traitement des données qualifiées de sensibles.
- Le choix d’une méthode rendant des données non identifiables lors de la production du dataset Silver.

## Anonymisation et pseudonymisation

L’**anonymisation** transforme les données de manière à ce que les personnes ne soient plus identifiables, y compris par recoupement raisonnablement possible. Si l’anonymisation est effective, le résultat n’est plus une donnée personnelle.

La **pseudonymisation** remplace un identifiant direct par un pseudonyme ou un code, mais une réidentification reste possible à l’aide d’informations supplémentaires. Les données pseudonymisées restent donc des données personnelles soumises au RGPD.

Supprimer seulement le nom ou remplacer un identifiant par un code ne suffit pas à démontrer une anonymisation : les autres colonnes peuvent permettre une réidentification par recoupement.

## Démarche à appliquer au TP

1. Identifier les colonnes contenant des données personnelles ou qualifiées de sensibles.
2. Déterminer si chaque colonne est réellement nécessaire au cas d’usage.
3. Rechercher les identifiants directs et les combinaisons de quasi-identifiants permettant un recoupement.
4. Choisir une méthode adaptée : suppression, généralisation, agrégation, masquage ou pseudonymisation, selon le besoin.
5. Documenter la transformation et conserver la traçabilité entre Bronze et Silver sans exposer les informations protégées.
6. Vérifier que le Silver reste utile au cas d’usage et évaluer le risque de réidentification restant.

### Décision appliquée au TP incidents-maintenance

Le cas d'usage cherche une relation temporelle entre les incidents et les maintenances des machines. Il ne nécessite aucune analyse par opérateur.

Les colonnes `operator_name`, `operator_badge` et `comment` sont donc supprimées du Silver par application du principe de minimisation. Cette solution est préférable à un simple hash du badge : un identifiant déterministe haché resterait un pseudonyme permettant de suivre la même personne et ne constituerait pas automatiquement une anonymisation.

Le contrôle doit porter sur le fichier Silver réellement exporté, et pas seulement sur le `DataFrame` en mémoire. Il faut relire son en-tête, vérifier l'absence des trois colonnes et confirmer que le nombre de lignes attendu a été conservé.

La présence d'un horodatage précis et d'un identifiant de machine maintient un risque résiduel de recoupement avec une source externe. La formulation rigoureuse est donc « non directement identifiable dans le périmètre du TP », sans prétendre avoir démontré une anonymisation RGPD irréversible.

Un **quasi-identifiant** est une information qui ne nomme pas directement une personne mais peut contribuer à l’identifier lorsqu’elle est combinée à d’autres informations, par exemple un âge précis, une localisation et une date.

## Erreurs fréquentes et bonnes pratiques

- Confondre les sept principes du traitement avec les six bases légales.
- Penser que tout traitement exige le consentement alors qu’il peut reposer sur une autre base légale adaptée.
- Choisir ou modifier la base légale après le début du traitement.
- Confondre anonymisation et pseudonymisation.
- Considérer qu’une donnée est anonyme dès que le nom a été supprimé.
- Conserver des colonnes personnelles « au cas où », sans besoin démontré.
- Transformer les données sans documenter les règles appliquées.
- Évaluer chaque colonne isolément et ignorer les possibilités de réidentification par combinaison.
- Altérer la source Bronze au lieu d’appliquer les transformations dans le niveau Silver.

## Points à retenir pour le QCM

- Le RGPD s’applique aux traitements de données personnelles.
- Les sept principes étudiés sont : licéité, loyauté et transparence ; limitation des finalités ; minimisation ; exactitude ; limitation de la conservation ; intégrité et confidentialité ; responsabilité.
- La licéité suppose de choisir l’une des six bases légales adaptées au traitement.
- Les six bases légales ne constituent pas les sept principes du RGPD.
- Une personne peut être identifiable indirectement, par recoupement de plusieurs informations.
- Les données pseudonymisées restent des données personnelles.
- Une anonymisation doit résister à une réidentification raisonnablement possible.
- Le RGPD et l’AI Act ont des objets différents et peuvent s’appliquer simultanément à un même projet d’IA.

## Points à savoir expliquer lors de la soutenance

- Quelles colonnes présentent un risque pour les personnes et pourquoi.
- Quelle finalité est poursuivie, quelle base légale autorise le traitement et comment ce choix est documenté.
- Comment chacun des sept principes est appliqué au cycle de vie des données et du modèle.
- Pourquoi une méthode d’anonymisation ou de pseudonymisation a été retenue.
- Comment l’utilité des données a été conciliée avec leur protection.
- Comment le risque de réidentification a été évalué.
- Comment les transformations sont tracées entre les datasets Bronze et Silver.

La correspondance exacte avec les compétences C1 à C9 reste à confirmer avec le Kit candidat.

## Sources de vérification

- Notes visuelles communiquées par l’utilisateur le 26 août 2026.
- [CNIL — Chapitre II du RGPD : principes](https://www.cnil.fr/fr/reglement-europeen-protection-donnees/chapitre2)
- [CNIL — La licéité du traitement et les six bases légales](https://www.cnil.fr/fr/les-bases-legales/liceite-essentiel-sur-les-bases-legales)

## Pour aller plus loin

- [CNIL — IA : comment être en conformité avec le RGPD ?](https://www.cnil.fr/fr/intelligence-artificielle/ia-comment-etre-en-conformite-avec-le-rgpd) : démarche pratique appliquée aux projets IA.
- [CNIL — Anonymisation, pseudonymisation et chiffrement](https://www.cnil.fr/fr/lanonymisation-de-donnees-personnelles) : distinguer les protections et leurs limites.
- [AI Act Service Desk](https://ai-act-service-desk.ec.europa.eu/en) : ressource officielle complémentaire pour la partie AI Act.
