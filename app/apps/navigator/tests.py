from django.test import SimpleTestCase
from django.urls import reverse

from apps.base.services import get_services

from .content import DEMO_VARIANTS, get_common, get_products, get_styles, validate
from .prompt import build_prompt

REQUIRED_STYLES = {
    'minimalism', 'swiss', 'editorial', 'brutalism', 'neobrutalism', 'retro', 'retrofuturism',
    'organic', 'playful', 'premium', 'tech', 'glassmorphism', 'neumorphism', 'flat',
    'skeuomorphism', 'bento', 'y2k', 'memphis', 'art-deco', 'cyberpunk', 'material',
    'hand-drawn', 'claymorphism', 'aurora',
}


class ContentTests(SimpleTestCase):
    def test_content_is_valid(self):
        errors, warnings = validate()
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_catalog_contains_all_required_styles(self):
        self.assertTrue(REQUIRED_STYLES <= {s['slug'] for s in get_styles()})

    def test_products_are_exactly_three(self):
        self.assertEqual([p['slug'] for p in get_products()], list(DEMO_VARIANTS))

    def test_prompt_contains_style_product_and_scope_notice(self):
        notice = get_common()['scope_notice']
        for style in get_styles():
            for product in get_products():
                text = build_prompt(style, product)
                self.assertIn(style['name_ru'], text)
                self.assertIn(product['prompt_label'], text)
                self.assertIn(notice, text)
                for rule in style['prompt']['product'][product['slug']]:
                    self.assertIn(rule, text)

    def test_prompts_differ_by_product(self):
        style = get_styles()[0]
        texts = {build_prompt(style, p) for p in get_products()}
        self.assertEqual(len(texts), 3)


class PageTests(SimpleTestCase):
    def test_home_lists_navigator_service(self):
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'Навигатор дизайна')
        self.assertContains(response, reverse('navigator:catalog'))
        self.assertTrue(any(s.slug == 'design-navigator' for s in get_services()))

    def test_catalog_and_search(self):
        response = self.client.get(reverse('navigator:catalog'))
        self.assertEqual(response.status_code, 200)
        for style in get_styles():
            self.assertContains(response, style['name_ru'])

        response = self.client.get(reverse('navigator:catalog'), {'q': 'Swiss'})
        self.assertIn('swiss', response.context['matched_slugs'])
        self.assertLess(response.context['matched_count'], len(get_styles()))

        response = self.client.get(reverse('navigator:catalog'), {'q': 'несуществующийзапрос'})
        self.assertEqual(response.context['matched_count'], 0)
        self.assertContains(response, 'Ничего не найдено')

    def test_kind_filter_and_stats(self):
        response = self.client.get(reverse('navigator:catalog'), {'kind': 'technique'})
        techniques = {s['slug'] for s in get_styles() if s['kind'] == 'technique'}
        self.assertEqual(response.context['matched_slugs'], techniques)
        self.assertContains(response, 'aria-current="true"')
        self.assertEqual(response.context['stats'][0]['value'], len(get_styles()))

        response = self.client.get(reverse('navigator:catalog'), {'kind': 'unknown'})
        self.assertEqual(response.context['matched_count'], len(get_styles()))

    def test_every_style_page_and_demo(self):
        for style in get_styles():
            for variant in DEMO_VARIANTS:
                url = reverse('navigator:style', args=[style['slug']]) + f'?demo={variant}'
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200, url)
                self.assertContains(response, 'Использовать')

    def test_unknown_style_returns_404(self):
        for name in ('navigator:style', 'navigator:use', 'navigator:prompt_type'):
            response = self.client.get(reverse(name, args=['no-such-style']))
            self.assertEqual(response.status_code, 404)
            self.assertContains(response, 'Такого стиля нет', status_code=404)

    def test_full_prompt_flow(self):
        slug = 'minimalism'
        use = self.client.get(reverse('navigator:use', args=[slug]))
        self.assertContains(use, reverse('navigator:prompt_type', args=[slug]))

        choose = self.client.get(reverse('navigator:prompt_type', args=[slug]))
        for product in get_products():
            self.assertContains(choose, f'value="{product["slug"]}"')

        redirect = self.client.get(reverse('navigator:prompt_type', args=[slug]), {'product': 'app'})
        self.assertRedirects(redirect, reverse('navigator:prompt_result', args=[slug, 'app']))

        invalid = self.client.get(reverse('navigator:prompt_type', args=[slug]), {'product': 'tv'})
        self.assertEqual(invalid.status_code, 400)

        result = self.client.get(reverse('navigator:prompt_result', args=[slug, 'app']))
        self.assertContains(result, 'Скопировать')
        self.assertContains(result, 'Скачать .txt')
        self.assertContains(result, 'Изменить тип продукта')
        self.assertContains(result, get_common()['scope_notice'])

        download = self.client.get(reverse('navigator:prompt_download', args=[slug, 'app']))
        self.assertEqual(download['Content-Type'], 'text/plain; charset=utf-8')
        self.assertIn('attachment', download['Content-Disposition'])
        self.assertIn('Минимализм', download.content.decode())

    def test_unknown_product_redirects_to_choice(self):
        response = self.client.get(reverse('navigator:prompt_result', args=['minimalism', 'tv']))
        self.assertRedirects(response, reverse('navigator:prompt_type', args=['minimalism']))


class AssetTests(SimpleTestCase):
    def test_demo_bundle_contains_every_style_and_is_cacheable(self):
        from .assets import css_bundle
        version, _ = css_bundle(get_styles())
        response = self.client.get(reverse('navigator:demo_bundle'), {'v': version})
        self.assertEqual(response.status_code, 200)
        self.assertIn('immutable', response['Cache-Control'])
        text = response.content.decode()
        for style in get_styles():
            self.assertIn(f'.dm-{style["slug"]}', text)

    def test_fonts_merge_weights_of_same_family(self):
        from .assets import font_urls
        a = {'demo_fonts': ['Exo 2:wght@400;700']}
        b = {'demo_fonts': ['Exo 2:wght@500', 'Russo One']}
        urls = font_urls([a, b])
        self.assertEqual(len(urls), 1)
        self.assertIn('Exo+2:wght@400;500;700', urls[0])
        self.assertIn('family=Russo+One', urls[0])
