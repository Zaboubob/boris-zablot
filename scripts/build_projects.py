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


def validate(projects, registry):
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


def generate(projects, registry):
    card_template = Template((ROOT / 'templates/project-card.html').read_text(encoding='utf-8'))
    page_template = Template((ROOT / 'templates/project.html').read_text(encoding='utf-8'))
    cards, output = [], {}
    for project in projects:
        common = {k: esc(project[k]) for k in ('id', 'category', 'status', 'title')}
        common['number'] = f'Projet {project["number"]:03d}'
        path = f'projets/{project["slug"]}.html'
        cards.append(card_template.substitute(**common, url=path, teaser=esc(project['teaser']),
                                              image=render_image(project['image'], lazy=True)))
        facts = []
        for label, value in [('Mon rôle', project.get('role')), ('Période', project.get('period')),
                             ('Outils & domaines', ' · '.join(project.get('domains') or []))]:
            if value:
                facts.append(f'<div><dt>{label}</dt><dd>{esc(value)}</dd></div>')
        facts_html = '<dl class="project-facts shell">' + ''.join(facts) + '</dl>' if facts else ''
        article = '\n'.join(f'<section aria-labelledby="section-{key}"><h2 id="section-{key}">{esc(label)}</h2>{render_blocks(project["sections"][key])}</section>' for key, label in SECTION_NAMES.items())
        related = [p for p in projects if p['id'] != project['id']][:2]
        related_html = ''
        if related:
            links = ''.join(f'<a href="{esc(p["slug"])}.html"><span>{esc(p["title"])}</span><span aria-hidden="true">↗</span></a>' for p in related)
            related_html = '<div class="project-related"><h2>À découvrir aussi</h2><div class="project-related-links">' + links + '</div></div>'
        extra = project.get('additional_image')
        extra_html = '<figure class="project-extra">' + render_image(extra, '../', True) + f'<figcaption>{esc(extra["caption"])}</figcaption></figure>' if extra else ''
        highlight = project.get('highlight')
        highlight_html = f'<aside class="project-highlight"><h2>{esc(highlight["title"])}</h2><p>{esc(highlight["text"])}</p></aside>' if highlight else ''
        hero = project.get('hero_image') or project['image']
        title = project['title'] + ' — Projet de Boris Zablot'
        structured_data = json.dumps({'@context': 'https://schema.org', '@type': 'CreativeWork',
            'name': project['title'], 'description': project['chapo'], 'url': BASE + path,
            'image': BASE + hero['src'], 'inLanguage': 'fr', 'author': {'@type': 'Person', 'name': 'Boris Zablot'}}, ensure_ascii=False).replace('<', '\\u003c')
        output[path] = page_template.substitute(**common, page_title=esc(title),
            description=esc(project['chapo']), canonical=BASE+path, chapo=esc(project['chapo']),
            share_image=esc(BASE+hero['src']), share_alt=esc(hero['alt']), share_width=hero['width'], share_height=hero['height'],
            hero_image=render_image(hero, '../'), facts=facts_html, article=article, additional_figure=extra_html,
            highlight=highlight_html, related=related_html, structured_data=structured_data)
    home = (ROOT / 'index.html').read_text(encoding='utf-8')
    if home.count(START) != 1 or home.count(END) != 1:
        raise ValueError('index.html: les marqueurs PROJECTS sont absents ou en double')
    before, rest = home.split(START)
    _, after = rest.split(END)
    note = ''
    if len(projects) == 1:
        note = '<div class="project-note"><p class="eyebrow">La suite se construit</p><h3>Explorer.<br>Expérimenter.<br>Partager.</h3><p>Cet espace évoluera au fil de mes projets. Chaque page permettra d’en découvrir le contexte, la démarche et les apprentissages.</p></div>'
    output['index.html'] = before + START + '\n' + '\n'.join(cards) + note + '\n' + END + after
    urls = [BASE] + [BASE + f'projets/{p["slug"]}.html' for p in projects]
    output['sitemap.xml'] = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + '\n'.join(f'  <url><loc>{xml_escape(url)}</loc></url>' for url in urls) + '\n</urlset>\n'
    identities = dict(registry.get('identities', {}))
    identities.update({p['id']: p['number'] for p in projects})
    output['content/project-registry.json'] = json.dumps({'identities': identities, 'pages': [f'projets/{p["slug"]}.html' for p in projects]}, indent=2, ensure_ascii=False) + '\n'
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
                if re.fullmatch(r'projets/[a-z0-9-]+\.html', path):
                    (ROOT / path).unlink(missing_ok=True)
        print(f'OK : {len(projects)} projet(s), {len(changed)} fichier(s) à jour' if not args.check else 'OK : HTML généré synchronisé')
        return 0
    except (ValueError, KeyError, OSError) as exc:
        print('ERREUR:', exc, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
