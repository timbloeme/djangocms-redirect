# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings
from django.utils.encoding import force_text
from django.utils.http import urlunquote_plus

from djangocms_redirect.middleware import RedirectMiddleware
from djangocms_redirect.models import Redirect

from .base import BaseRedirectTest


class TestRedirect(BaseRedirectTest):

    _pages_data = (
        {'en': {'title': 'home page', 'template': 'page.html', 'publish': True}},
        {'en': {'title': 'test page', 'template': 'page.html', 'publish': True}},
        {'en': {'title': 'internal page', 'template': 'page.html', 'publish': True,
                'parent': 'test-page'}},
    )

    def test_str(self):
        pages = self.get_pages()

        redirect = Redirect.objects.create(
            site=self.site_1,
            old_path=pages[1].get_absolute_url(),
            new_path=pages[0].get_absolute_url(),
            response_code='301',
        )
        self.assertIn(pages[1].get_absolute_url(), force_text(redirect))
        self.assertIn(pages[0].get_absolute_url(), force_text(redirect))

    def test_301_redirect(self):
        pages = self.get_pages()

        redirect = Redirect.objects.create(
            site=self.site_1,
            old_path=pages[1].get_absolute_url(),
            new_path=pages[0].get_absolute_url(),
            response_code='301',
        )

        with self.assertNumQueries(1):
            response = self.client.get(pages[1].get_absolute_url())
        self.assertEqual(response.status_code, 301)
        self.assertRedirects(response, redirect.new_path, status_code=301)

    def test_cached_redirect(self):
        pages = self.get_pages()

        redirect = Redirect.objects.create(
            site=self.site_1,
            old_path=pages[1].get_absolute_url(),
            new_path=pages[0].get_absolute_url(),
            response_code='301',
        )

        with self.assertNumQueries(1):
            response = self.client.get(pages[1].get_absolute_url())
        self.assertEqual(response.status_code, 301)
        self.assertRedirects(response, redirect.new_path, status_code=301)

        with self.assertNumQueries(0):
            response = self.client.get(pages[1].get_absolute_url())
        self.assertEqual(response.status_code, 301)

    def test_302_redirect(self):
        pages = self.get_pages()

        redirect = Redirect.objects.create(
            site=self.site_1,
            old_path=pages[1].get_absolute_url(),
            new_path=pages[0].get_absolute_url(),
            response_code='302',
        )

        with self.assertNumQueries(1):
            response = self.client.get(pages[1].get_absolute_url())
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, redirect.new_path, status_code=302)

    def test_querystring_redirect(self):
        pages = self.get_pages()

        redirect = Redirect.objects.create(
            site=self.site_1,
            old_path=pages[1].get_absolute_url(),
            new_path=pages[0].get_absolute_url(),
            response_code='302',
        )

        with self.assertNumQueries(1):
            response = self.client.get(pages[1].get_absolute_url() + '?Some_query_param')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, redirect.new_path + '?Some_query_param', status_code=302)

    def test_quoted_path_redirect(self):
        pages = self.get_pages()

        escaped_path = '/path%20%28escaped%29/'
        redirect = Redirect.objects.create(
            site=self.site_1,
            old_path=escaped_path,
            new_path=pages[0].get_absolute_url(),
            response_code='302',
        )

        response = self.client.get(escaped_path)
        self.assertEqual(response.status_code, 404)

        redirect.old_path = '/path%20(escaped)/'
        redirect.save()
        response = self.client.get(escaped_path)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, redirect.new_path, status_code=302)

        unescaped_path = urlunquote_plus(escaped_path)
        redirect.old_path = unescaped_path
        redirect.save()

        response = self.client.get(escaped_path)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, redirect.new_path, status_code=302)

    def test_410_redirect(self):
        pages = self.get_pages()

        Redirect.objects.create(
            site=self.site_1,
            old_path=pages[1].get_absolute_url(),
            new_path=pages[0].get_absolute_url(),
            response_code='410',
        )

        with self.assertNumQueries(1):
            response = self.client.get(pages[1].get_absolute_url())
        self.assertEqual(response.status_code, 410)

        Redirect.objects.create(
            site=self.site_1,
            old_path='/some-path/',
            response_code='302'
        )

        with self.assertNumQueries(1):
            response2 = self.client.get('/some-path/')
        self.assertEqual(response2.status_code, 410)

    def test_use_response_404_only(self):
        pages = self.get_pages()

        with self.settings(DJANGOCMS_REDIRECT_USE_REQUEST=False):
            Redirect.objects.create(
                site=self.site_1,
                old_path=pages[1].get_absolute_url(),
                new_path=pages[0].get_absolute_url(),
                response_code='302',
            )

            with self.assertNumQueries(8):
                response = self.client.get(pages[1].get_absolute_url())
            self.assertEqual(response.status_code, 200)

    def test_use_response_no404(self):
        pages = self.get_pages()

        with self.settings(DJANGOCMS_REDIRECT_USE_REQUEST=False, DJANGOCMS_REDIRECT_404_ONLY=False):
            redirect = Redirect.objects.create(
                site=self.site_1,
                old_path=pages[1].get_absolute_url(),
                new_path=pages[0].get_absolute_url(),
                response_code='302',
            )

            with self.assertNumQueries(9):
                response = self.client.get(pages[1].get_absolute_url())
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, redirect.new_path, status_code=302)

    def test_delete_redirect(self):
        pages = self.get_pages()

        redirect = Redirect.objects.create(
            site=self.site_1,
            old_path=pages[1].get_absolute_url(),
            new_path=pages[0].get_absolute_url(),
            response_code='301',
        )

        with self.assertNumQueries(1):
            response = self.client.get(pages[1].get_absolute_url())
        self.assertRedirects(response, redirect.new_path, status_code=301)
        redirect.delete()

        with self.assertNumQueries(7):
            response2 = self.client.get(pages[1].get_absolute_url())
        self.assertEqual(response2.status_code, 200)

    def test_redirect_no_append_slash(self):
        pages = self.get_pages()

        with override_settings(APPEND_SLASH=False):
            redirect = Redirect.objects.create(
                site=self.site_1,
                old_path=pages[1].get_absolute_url(),
                new_path=pages[0].get_absolute_url(),
                response_code='301',
            )

            with self.assertNumQueries(3):
                response = self.client.get(pages[1].get_absolute_url().rstrip('/'))
            self.assertRedirects(response, redirect.new_path, status_code=301)

    def test_redirect_no_append_slash_quoted(self):
        pages = self.get_pages()

        original_path = '/path%20(escaped)/'
        with override_settings(APPEND_SLASH=False):
            redirect = Redirect.objects.create(
                site=self.site_1,
                old_path=original_path,
                new_path=pages[0].get_absolute_url(),
                response_code='301',
            )

            with self.assertNumQueries(5):
                response = self.client.get(original_path.rstrip('/'))
            self.assertRedirects(response, redirect.new_path, status_code=301)

    def test_redirect_no_append_slash_no_match(self):
        pages = self.get_pages()

        with override_settings(APPEND_SLASH=False):
            Redirect.objects.create(
                site=self.site_1,
                old_path='/no-match',
                new_path=pages[0].get_absolute_url(),
                response_code='301',
            )

            with self.assertNumQueries(4):
                response = self.client.get(pages[1].get_absolute_url().rstrip('/'))
            self.assertEqual(404, response.status_code)


