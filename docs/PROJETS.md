# Ajouter un projet

## Versions française et anglaise

Le français reste à la racine ; l’anglais se trouve sous `en/`. Chaque fiche peut contenir un objet `en` : `title`, `category`, `teaser`, `chapo`, `sections` et `image_alt` sont alors obligatoires. Traduire aussi `role`, `period`, `domains`, `highlight`, `additional_image` et `hero_image` lorsqu’ils sont présents en français. Les identifiants, numéro, ordre, statut métier et slug sont communs aux deux langues ; le statut et les libellés de navigation sont traduits automatiquement.

`en.image_src` permet de fournir un visuel traduit de mêmes dimensions que le visuel français. Sinon, l’image est partagée et seul son texte alternatif est traduit. La fiche `subventions-2026.json` constitue un exemple bilingue complet.

Les modèles partagés produisent `projets/<slug>.html` et `en/projects/<slug>.html`. Le sélecteur FR | EN relie exactement les pages équivalentes. Sans traduction, le projet n’est pas ajouté au catalogue anglais et le lien EN mène à ce catalogue plutôt qu’à une URL inexistante. Les fiches anglaises incomplètes bloquent la génération. Les URL canoniques, les liens `hreflang` et le sitemap sont générés pour chaque langue.

L’accueil français reste dans `index.html`. Le contenu éditorial de l’accueil anglais se modifie dans `templates/home-en.html`, puis `python3 scripts/build_projects.py` régénère `en/index.html`. Les marqueurs `PROJECTS` y fonctionnent comme sur l’accueil français. Le script léger `assets/languages.js` conserve l’ancre de section lors d’un changement de langue sur l’accueil ; les liens fonctionnent aussi sans JavaScript. Aucun visiteur n’est redirigé automatiquement selon son navigateur.

Le contenu se trouve dans `content/projects/*.json`. Le générateur Python standard produit les cartes de l’accueil, les pages `projets/<slug>.html` et le sitemap. Les textes et liens sont présents dans le HTML : aucun JavaScript n’est nécessaire.

## En pratique

1. Copier `docs/projet-exemple.json` dans `content/projects/mon-projet.json`. Ce brouillon est volontairement vide : il doit être rempli avant publication. Seules les fiches de `content/projects/` sont publiées.
2. Fournir les informations et les quatre sections, puis déposer le visuel dans `assets/projets/`. Conserver des noms de fichiers simples, sans espaces ni accents.
3. Exécuter `python3 scripts/build_projects.py --validate`, puis `python3 scripts/build_projects.py`. Aucun paquet à installer. Python 3.10 ou ultérieur suffit.
4. Vérifier `python3 scripts/build_projects.py --check`, puis committer la fiche, l’image et les sorties générées. Sur `main`, le workflow fait aussi la génération automatiquement si seules les sources ont été modifiées ; il enregistre les sorties puis demande une reconstruction Pages.

Le déploiement existant reste GitHub Pages depuis `main / (root)`. Le workflow `projects.yml` n’introduit ni hébergeur ni branche de publication supplémentaire. Son appel explicite à l’API Pages est nécessaire car les commits faits avec `GITHUB_TOKEN` ne déclenchent pas eux-mêmes une publication Pages. Aucun secret personnel n’est nécessaire. Les permissions `contents: write` et `pages: write` sont limitées au job de génération sur `main` ; les pull requests restent en lecture seule. Si une règle de protection interdit l’écriture automatique sur `main`, générer localement et inclure les sorties dans la PR.

## Champs

Les limites comptent les espaces et les caractères Unicode. Un dépassement de maximum bloque la génération ; une cible éditoriale non atteinte produit un avertissement, sans couper le texte.

| Champ | Obligatoire | Format / longueur |
| --- | --- | --- |
| `id` | Oui | Identifiant unique et permanent, minuscules ASCII et tirets |
| `number` | Oui | Numéro permanent unique de 1 à 999 ; affiché « Projet 001 » |
| `slug` | Oui | Nom de l’URL sans extension : `mon-projet` |
| `order` | Oui | Entier de classement ; plus petit = plus haut. Indépendant du numéro |
| `title` | Oui | Cible 25–45 caractères, maximum 60 |
| `category` | Oui | Maximum 30 caractères |
| `status` | Oui | `En cours`, `Terminé` ou `En pause` |
| `teaser` | Oui | Accroche de carte : cible 100–150, maximum 170 |
| `chapo` | Oui | Introduction / description : cible 140–240, maximum 240 |
| `image` | Oui | Visuel commun à la carte et à la page, voir ci-dessous |
| `hero_image` | Non | Variante du visuel principal ; même structure que `image` |
| `role` | Non | Votre rôle réel, texte court |
| `period` | Non | Période réelle, texte libre, sans date inventée |
| `domains` | Non | Liste de noms d’outils ou de domaines réellement mobilisés |
| `sections` | Oui | Les quatre listes de blocs : `start`, `objective`, `approach`, `outcome` |
| `additional_image` | Non | Image complémentaire avec `caption` obligatoire si elle est fournie |
| `highlight` | Non | Objet avec `title` et `text`, pour un résultat ou apprentissage réel |

