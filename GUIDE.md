# Site personnel de Boris Zablot

Site statique : index.html, assets/style.css, portraits WebP et pages projets générées sans dépendance Python externe.

## Design
Fond anthracite, rouge, grandes typographies condensées, portraits noir et blanc et navigation par sections. Aucun logo ni contenu F1 réutilisé.

## Publication
GitHub Pages depuis main / (root). Adresse : https://zaboubob.github.io/boris-zablot/

## Ajouter un projet

Remplir une fiche JSON dans `content/projects/` et fournir son visuel. Les modèles partagés génèrent les cartes et pages. Voir [le guide des projets](docs/PROJETS.md) et [la fiche prête à remplir](docs/projet-exemple.json).

Commande : `python3 scripts/build_projects.py`. La génération est aussi intégrée au workflow GitHub, en conservant la publication Pages depuis main.

## Contenu
Parcours enrichi depuis le PDF LinkedIn fourni le 27 octobre 2026. Les descriptions tronquées dans le PDF n’ont pas été extrapolées. Le PDF complet, les statistiques privées LinkedIn et les suggestions de contacts ne sont pas publiés.

## Référencement
Titres, descriptions, données Person / sameAs, URL canoniques, sitemap.xml, robots.txt et métadonnées sociales. En cas de changement de domaine, remplacer les URL absolues dans ces fichiers. Ajouter le site à LinkedIn et vérifier la propriété dans Google Search Console pour demander l’indexation. Aucun classement garanti.

## Polices
Barlow et Barlow Condensed via Google Fonts, avec polices de secours locales.

