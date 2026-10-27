# Vérifications du modèle projets

## Ajout de l’anglais

Sept tests automatisés passent après l’ajout du bilingue. Ils incluent les routes françaises et anglaises, les URL canoniques, les liens FR | EN équivalents et le refus des traductions incomplètes. Les six pages (deux accueils et quatre pages projets) passent le contrôle des chemins locaux. L’accueil et la page subventions anglais ont été contrôlés à 375 px sans débordement, et l’accueil à 768 et 1440 px. Le changement de langue dans les deux sens sur une page projet a été activé dans le navigateur ; le lien français de l’accueil anglais conserve aussi l’ancre de section. Le visuel anglais des subventions affiche CAD 102,500.

- Dépôt examiné : site statique, publication Pages depuis `main / (root)`, aucun `AGENTS.md` présent. Lecture du README et du guide avant modification.
- Génération et `--check` réussis. Cinq tests automatisés réussis : champs obligatoires et limites, unicité, numéros permanents, champs facultatifs, échappement HTML/JSON, chemins d’images, ordre d’affichage et liens vers deux autres projets sans lien vers soi.
- Rendu navigateur vérifié dans des fenêtres intégrées de largeur 375, 768 et 1440 px. Aucun débordement horizontal dans les pages et cartes contrôlées (largeurs utiles respectives 360, 753, 1425 px, hors barre de défilement de 15 px).
- Essai temporaire avec trois projets et des titres/accroches de longueurs différentes : appels à l’action alignés sur une même rangée à 768 et 1440 px. Ces fiches de test ne sont pas publiées.
- Carte entière activable au clavier, nom accessible égal au titre. Focus `:focus-visible` contrôlé sur la carte et le lien de retour ; contour blanc cassé de 3 px, décalé de 5 px. Activation par Entrée et liens relatifs contrôlés.
- Chargement direct de `projets/site-personnel.html` sous un préfixe local `/boris-zablot/` : visuel chargé (1600 px), retour `../#projets`. URL actuelle conservée.
- Contrastes calculés : texte principal/fond 16,10:1 ; texte secondaire/fond 9,08:1 ; texte secondaire/carte 8,02:1 ; accent textuel rose/fond 6,24:1. Rouge réservé aux accents graphiques et aux grands titres au survol.
- Titres, descriptions, URL canoniques, métadonnées Open Graph/Twitter et données structurées propres à chaque page générée. Les images ont dimensions et alt ; cartes et images complémentaires utilisent `loading="lazy"`.
- Préférence de réduction des animations prise en compte par la règle dédiée de `assets/projects.css` : suppression de la transition et du déplacement des cartes. Pas d’animation JavaScript.
- Aucun ellipsis, line-clamp ou masquage de texte. Le débordement masqué concerne seulement le cadre des visuels et les coins des cartes.
- Le reste de l’accueil est conservé : seule la zone des cartes entre marqueurs et le chargement de la feuille de styles projets sont modifiés.

Les objectifs éditoriaux sont des avertissements, pas une raison d’inventer du contenu : le premier projet garde son titre d’origine de 19 caractères et un article de 343 mots. Les maximums bloquants sont respectés.
