"""
İçerik Toplayıcı (Content Collector)
Dünyanın çeşitli forum ve platformlarından en popüler içerikleri toplar.

Desteklenen Kaynaklar:
- Reddit (çeşitli subreddit'ler)
- Hacker News (top/best stories)
- Dev.to (popüler makaleler)
- Lobste.rs (en çok oylanan)
- Product Hunt (günün ürünleri)
- GitHub Trending
- Lemmy (Fediverse forumları)
"""

import requests
import time
import hashlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ortak request headers
HEADERS = {
    'User-Agent': 'MakaleUretici/1.0 (Content Aggregator; Educational)',
    'Accept': 'application/json',
}

REQUEST_TIMEOUT = 10  # saniye


class ContentCollector:
    """Çeşitli platformlardan popüler içerik toplayan sınıf."""

    # ===== Kategori bazlı subreddit'ler =====
    REDDIT_SUBS = {
        'teknoloji': ['technology', 'programming', 'webdev', 'artificial', 'MachineLearning'],
        'bilim': ['science', 'space', 'Physics', 'biology', 'EverythingScience'],
        'finans': ['finance', 'investing', 'CryptoCurrency', 'economics', 'personalfinance'],
        'tasarim': ['design', 'web_design', 'UI_Design', 'graphic_design'],
        'girisimcilik': ['startups', 'Entrepreneur', 'smallbusiness', 'SideProject'],
        'genel': ['worldnews', 'todayilearned', 'explainlikeimfive', 'AskReddit', 'Futurology'],
        'saglik': ['Health', 'nutrition', 'Fitness', 'mentalhealth'],
        'egitim': ['learnprogramming', 'datascience', 'AskAcademia', 'education'],
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def collect_all(self, categories=None, limit=10):
        """
        Tüm kaynaklardan paralel olarak içerik toplar.

        Args:
            categories: Reddit için kategori listesi (None = hepsi)
            limit: Her kaynaktan max kaç içerik

        Returns:
            dict: { 'reddit': [...], 'hackernews': [...], ... }
        """
        results = {}
        tasks = {}

        with ThreadPoolExecutor(max_workers=8) as executor:
            # Reddit
            reddit_cats = categories or ['genel', 'teknoloji']
            tasks[executor.submit(self.fetch_reddit, reddit_cats, limit)] = 'reddit'

            # Hacker News
            tasks[executor.submit(self.fetch_hackernews, limit)] = 'hackernews'

            # Dev.to
            tasks[executor.submit(self.fetch_devto, limit)] = 'devto'

            # Lobste.rs
            tasks[executor.submit(self.fetch_lobsters, limit)] = 'lobsters'

            # Product Hunt (daily digest)
            tasks[executor.submit(self.fetch_producthunt, limit)] = 'producthunt'

            # GitHub Trending
            tasks[executor.submit(self.fetch_github_trending, limit)] = 'github'

            # Lemmy
            tasks[executor.submit(self.fetch_lemmy, limit)] = 'lemmy'

            for future in as_completed(tasks):
                source = tasks[future]
                try:
                    results[source] = future.result()
                except Exception as e:
                    results[source] = {'error': str(e), 'items': []}

        return results

    # ===================================================================
    # REDDIT
    # ===================================================================
    def fetch_reddit(self, categories=None, limit=10):
        """Reddit'ten popüler içerik çeker."""
        categories = categories or ['genel']
        all_items = []

        for cat in categories:
            subs = self.REDDIT_SUBS.get(cat, self.REDDIT_SUBS['genel'])
            for sub in subs[:3]:  # Her kategoriden max 3 subreddit
                try:
                    url = f'https://www.reddit.com/r/{sub}/top.json?t=day&limit={limit}'
                    resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
                    if resp.status_code == 200:
                        data = resp.json()
                        for post in data.get('data', {}).get('children', []):
                            p = post['data']
                            all_items.append({
                                'id': self._make_id('reddit', p.get('id', '')),
                                'source': 'Reddit',
                                'source_icon': 'fab fa-reddit-alien',
                                'source_color': 'text-orange-500',
                                'subreddit': f"r/{p.get('subreddit', sub)}",
                                'category': cat,
                                'title': p.get('title', ''),
                                'url': f"https://www.reddit.com{p.get('permalink', '')}",
                                'external_url': p.get('url', ''),
                                'score': p.get('score', 0),
                                'comments': p.get('num_comments', 0),
                                'author': p.get('author', ''),
                                'created': self._ts_to_date(p.get('created_utc', 0)),
                                'selftext': (p.get('selftext', '') or '')[:300],
                                'thumbnail': p.get('thumbnail', '') if p.get('thumbnail', '').startswith('http') else '',
                                'engagement': p.get('score', 0) + p.get('num_comments', 0) * 2,
                            })
                    time.sleep(0.5)  # Rate limit
                except Exception:
                    continue

        # En yüksek etkileşime göre sırala
        all_items.sort(key=lambda x: x['engagement'], reverse=True)
        return {'items': all_items[:limit * 2], 'source_name': 'Reddit', 'source_url': 'https://reddit.com'}

    # ===================================================================
    # HACKER NEWS
    # ===================================================================
    def fetch_hackernews(self, limit=10):
        """Hacker News'ten en popüler hikayeleri çeker."""
        items = []
        try:
            # Top stories ID'leri
            url = 'https://hacker-news.firebaseio.com/v0/topstories.json'
            resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
            if resp.status_code != 200:
                return {'items': [], 'source_name': 'Hacker News', 'source_url': 'https://news.ycombinator.com'}

            story_ids = resp.json()[:limit * 2]

            # Paralel fetch
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {executor.submit(self._fetch_hn_item, sid): sid for sid in story_ids}
                for future in as_completed(futures):
                    try:
                        item = future.result()
                        if item and item.get('type') == 'story':
                            items.append({
                                'id': self._make_id('hn', str(item.get('id', ''))),
                                'source': 'Hacker News',
                                'source_icon': 'fab fa-hacker-news',
                                'source_color': 'text-orange-600',
                                'category': 'teknoloji',
                                'title': item.get('title', ''),
                                'url': f"https://news.ycombinator.com/item?id={item.get('id', '')}",
                                'external_url': item.get('url', ''),
                                'score': item.get('score', 0),
                                'comments': len(item.get('kids', [])),
                                'author': item.get('by', ''),
                                'created': self._ts_to_date(item.get('time', 0)),
                                'selftext': '',
                                'engagement': item.get('score', 0) + len(item.get('kids', [])) * 2,
                            })
                    except Exception:
                        continue

        except Exception:
            pass

        items.sort(key=lambda x: x['engagement'], reverse=True)
        return {'items': items[:limit], 'source_name': 'Hacker News', 'source_url': 'https://news.ycombinator.com'}

    def _fetch_hn_item(self, item_id):
        """Tek bir HN item'ı çeker."""
        url = f'https://hacker-news.firebaseio.com/v0/item/{item_id}.json'
        resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            return resp.json()
        return None

    # ===================================================================
    # DEV.TO
    # ===================================================================
    def fetch_devto(self, limit=10):
        """Dev.to'dan popüler makaleleri çeker."""
        items = []
        try:
            url = f'https://dev.to/api/articles?per_page={limit}&top=1'
            resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                articles = resp.json()
                for a in articles:
                    items.append({
                        'id': self._make_id('devto', str(a.get('id', ''))),
                        'source': 'Dev.to',
                        'source_icon': 'fab fa-dev',
                        'source_color': 'text-gray-900',
                        'category': 'teknoloji',
                        'title': a.get('title', ''),
                        'url': a.get('url', ''),
                        'external_url': a.get('url', ''),
                        'score': a.get('public_reactions_count', 0),
                        'comments': a.get('comments_count', 0),
                        'author': a.get('user', {}).get('username', ''),
                        'created': a.get('published_at', '')[:10] if a.get('published_at') else '',
                        'selftext': a.get('description', '')[:300],
                        'thumbnail': a.get('cover_image', '') or a.get('social_image', '') or '',
                        'tags': ', '.join(a.get('tag_list', [])),
                        'engagement': a.get('public_reactions_count', 0) + a.get('comments_count', 0) * 2,
                    })
        except Exception:
            pass

        items.sort(key=lambda x: x['engagement'], reverse=True)
        return {'items': items[:limit], 'source_name': 'Dev.to', 'source_url': 'https://dev.to'}

    # ===================================================================
    # LOBSTE.RS
    # ===================================================================
    def fetch_lobsters(self, limit=10):
        """Lobste.rs'tan en popüler içerikleri çeker."""
        items = []
        try:
            url = 'https://lobste.rs/hottest.json'
            resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                stories = resp.json()[:limit]
                for s in stories:
                    items.append({
                        'id': self._make_id('lobsters', s.get('short_id', '')),
                        'source': 'Lobste.rs',
                        'source_icon': 'fas fa-shrimp',
                        'source_color': 'text-red-600',
                        'category': 'teknoloji',
                        'title': s.get('title', ''),
                        'url': s.get('comments_url', ''),
                        'external_url': s.get('url', ''),
                        'score': s.get('score', 0),
                        'comments': s.get('comment_count', 0),
                        'author': s.get('submitter_user', {}).get('username', '') if isinstance(s.get('submitter_user'), dict) else str(s.get('submitter_user', '')),
                        'created': s.get('created_at', '')[:10] if s.get('created_at') else '',
                        'selftext': s.get('description', '')[:300] if s.get('description') else '',
                        'tags': ', '.join(s.get('tags', [])),
                        'engagement': s.get('score', 0) + s.get('comment_count', 0) * 2,
                    })
        except Exception:
            pass

        return {'items': items, 'source_name': 'Lobste.rs', 'source_url': 'https://lobste.rs'}

    # ===================================================================
    # PRODUCT HUNT (Unofficial - front page)
    # ===================================================================
    def fetch_producthunt(self, limit=10):
        """Product Hunt benzeri veri - günlük trending ürünler."""
        # PH API v2 OAuth gerektiriyor, alternatif kaynak kullanıyoruz
        items = []
        try:
            # Unofficial: daily popular posts via RSS proxy
            url = 'https://www.reddit.com/r/SideProject/top.json?t=week&limit=' + str(limit)
            resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                for post in data.get('data', {}).get('children', []):
                    p = post['data']
                    items.append({
                        'id': self._make_id('ph', p.get('id', '')),
                        'source': 'Product Hunt / SideProject',
                        'source_icon': 'fab fa-product-hunt',
                        'source_color': 'text-orange-500',
                        'category': 'girisimcilik',
                        'title': p.get('title', ''),
                        'url': f"https://www.reddit.com{p.get('permalink', '')}",
                        'external_url': p.get('url', ''),
                        'score': p.get('score', 0),
                        'comments': p.get('num_comments', 0),
                        'author': p.get('author', ''),
                        'created': self._ts_to_date(p.get('created_utc', 0)),
                        'selftext': (p.get('selftext', '') or '')[:300],
                        'engagement': p.get('score', 0) + p.get('num_comments', 0) * 2,
                    })
        except Exception:
            pass

        items.sort(key=lambda x: x['engagement'], reverse=True)
        return {'items': items[:limit], 'source_name': 'Product Hunt / SideProject', 'source_url': 'https://www.producthunt.com'}

    # ===================================================================
    # GITHUB TRENDING
    # ===================================================================
    def fetch_github_trending(self, limit=10):
        """GitHub'dan trending repo bilgilerini çeker."""
        items = []
        try:
            # GitHub Search API - son 7 günde en çok yıldız alan
            url = 'https://api.github.com/search/repositories?q=created:>2026-02-23&sort=stars&order=desc&per_page=' + str(limit)
            resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                repos = resp.json().get('items', [])
                for r in repos:
                    items.append({
                        'id': self._make_id('github', str(r.get('id', ''))),
                        'source': 'GitHub Trending',
                        'source_icon': 'fab fa-github',
                        'source_color': 'text-gray-800',
                        'category': 'teknoloji',
                        'title': f"{r.get('full_name', '')} — {r.get('description', '')[:100]}",
                        'url': r.get('html_url', ''),
                        'external_url': r.get('html_url', ''),
                        'score': r.get('stargazers_count', 0),
                        'comments': r.get('open_issues_count', 0),
                        'author': r.get('owner', {}).get('login', ''),
                        'created': r.get('created_at', '')[:10] if r.get('created_at') else '',
                        'selftext': r.get('description', '')[:300] if r.get('description') else '',
                        'language': r.get('language', ''),
                        'stars': r.get('stargazers_count', 0),
                        'forks': r.get('forks_count', 0),
                        'engagement': r.get('stargazers_count', 0) + r.get('forks_count', 0),
                    })
        except Exception:
            pass

        return {'items': items, 'source_name': 'GitHub Trending', 'source_url': 'https://github.com/trending'}

    # ===================================================================
    # LEMMY (Fediverse)
    # ===================================================================
    def fetch_lemmy(self, limit=10):
        """Lemmy (Fediverse) forumlarından popüler içerikleri çeker."""
        items = []
        try:
            url = f'https://lemmy.world/api/v3/post/list?sort=TopDay&limit={limit}'
            resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                posts = resp.json().get('posts', [])
                for p in posts:
                    post = p.get('post', {})
                    counts = p.get('counts', {})
                    community = p.get('community', {})
                    creator = p.get('creator', {})
                    items.append({
                        'id': self._make_id('lemmy', str(post.get('id', ''))),
                        'source': 'Lemmy',
                        'source_icon': 'fas fa-comments',
                        'source_color': 'text-teal-600',
                        'category': 'genel',
                        'subreddit': community.get('name', ''),
                        'title': post.get('name', ''),
                        'url': post.get('ap_id', ''),
                        'external_url': post.get('url', '') or post.get('ap_id', ''),
                        'score': counts.get('score', 0),
                        'comments': counts.get('comments', 0),
                        'author': creator.get('name', ''),
                        'created': post.get('published', '')[:10] if post.get('published') else '',
                        'selftext': (post.get('body', '') or '')[:300],
                        'engagement': counts.get('score', 0) + counts.get('comments', 0) * 2,
                    })
        except Exception:
            pass

        items.sort(key=lambda x: x['engagement'], reverse=True)
        return {'items': items[:limit], 'source_name': 'Lemmy (Fediverse)', 'source_url': 'https://lemmy.world'}

    # ===================================================================
    # YARDIMCI METOTLAR
    # ===================================================================
    def _ts_to_date(self, ts):
        """Unix timestamp'i tarih string'ine çevirir."""
        try:
            return datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
        except Exception:
            return ''

    def _make_id(self, source, item_id):
        """Benzersiz bir ID oluşturur."""
        raw = f"{source}_{item_id}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]

    def get_all_categories(self):
        """Mevcut tüm kategorileri döndürür."""
        return list(self.REDDIT_SUBS.keys())