Omettre les champs facultatifs ou garder `null`. Ne pas laisser de chaînes vides, de listes vides ni de texte provisoire. Aucun bloc facultatif absent n’est rendu. Les repères sont limités à trois : rôle, période et outils/domaines. Le premier projet conserve son titre court d’origine (19 caractères) : l’avertissement est volontaire. Son article reste proche de la cible, sans remplissage.

### Textes de l’article

Les quatre rubriques sont rendues automatiquement dans cet ordre :

- `start` → Le point de départ
- `objective` → L’objectif
- `approach` → La démarche
- `outcome` → Le bilan & la suite

Les blocs sont du texte brut, automatiquement échappé. Ne pas écrire de HTML ou de Markdown. Utiliser `{"type":"paragraph","text":"Un paragraphe court."}` ou `{"type":"list","items":["Première action","Seconde action"]}`. Cible : 350–600 mots au total pour l’article ; un avertissement n’oblige jamais à ajouter du contenu fictif.

### Images et cadrage

`image` contient `src`, `alt`, `width`, `height` et, facultativement, `focal`. Exemple :

```json
{"src":"assets/projets/mon-projet.webp","alt":"Description précise du visuel", "width":1600,"height":900,"focal":[60,35]}
```

`width` et `height` sont les dimensions réelles du fichier. `focal` donne le point à garder visible, en pourcentage horizontal puis vertical (0–100 ; centre par défaut : `[50,50]`). Les cartes et couvertures utilisent un cadre 16:9 ; `hero_image` permet de fournir une composition différente pour la page. Les autres images gardent leur ratio naturel. Les images de carte et complémentaires sont chargées en différé ; la couverture est prioritaire.

Préférer WebP/AVIF pour les photos (1600 px de large suffisent souvent ; viser moins de 300 Ko), PNG pour un motif graphique précis. JPEG et PNG sont aussi acceptés. Ne pas convertir une image déjà optimisée à chaque génération. Conserver un vrai texte alternatif ; ne pas utiliser une photographie générique pour combler une absence. Le premier projet utilise le motif BZ. exporté en PNG.

Pour un visuel complémentaire, reprendre les propriétés d’image dans `additional_image` et ajouter `"caption":"Ce que montre cette image."`. Pour un encadré : `"highlight":{"title":"Un apprentissage","text":"Ce que cette démarche m’a appris."}`. N’ajouter ces éléments que s’ils apportent une information réelle.

## Modèles et sorties

- `templates/project-card.html` : structure commune de toutes les cartes.
- `templates/project.html` : structure commune de toutes les pages.
- `assets/projects.css` : styles partagés, limités aux projets.
- `scripts/build_projects.py` : validation, génération et liens vers deux autres projets au maximum.
- `content/project-registry.json` : registre des numéros permanents et des pages générées. Ne pas renuméroter un projet lors d’un changement d’ordre. Un numéro retiré reste réservé.
- `index.html` : seules les balises entre `PROJECTS:START` et `PROJECTS:END` sont générées. Ne pas modifier les cartes directement.
- `projets/*.html` et `sitemap.xml` : sorties versionnées. Modifier les sources puis régénérer.

Un changement de modèle s’applique à tous les projets à la prochaine génération. Le préfixe `/boris-zablot/` est respecté par les liens relatifs. Les URL absolues SEO se basent sur `BASE` dans le générateur ; à adapter en cas de changement de domaine.

Pour retirer un projet, supprimer sa fiche puis relancer la génération : seule son ancienne page enregistrée est supprimée, son numéro reste réservé. Changer un slug change une URL publique : prévoir une redirection si ce cas se présente. Ne pas changer `site-personnel`, dont l’URL existante est conservée.

## Vérifications

`python3 -m unittest discover -s tests` vérifie les erreurs de contenu, les numéros permanents, l’échappement, les chemins, les champs absents, le classement et les liens entre projets. `--check` vérifie que les sorties sont synchronisées. Avant publication, contrôler les cartes et pages à 375, 768 et 1440 px, les liens, le focus au clavier et le cadrage des visuels. Pas de texte coupé ou masqué pour satisfaire les limites.

## Carrousel de l’accueil

Les cartes sont générées dans `templates/project-carousel.html`. `assets/projects.css` organise une piste horizontale avec ancrage des cartes ; `assets/projects.js` ajoute les flèches, désactivées aux extrémités. Le défilement tactile et la barre native restent disponibles sans JavaScript. Au clavier : Tab pour accéder aux cartes et boutons, flèches gauche/droite et Début/Fin sur la piste. Aucune avance automatique ; les déplacements sont instantanés si la réduction des animations est activée. Ajouter un projet ne nécessite aucun changement au carrousel.
