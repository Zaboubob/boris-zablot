import copy
import importlib.util
import json
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('projects', Path(__file__).resolve().parents[1] / 'scripts/build_projects.py')
build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build)


class Projects(unittest.TestCase):
    def setUp(self):
        self.project = json.loads((build.ROOT / 'content/projects/site-personnel.json').read_text())

    def test_missing_duplicate_and_card_limits(self):
        p = copy.deepcopy(self.project)
        p.pop('title')
        errors, _ = build.validate([p], {})
        self.assertTrue(any('title' in e for e in errors))
        p = copy.deepcopy(self.project)
        p['title'] = 'x' * 61
        p['category'] = 'x' * 31
        p['teaser'] = 'x' * 171
        errors, _ = build.validate([self.project, p], {})
        for key in ('title', 'category', 'teaser', 'id en double', 'slug en double', 'number en double'):
            self.assertTrue(any(key in e for e in errors), key)

    def test_optional_fields_omitted_and_no_self_link(self):
        p = copy.deepcopy(self.project)
        p.pop('role', None)
        p.pop('domains', None)
        self.assertEqual(build.validate([p], {})[0], [])
        page = build.generate([p], {})['projets/site-personnel.html']
        self.assertNotIn('<dl', page)
        self.assertNotIn('project-related', page)
        self.assertNotIn('project-highlight', page)
        self.assertNotIn('project-extra', page)
        self.assertIn('href="../#projets"', page)

    def test_order_does_not_renumber_or_include_self(self):
        ps = [copy.deepcopy(self.project) for _ in range(3)]
        for i, p in enumerate(ps, 1):
            p.update(id=f'projet-{i}', slug=f'projet-{i}', number=i, order=40-i)
        ps.sort(key=lambda p: p['order'])
        output = build.generate(ps, {})
        home = output['index.html']
        self.assertLess(home.index('card-projet-3-title'), home.index('card-projet-1-title'))
        self.assertIn('Projet 003', output['projets/projet-3.html'])
        related = output['projets/projet-1.html'].split('project-related-links')[1]
        self.assertIn('href="projet-2.html"', related)
        self.assertIn('href="projet-3.html"', related)
        self.assertNotIn('href="projet-1.html"', related)
        errors, _ = build.validate([dict(ps[0], number=5)], {'identities': {'projet-3': 3}})
        self.assertTrue(any('permanent' in e for e in errors))
        errors, _ = build.validate([dict(ps[0], id='nouveau')], {'identities': {'ancien': 3}})
        self.assertTrue(any('réservé' in e for e in errors))

    def test_escape_content_and_validate_images(self):
        p = copy.deepcopy(self.project)
        p['title'] = '<script>"&'
        p['sections']['start'][0]['text'] = '<img src=x onerror=alert(1)>'
        page = build.generate([p], {})['projets/site-personnel.html']
        self.assertIn('&lt;script&gt;&quot;&amp;', page)
        self.assertNotIn('<img src=x', page)
        self.assertIn('\\u003cscript', page)
        p['image']['src'] = 'assets/../../secret.webp'
        p['image']['focal'] = [105, 10]
        errors, _ = build.validate([p], {})
        self.assertTrue(any('src' in e for e in errors))
        self.assertTrue(any('focal' in e for e in errors))

    def test_optional_content_and_home_preserved(self):
        p = copy.deepcopy(self.project)
        p['additional_image'] = dict(p['image'], caption='Une légende réelle')
        p['highlight'] = {'title': 'Apprentissage', 'text': 'Un enseignement réel.'}
        self.assertEqual(build.validate([p], {})[0], [])
        output = build.generate([p], {})
        page = output['projets/site-personnel.html']
        self.assertIn('project-extra', page)
        self.assertIn('loading="lazy"', page)
        self.assertIn('Une légende réelle', page)
        self.assertIn('project-highlight', page)
        current = (build.ROOT / 'index.html').read_text()
        self.assertEqual(current.split(build.START)[0], output['index.html'].split(build.START)[0])
        self.assertEqual(current.split(build.END)[1], output['index.html'].split(build.END)[1])
        self.assertIn(build.BASE + 'projets/site-personnel.html', output['sitemap.xml'])


if __name__ == '__main__':
    unittest.main()
