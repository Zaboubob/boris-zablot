#!/usr/bin/env python3
"""Generate project HTML with Python's standard library; no browser JS required."""
import argparse
import html
import json
import re
import sys
from pathlib import Path
from string import Template
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://zaboubob.github.io/boris-zablot/'
START = '<!-- PROJECTS:START -->'
END = '<!-- PROJECTS:END -->'
SECTION_NAMES = {'start': 'Le point de départ', 'objective': 'L’objectif',
                 'approach': 'La démarche', 'outcome': 'Le bilan & la suite'}
STATUSES = {'En cours', 'Terminé', 'En pause'}
MANIFEST = ROOT / 'content/project-registry.json'


def esc(value):
    return html.escape(str(value), quote=True)


def load_json(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (ValueError, OSError) as exc:
        raise ValueError(f'{path.relative_to(ROOT)}: {exc}') from exc


def _validate_content(projects, registry):
    errors, warnings = [], []
    seen = {key: set() for key in ('id', 'number', 'slug')}
    for project in projects:
        name = project.get('id') or project.get('_source', '?')
        def error(message):
            errors.append(f'{name}: {message}')
        def text(key, maximum=None, target=None):
            value = project.get(key)
            if not isinstance(value, str) or not value.strip():
                error(f'champ obligatoire « {key} » manquant ou vide')
                return
            if value != value.strip():
                error(f'{key}: retirer les espaces de début/fin')
            if maximum and len(value) > maximum:
                error(f'{key}: {len(value)} caractères, maximum {maximum} (espaces compris)')
            if target and not target[0] <= len(value) <= target[1]:
                warnings.append(f'{name}: {key} = {len(value)} caractères ; cible {target[0]}–{target[1]}')
        for key in ('id', 'slug'):
            text(key)
            value = project.get(key)
            if isinstance(value, str) and not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', value):
                error(f'{key}: utiliser des lettres minuscules ASCII, chiffres et tirets')
        for key in ('number', 'order'):
            value = project.get(key)
            if type(value) is not int or (key == 'number' and not 1 <= value <= 999):
                error(f'{key}: entier obligatoire' + (' entre 1 et 999' if key == 'number' else ''))
        for key in seen:
            value = project.get(key)
            if not isinstance(value, (str, int)):
                continue
            if value in seen[key]:
                error(f'{key} en double : {value}')
            seen[key].add(value)
        text('title', 60, (25, 45))
        text('category', 30)
        text('teaser', 170, (100, 150))
        text('chapo', 240, (140, 240))
        if project.get('status') not in STATUSES:
            error('status doit être En cours, Terminé ou En pause')
        for key in ('role', 'period'):
            if project.get(key) is not None and (not isinstance(project[key], str) or not project[key].strip()):
                error(f'{key}: omettre le champ plutôt que laisser du texte vide')
        domains = project.get('domains')
        if domains is not None and (not isinstance(domains, list) or not domains or any(not isinstance(x, str) or not x.strip() for x in domains)):
            error('domains: liste non vide de textes, ou champ omis')

        def image(value, key):
            if not isinstance(value, dict):
                error(f'{key}: objet image obligatoire')
                return
            src = value.get('src', '')
            if not isinstance(src, str) or not re.fullmatch(r'assets/[a-zA-Z0-9_./-]+\.(webp|png|jpe?g|avif)', src) or '..' in src.split('/'):
                error(f'{key}.src: chemin local sûr dans assets/, format webp, png, jpg ou avif')
            elif not (ROOT / src).is_file():
                error(f'{key}.src: fichier introuvable : {src}')
            if not isinstance(value.get('alt'), str) or not value['alt'].strip():
                error(f'{key}.alt: texte alternatif obligatoire')
            for dimension in ('width', 'height'):
                if type(value.get(dimension)) is not int or value[dimension] <= 0:
                    error(f'{key}.{dimension}: dimension réelle positive obligatoire')
            focal = value.get('focal', [50, 50])
            if not isinstance(focal, list) or len(focal) != 2 or any(type(n) not in (float, int) or not 0 <= n <= 100 for n in focal):
                error(f'{key}.focal: deux nombres de 0 à 100')
        image(project.get('image'), 'image')
        if project.get('hero_image') is not None:
            image(project['hero_image'], 'hero_image')
        extra = project.get('additional_image')
        if extra is not None:
            image(extra, 'additional_image')
            if not isinstance(extra, dict) or not isinstance(extra.get('caption'), str) or not extra['caption'].strip():
                error('additional_image.caption: légende obligatoire lorsque le visuel est présent')
        highlight = project.get('highlight')
        if highlight is not None and (not isinstance(highlight, dict) or any(not isinstance(highlight.get(k), str) or not highlight[k].strip() for k in ('title', 'text'))):
            error('highlight: title et text obligatoires si présent')
        sections = project.get('sections')
        words = 0
        if not isinstance(sections, dict):
            error('sections: les quatre sections sont obligatoires')
        else:
            for key in SECTION_NAMES:
                blocks = sections.get(key)
                if not isinstance(blocks, list) or not blocks:
                    error(f'sections.{key}: liste de blocs non vide obligatoire')
                    continue
                for block in blocks:
                    if not isinstance(block, dict):
                        error(f'sections.{key}: bloc invalide')
                    elif block.get('type') == 'paragraph' and isinstance(block.get('text'), str) and block['text'].strip():
                        words += len(block['text'].split())
                    elif block.get('type') == 'list' and isinstance(block.get('items'), list) and block['items'] and all(isinstance(x, str) and x.strip() for x in block['items']):
                        words += sum(len(x.split()) for x in block['items'])
                    else:
                        error(f'sections.{key}: utiliser paragraph/text ou list/items non vides')
            if not 350 <= words <= 600:
                warnings.append(f'{name}: article = {words} mots ; cible indicative 350–600, ne pas ajouter de remplissage')
        permanent = registry.get('identities', {})
        if isinstance(project.get('id'), str) and project['id'] in permanent and permanent[project['id']] != project.get('number'):
            error('numéro permanent modifié : conserver le numéro enregistré')
        for old_id, number in permanent.items():
            if number == project.get('number') and old_id != project.get('id'):
                error(f'numéro déjà réservé à {old_id}, même si ce projet a été retiré')
    return errors, warnings


def render_image(image, prefix='', lazy=False):
    x, y = image.get('focal', [50, 50])
    loading = 'loading="lazy"' if lazy else 'fetchpriority="high"'
    return (f'<img src="{esc(prefix + image["src"])}" alt="{esc(image["alt"])}" '
            f'width="{image["width"]}" height="{image["height"]}" {loading} decoding="async" '
            f'style="object-position:{x}% {y}%">')


def render_blocks(blocks):
    output = []
    for block in blocks:
        if block['type'] == 'paragraph':
            output.append(f'<p>{esc(block["text"])}</p>')
        else:
            output.append('<ul>' + ''.join(f'<li>{esc(x)}</li>' for x in block['items']) + '</ul>')
    return '\n'.join(output)


def localize(project, language='en'):
    translation = project[language]
    localized = {key: project[key] for key in ('id', 'number', 'slug', 'order', 'status')}
    for key in ('title', 'category', 'teaser', 'chapo', 'sections'):
        localized[key] = translation[key]
    for key in ('role', 'period', 'domains', 'highlight', 'additional_image', 'hero_image'):
        if translation.get(key) is not None:
            localized[key] = translation[key]
    localized['image'] = dict(project['image'], alt=translation['image_alt'])
    if translation.get('image_src'):
        localized['image']['src'] = translation['image_src']
    return localized


def validate(projects, registry):
    errors, warnings = _validate_content(projects, registry)
    for language in ('en', 'es'):
        for project in projects:
            if language not in project:
                warnings.append(f'{project.get("id", "?")}: traduction {language} absente')
                continue
            translation = project[language]
            if not isinstance(translation, dict):
                errors.append(f'{project.get("id", "?")}: {language} doit être un objet')
                continue
            missing = [k for k in ('title', 'category', 'teaser', 'chapo', 'sections', 'image_alt') if not translation.get(k)]
            missing += [k for k in ('role', 'period', 'domains', 'highlight', 'additional_image', 'hero_image') if project.get(k) and not translation.get(k)]
            if missing:
                errors.append(f'{project.get("id", "?")}: champs {language} manquants : {", ".join(missing)}')
                continue
            e, w = _validate_content([localize(project, language)], {})
            errors.extend(language.upper() + ': ' + x for x in e)
            warnings.extend(language.upper() + ': ' + x for x in w)
    return errors, warnings


def language_switch(language, fr_href, en_href, es_href=None):
    links = []
    for lang, href, label in [('fr', fr_href, 'Lire cette page en français'), ('en', en_href, 'Read this page in English'), ('es', es_href, 'Leer esta página en español')]:
        if not href:
            continue
        links.append(f'<span lang="{lang}" aria-current="page">{lang.upper()}</span>' if language == lang else f'<a lang="{lang}" hreflang="{lang}" href="{esc(href)}" aria-label="{label}">{lang.upper()}</a>')
    return '<span class="language-switch" aria-label="Langue / Language / Idioma">' + '<span aria-hidden="true">|</span>'.join(links) + '</span>'


def alternates(fr_path, en_path=None, es_path=None):
    links = ''.join(f'<link rel="alternate" hreflang="{lang}" href="{BASE}{path}">' for lang, path in [('fr', fr_path), ('en', en_path), ('es', es_path)] if path is not None)
    return links + f'<link rel="alternate" hreflang="x-default" href="{BASE}{fr_path}">'


def _generate_locale(projects, registry, language='fr', translated_ids=None):
    english = language != 'fr'
    spanish = language == 'es'
    prefix = '../../' if english else '../'
    directory = f'{language}/projects' if english else 'projets'
    sections = {'start': 'The starting point', 'objective': 'The goal', 'approach': 'The approach', 'outcome': 'Results & next steps'} if english else SECTION_NAMES
    labels = {
        'language': language, 'locale': 'en_CA' if english else 'fr_CA', 'asset_prefix': prefix,
        'discover_label': 'Discover the project' if english else 'Découvrir le projet',
        'skip_label': 'Skip to content' if english else 'Aller au contenu',
        'home_label': 'Boris Zablot — Home' if english else 'Boris Zablot — Accueil',
        'navigation_label': 'Main navigation' if english else 'Navigation principale',
        'all_projects_label': '← All projects' if english else '← Tous les projets',
        'article_label': 'About this project' if english else 'Présentation du projet',
        'continue_label': 'Keep exploring' if english else 'Continuer la découverte',
        'return_label': 'Back to projects' if english else 'Retour aux projets',
        'back_home_label': 'Back to home' if english else 'Retour à l’accueil'
    }
    if spanish:
        sections = {'start': 'El punto de partida', 'objective': 'El objetivo', 'approach': 'El proceso', 'outcome': 'Balance y próximos pasos'}
        labels.update(locale='es_CA', discover_label='Descubrir el proyecto', skip_label='Ir al contenido', home_label='Boris Zablot — Inicio', navigation_label='Navegación principal', all_projects_label='← Todos los proyectos', article_label='Presentación del proyecto', continue_label='Seguir explorando', return_label='Volver a los proyectos', back_home_label='Volver al inicio')
    card_template = Template((ROOT / 'templates/project-card.html').read_text(encoding='utf-8'))
    page_template = Template((ROOT / 'templates/project.html').read_text(encoding='utf-8'))
    cards, output = [], {}
    for project in projects:
        common = {k: esc(project[k]) for k in ('id', 'category', 'status', 'title')}
        if english:
            common['status'] = {'En cours': 'In progress', 'Terminé': 'Completed', 'En pause': 'On hold'}[project['status']]
        if spanish:
            common['status'] = {'En cours': 'En curso', 'Terminé': 'Finalizado', 'En pause': 'En pausa'}[project['status']]
        common['number'] = f'{"Proyecto" if spanish else "Project" if english else "Projet"} {project["number"]:03d}'
        path = f'{directory}/{project["slug"]}.html'
        card_path = f'projects/{project["slug"]}.html' if english else path
        cards.append(card_template.substitute(**common, url=card_path, teaser=esc(project['teaser']), discover_label=labels['discover_label'],
                                              image=render_image(project['image'], '../' if english else '', lazy=False)))
        facts = []
        for label, value in [('Mi función' if spanish else 'My role' if english else 'Mon rôle', project.get('role')), ('Período' if spanish else 'Period' if english else 'Période', project.get('period')),
                             ('Herramientas y ámbitos' if spanish else 'Tools & areas' if english else 'Outils & domaines', ' · '.join(project.get('domains') or []))]:
            if value:
                facts.append(f'<div><dt>{label}</dt><dd>{esc(value)}</dd></div>')
        facts_html = '<dl class="project-facts shell">' + ''.join(facts) + '</dl>' if facts else ''
        article = '\n'.join(f'<section aria-labelledby="section-{key}"><h2 id="section-{key}">{esc(label)}</h2>{render_blocks(project["sections"][key])}</section>' for key, label in sections.items())
        related = [p for p in projects if p['id'] != project['id']][:2]
        related_html = ''
        if related:
            links = ''.join(f'<a href="{esc(p["slug"])}.html"><span>{esc(p["title"])}</span><span aria-hidden="true">↗</span></a>' for p in related)
            related_html = '<div class="project-related"><h2>' + ('Descubre otros proyectos' if spanish else 'Explore another project' if english else 'À découvrir aussi') + '</h2><div class="project-related-links">' + links + '</div></div>'
        extra = project.get('additional_image')
        extra_html = '<figure class="project-extra">' + render_image(extra, prefix, True) + f'<figcaption>{esc(extra["caption"])}</figcaption></figure>' if extra else ''
        highlight = project.get('highlight')
        highlight_html = f'<aside class="project-highlight"><h2>{esc(highlight["title"])}</h2><p>{esc(highlight["text"])}</p></aside>' if highlight else ''
        hero = project.get('hero_image') or project['image']
        title = project['title'] + (' — Proyecto de Boris Zablot' if spanish else ' — A project by Boris Zablot' if english else ' — Projet de Boris Zablot')
        structured_data = json.dumps({'@context': 'https://schema.org', '@type': 'CreativeWork',
            'name': project['title'], 'description': project['chapo'], 'url': BASE + path,
            'image': BASE + hero['src'], 'inLanguage': language, 'author': {'@type': 'Person', 'name': 'Boris Zablot'}}, ensure_ascii=False).replace('<', '\\u003c')
        fr_path = f'projets/{project["slug"]}.html'
        en_path = f'en/projects/{project["slug"]}.html'
        es_path = f'es/projects/{project["slug"]}.html'
        available = translated_ids or {}
        has_en = language == 'en' or project['id'] in available.get('en', set())
        has_es = spanish or project['id'] in available.get('es', set())
        switch = language_switch(language, prefix + fr_path, prefix + en_path if has_en else prefix + 'en/#projets', prefix + es_path if has_es else prefix + 'es/#projets')
        output[path] = page_template.substitute(**common, **labels, page_title=esc(title), language_switch=switch,
            alternate_links=alternates(fr_path, en_path if has_en else None, es_path if has_es else None),
            description=esc(project['chapo']), canonical=BASE+path, chapo=esc(project['chapo']),
            share_image=esc(BASE+hero['src']), share_alt=esc(hero['alt']), share_width=hero['width'], share_height=hero['height'],
            hero_image=render_image(hero, prefix), facts=facts_html, article=article, additional_figure=extra_html,
            highlight=highlight_html, related=related_html, structured_data=structured_data)
    home = (ROOT / (f'templates/home-{language}.html' if english else 'index.html')).read_text(encoding='utf-8')
    if home.count(START) != 1 or home.count(END) != 1:
        raise ValueError('index.html: les marqueurs PROJECTS sont absents ou en double')
    before, rest = home.split(START)
    _, after = rest.split(END)
    note = ''
    if len(projects) == 1:
        note = '<div class="project-note"><p class="eyebrow">La suite se construit</p><h3>Explorer.<br>Expérimenter.<br>Partager.</h3><p>Cet espace évoluera au fil de mes projets. Chaque page permettra d’en découvrir le contexte, la démarche et les apprentissages.</p></div>'
        if english:
            note = '<div class="project-note"><p class="eyebrow">More to come</p><h3>Explore.<br>Experiment.<br>Share.</h3><p>This space will grow with my projects, sharing their context, approach and lessons learned.</p></div>'
    if spanish and len(projects) == 1:
        note = '<div class="project-note"><p class="eyebrow">La historia continúa</p><h3>Explorar.<br>Experimentar.<br>Compartir.</h3><p>Este espacio crecerá con mis proyectos, compartiendo su contexto, su proceso y sus aprendizajes.</p></div>'
    carousel_template = Template((ROOT / 'templates/project-carousel.html').read_text(encoding='utf-8'))
    carousel = carousel_template.substitute(
        cards='\n'.join(cards),
        gallery_label='Proyectos' if spanish else 'Projects' if english else 'Projets',
        previous_label='Anterior' if spanish else 'Previous' if english else 'Précédent',
        next_label='Siguiente' if spanish else 'Next' if english else 'Suivant',
        hint='Desliza o usa las flechas para explorar' if spanish else 'Swipe or use the arrows to explore' if english else 'Faites défiler pour découvrir les projets',
        script_prefix='../' if english else '')
    output[f'{language}/index.html' if english else 'index.html'] = before + START + '\n' + carousel + note + '\n' + END + after
    urls = [BASE] + [BASE + f'projets/{p["slug"]}.html' for p in projects]
    output['sitemap.xml'] = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + '\n'.join(f'  <url><loc>{xml_escape(url)}</loc></url>' for url in urls) + '\n</urlset>\n'
    identities = dict(registry.get('identities', {}))
    identities.update({p['id']: p['number'] for p in projects})
    output['content/project-registry.json'] = json.dumps({'identities': identities, 'pages': [f'projets/{p["slug"]}.html' for p in projects]}, indent=2, ensure_ascii=False) + '\n'
    return output


def generate(projects, registry):
    translations = {lang: [localize(p, lang) for p in projects if p.get(lang)] for lang in ('en', 'es')}
    available = {lang: {p['id'] for p in items} for lang, items in translations.items()}
    output = _generate_locale(projects, registry, translated_ids=available)
    for lang, items in translations.items():
        for path, content in _generate_locale(items, registry, lang, available).items():
            if path not in ('sitemap.xml', 'content/project-registry.json'):
                output[path] = content
    groups = [{'fr': '', 'en': 'en/', 'es': 'es/'}]
    for p in projects:
        groups.append({'fr': f'projets/{p["slug"]}.html', **{lang: f'{lang}/projects/{p["slug"]}.html' for lang in translations if p['id'] in available[lang]}})
    entries = []
    for group in groups:
        links = ''.join(f'<xhtml:link rel="alternate" hreflang="{lang}" href="{BASE}{path}"/>' for lang, path in group.items())
        links += f'<xhtml:link rel="alternate" hreflang="x-default" href="{BASE}{group["fr"]}"/>'
        for path in group.values():
            entries.append(f'  <url><loc>{xml_escape(BASE + path)}</loc>{links}</url>')
    output['sitemap.xml'] = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + '\n'.join(entries) + '\n</urlset>\n'
    identities = dict(registry.get('identities', {}))
    identities.update({p['id']: p['number'] for p in projects})
    pages = [f'projets/{p["slug"]}.html' for p in projects] + [f'{lang}/projects/{p["slug"]}.html' for lang, items in translations.items() for p in items]
    output['content/project-registry.json'] = json.dumps({'identities': identities, 'pages': pages}, ensure_ascii=False, indent=2) + '\n'
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Vérifier les sorties sans écrire')
    parser.add_argument('--validate', action='store_true', help='Valider les fiches seulement')
    args = parser.parse_args()
    try:
        projects = []
        for file in sorted((ROOT / 'content/projects').glob('*.json')):
            project = load_json(file)
            if not isinstance(project, dict):
                raise ValueError(f'{file.name}: objet JSON attendu')
            project['_source'] = file.name
            projects.append(project)
        if not projects:
            raise ValueError('Aucune fiche dans content/projects/')
        registry = load_json(MANIFEST) if MANIFEST.exists() else {}
        errors, warnings = validate(projects, registry)
        for warning in warnings:
            print('AVERTISSEMENT:', warning, file=sys.stderr)
        if errors:
            raise ValueError('\n'.join(errors))
        if args.validate:
            print(f'OK : {len(projects)} fiche(s) valide(s)')
            return 0
        projects.sort(key=lambda p: (p['order'], p['number']))
        output = generate(projects, registry)
        stale = [path for path in registry.get('pages', []) if path not in output]
        changed = [path for path, value in output.items() if not (ROOT / path).exists() or (ROOT / path).read_text(encoding='utf-8') != value]
        if args.check:
            if changed or stale:
                raise ValueError('Sorties à régénérer : ' + ', '.join(changed + stale) + '\nExécuter python3 scripts/build_projects.py')
        else:
            for path in changed:
                (ROOT / path).parent.mkdir(parents=True, exist_ok=True)
                (ROOT / path).write_text(output[path], encoding='utf-8')
            for path in stale:
                # Remove only known generated project pages, never arbitrary paths.
                if re.fullmatch(r'(?:projets|en/projects|es/projects)/[a-z0-9-]+\.html', path):
                    (ROOT / path).unlink(missing_ok=True)
        print(f'OK : {len(projects)} projet(s), {len(changed)} fichier(s) à jour' if not args.check else 'OK : HTML généré synchronisé')
        return 0
    except (ValueError, KeyError, OSError) as exc:
        print('ERREUR:', exc, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