class TestPartialMatch(BaseRedirectTest):
    _pages_data = (
        {'en': {'title': 'home page', 'template': 'page.html', 'publish': True}},
        {'en': {'title': 'test page', 'template': 'page.html', 'publish': True}},
        {'en': {'title': 'internal page', 'template': 'page.html', 'publish': True,
                'parent': 'test-page'}},
    )

    def setUp(self):
        super(TestPartialMatch, self).setUp()
        Redirect.objects.create(
            site=self.site_1,
            old_path='/en/test',
            new_path='/baz',
            response_code='301',
        )
        Redirect.objects.create(
            site=self.site_1,
            old_path='/en/test-page/in',
            new_path='/bar',
            response_code='301',
        )
        Redirect.objects.create(
            site=self.site_1,
            old_path='/en/test-page/internal',
            new_path='/not-match',
            response_code='302',
        )
        Redirect.objects.create(
            site=self.site_1,
            old_path='/en/test-page/other/path',
            new_path='/foo',
            response_code='301',
        )
        Redirect.objects.create(
            site=self.site_1,
            old_path='/en/fobz/',
            new_path='/fabz',
            response_code='301',
        )

    def _patch_catchall_redirect(self, redirect):
        redirect.catchall_redirect = True
        redirect.save()
        return redirect

    def _patch_subpath_match(self, redirect):
        redirect.subpath_match = True
        redirect.save()
        return redirect

    def test_no_substring(self):
        pages = self.get_pages()
        with self.assertNumQueries(13):
            response = self.client.get(pages[2].get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_partial_success(self):
        pages = self.get_pages()
        redirect = self._patch_catchall_redirect(Redirect.objects.get(old_path='/en/test-page/in'))
        with self.assertNumQueries(2):
            response = self.client.get(pages[2].get_absolute_url())
        self.assertRedirects(
            response, redirect.new_path, status_code=301, fetch_redirect_response=False
        )

    def test_partial_subpath_replace(self):
        pages = self.get_pages()
        self._patch_subpath_match(Redirect.objects.get(old_path='/en/test-page/in'))
        with self.assertNumQueries(2):
            response = self.client.get(pages[2].get_absolute_url())
        new_path = pages[2].get_absolute_url().replace('/en/test-page/in', '/bar')
        self.assertRedirects(
            response, new_path, status_code=301, fetch_redirect_response=False
        )

    def test_all_partials(self):
        pages = self.get_pages()
        redirect = Redirect.objects.get(old_path='/en/test-page/internal')
        for patched in Redirect.objects.all():
            self._patch_catchall_redirect(patched)
        with self.assertNumQueries(2):
            response = self.client.get(pages[2].get_absolute_url())
        self.assertRedirects(
            response, redirect.new_path, status_code=302, fetch_redirect_response=False
        )


class TestNoSitesMatch(BaseRedirectTest):
    _pages_data = (
        {'en': {'title': 'home page', 'template': 'page.html', 'publish': True}},
        {'en': {'title': 'test page', 'template': 'page.html', 'publish': True}},
        {'en': {'title': 'internal page', 'template': 'page.html', 'publish': True,
                'parent': 'test-page'}},
    )
    PATCHED_INSTALLED_APPS = [
        app for app in settings.INSTALLED_APPS if app != 'django.contrib.sites'
    ]

    @override_settings(INSTALLED_APPS=PATCHED_INSTALLED_APPS)
    def test_no_sites(self):
        pages = self.get_pages()

        Redirect.objects.create(
            site=self.site_1,
            old_path=pages[1].get_absolute_url(),
            new_path=pages[0].get_absolute_url(),
            response_code='301',
        )

        with self.assertRaises(ImproperlyConfigured) as context:
            self.client.get(pages[1].get_absolute_url())
        self.assertEqual(RedirectMiddleware.no_site_message, force_text(context.exception))

try:
    import memcache
except ImportError:
    pass
else:
    @override_settings(
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
                'LOCATION': '127.0.0.1:11211',
            }
        }
    )
    class TestMemcacheRedirect(BaseRedirectTest):
        _pages_data = (
            {'en': {'title': 'home page', 'template': 'page.html', 'publish': True}},
            {'en': {'title': 'test page', 'template': 'page.html', 'publish': True}},
            {'en': {'title': 'internal page', 'template': 'page.html', 'publish': True,
                    'parent': 'test-page'}},
        )

        def test_fix_memcache_MemcachedKeyLengthError(self):
            """
            Fixes https://github.com/nephila/djangocms-redirect/issues/8
            Using an url > 250 chars with memcache active, a memcache.Client.MemcachedKeyLengthError is raised
            """
            pages = self.get_pages()
            url_suffix = 'x' * 250  # url > 250 chars

            url = '{}?{}'.format(
                pages[1].get_absolute_url(),
                url_suffix
            )
            expected_url = '{}?{}'.format(
                pages[0].get_absolute_url(),
                url_suffix
            )

            Redirect.objects.create(
                site=self.site_1,
                old_path=pages[1].get_absolute_url(),
                new_path=pages[0].get_absolute_url(),
                response_code='302',
            )
            try:
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertRedirects(response, expected_url, status_code=302)
            except memcache.Client.MemcachedKeyLengthError:
                self.fail("memcache.Client.MemcachedKeyLengthError raised")
