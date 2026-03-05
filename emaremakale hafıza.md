# 🧠 EMARE MAKALE — PROJE HAFIZA DOSYASI

> 🔗 **Ortak Hafıza:** [`EMARE_ORTAK_HAFIZA.md`](/Users/emre/Desktop/Emare/EMARE_ORTAK_HAFIZA.md) — Tüm Emare ekosistemi, sunucu bilgileri, standartlar ve proje envanteri için bak.


> **Son Güncelleme:** 3 Mart 2026  
> **Proje Durumu:** ✅ Tam çalışır durumda  
> **Proje Dizini:** `/Users/emre/Desktop/makale`  
> **Çalıştırma:** `export PATH="$HOME/Library/Python/3.9/bin:$PATH" && python3 app.py`  
> **Erişim Adresi:** http://127.0.0.1:5000

---

## 📌 PROJE NEDİR?

**"Emare Makale Üretici"** — Otomatik makale yazan, yöneten ve paylaşan bir web uygulaması.

### Temel Yetenekler:
1. **Otomatik Makale Üretimi** — Konu gir, ton seç, uzunluk ayarla → profesyonel makale üretilsin
2. **Makale Yönetimi** — Oluşturulan makaleleri listeleme, görüntüleme, silme, indirme (Markdown)
3. **Tek Tıkla Yayınlama & Paylaşım** — Makaleye benzersiz slug atanır, paylaşım linki oluşur, Twitter/LinkedIn/WhatsApp/Telegram/E-posta butonları
4. **Trend İçerik Toplayıcı** — Reddit, Hacker News, Dev.to, Lobste.rs, GitHub, Lemmy, ProductHunt'tan en yüksek etkileşimli içerikleri toplar
5. **Trend → Makale** — Trend içerikten tek tıkla o konuda makale üretme

---

## 🏗️ TEKNOLOJİ STACK

| Katman | Teknoloji | Detay |
|--------|-----------|-------|
| **Backend** | Python 3.9 + Flask 3.0 | Ana web framework |
| **Veritabanı** | SQLite + Flask-SQLAlchemy 3.1.1 | `sqlite:///makaleler.db` |
| **AI** | OpenAI API (gpt-4o) | Opsiyonel — API key yoksa şablon tabanlı üretim çalışır |
| **Frontend** | Tailwind CSS (CDN) | Emare Finance Design System renkleri/animasyonları |
| **Etkileşim** | Alpine.js 3.x (CDN) | Mobil menü, form loading, tab switching, canlı filtreleme |
| **İkonlar** | Font Awesome 6.5.1 (CDN) | Tüm ikonlar |
| **Font** | Inter (Google Fonts) | Ağırlıklar: 300-900 |
| **Markdown** | python-markdown 3.5.2 + bleach 6.1.0 | Makale içeriği markdown → güvenli HTML |
| **HTTP** | requests 2.31.0 | İçerik toplayıcı için |
| **Ortam** | python-dotenv 1.0.1 | .env dosyası desteği |

---

## 📁 DOSYA YAPISI — HER DOSYANIN DETAYLI AÇIKLAMASI

```
/Users/emre/Desktop/makale/
├── app.py                          # Ana Flask uygulaması (301 satır)
├── config.py                       # Konfigürasyon (17 satır)
├── models.py                       # Veritabanı modelleri (62 satır)
├── generator.py                    # Makale üretim motoru (280 satır)
├── collector.py                    # İçerik toplayıcı (395 satır)
├── requirements.txt                # Python bağımlılıkları
├── emaremakale hafıza.md           # BU DOSYA
├── instance/
│   └── makaleler.db                # SQLite veritabanı (otomatik oluşur)
├── templates/
│   ├── base.html                   # Ana layout (234 satır)
│   ├── index.html                  # Ana sayfa + form (190 satır)
│   ├── article.html                # Makale görüntüleme (167 satır)
│   ├── articles.html               # Makale listesi (155 satır)
│   ├── share.html                  # Paylaşılan makale sayfası (80 satır)
│   └── trending.html               # Trend içerikler sayfası (247 satır)
└── static/
    ├── css/
    │   └── style.css               # Emare DS özel stiller (141 satır)
    └── js/
        └── main.js                 # Scroll reveal (32 satır)
```

---

## 📄 DOSYA DOSYA DETAYLI AÇIKLAMA

### 1. `app.py` — Ana Flask Uygulaması (301 satır)

**Import'lar:** os, uuid, markdown, bleach, datetime, flask (Flask, render_template, request, redirect, url_for, flash, send_file, Response), models, generator, collector, config

**Başlatma:**
- `app = Flask(__name__)` + `app.config.from_object(Config)`
- `db.init_app(app)` — SQLAlchemy veritabanı
- `generator = ArticleGenerator(api_key=...)` — Makale üretici
- `collector = ContentCollector()` — İçerik toplayıcı
- `md = markdown.Markdown(extensions=['extra', 'codehilite', 'toc', 'nl2br'])`

**Güvenlik:**
- `ALLOWED_TAGS` — h1-h6, p, br, hr, ul, ol, li, pre, code, blockquote, table, thead, tbody, tr, th, td, img, div, span, strong, em, a, del, sup, sub
- `ALLOWED_ATTRS` — class, id, style (tümü); href, title, target (a); src, alt vs. (img)
- `markdown_to_html(text)` — markdown → HTML → bleach.clean()

**Rotalar (Routes):**

| Route | Method | Fonksiyon | Açıklama |
|-------|--------|-----------|----------|
| `/` | GET | `index()` | Ana sayfa — makale oluşturma formu |
| `/generate` | POST | `generate()` | Form verilerini alıp makale üretir, DB'ye kaydeder, article sayfasına yönlendirir |
| `/article/<article_id>` | GET | `view_article()` | Tek makale görüntüle (markdown → HTML) |
| `/articles` | GET | `articles_list()` | Tüm makaleleri listele (tarihe göre azalan sıra) |
| `/article/<id>/publish` | POST | `publish_article()` | Makaleyi yayınla — slug oluşturur, is_published=True yapar |
| `/s/<slug>` | GET | `shared_article()` | Paylaşılan makaleyi göster + view_count++ |
| `/article/<id>/download` | GET | `download_article()` | Makaleyi .md dosyası olarak indir |
| `/article/<id>/delete` | POST | `delete_article()` | Makaleyi sil |
| `/trending` | GET | `trending()` | Trend içerikleri topla ve göster |
| `/api/trending` | GET | `api_trending()` | Trend verilerini JSON döndür |
| `/api/generate` | POST | `api_generate()` | API ile makale üret (JSON body) |
| `/api/articles` | GET | `api_articles()` | Tüm makaleleri JSON listele |
| `/api/article/<id>` | GET | `api_article()` | Tek makaleyi JSON döndür |

**Hata Sayfaları:** 404 ve 500 handler'ları

**Çalıştırma:** `app.run(debug=True, host='0.0.0.0', port=5000)`

---

### 2. `config.py` — Konfigürasyon (17 satır)

```python
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'makale-gizli-anahtar-2026')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///makaleler.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o')
    DEFAULT_LANGUAGE = 'tr'
    MAX_ARTICLE_LENGTH = 5000
    MIN_ARTICLE_LENGTH = 500
```

**Not:** OpenAI API key çevre değişkeninden okunur. Key yoksa şablon tabanlı üretim devreye girer.

---

### 3. `models.py` — Veritabanı Modelleri (62 satır)

**Article modeli:**
| Alan | Tip | Varsayılan | Açıklama |
|------|-----|------------|----------|
| `id` | String(36) | UUID4 | Primary key |
| `title` | String(500) | — | Makale başlığı |
| `content` | Text | — | Makale içeriği (Markdown) |
| `topic` | String(200) | — | Konu |
| `tone` | String(50) | 'profesyonel' | Yazım tonu |
| `length` | String(20) | 'orta' | Uzunluk ayarı |
| `keywords` | String(500) | '' | Anahtar kelimeler (virgülle ayrılmış) |
| `target_audience` | String(200) | 'genel' | Hedef kitle |
| `word_count` | Integer | 0 | Kelime sayısı |
| `created_at` | DateTime | utcnow | Oluşturulma tarihi |
| `updated_at` | DateTime | utcnow | Güncelleme tarihi |
| `is_published` | Boolean | False | Yayınlandı mı? |
| `share_slug` | String(100) | None | Paylaşım URL slug'ı (unique) |
| `view_count` | Integer | 0 | Görüntülenme sayısı |

**Metotlar:** `__repr__()`, `to_dict()` (API için JSON serialization)

**ArticleTemplate modeli:**
| Alan | Tip | Açıklama |
|------|-----|----------|
| `id` | Integer (auto) | Primary key |
| `name` | String(200) | Şablon adı |
| `description` | Text | Açıklama |
| `prompt_template` | Text | Prompt şablonu |
| `category` | String(100) | Kategori |
| `created_at` | DateTime | Oluşturulma tarihi |

---

### 4. `generator.py` — Makale Üretim Motoru (280 satır)

**Sınıf:** `ArticleGenerator`

**Tonlar (TONES):**
| Anahtar | Açıklama |
|---------|----------|
| `profesyonel` | Resmi ve bilgilendirici |
| `samimi` | Sıcak, sohbet tarzı |
| `akademik` | Bilimsel, kaynaklara dayanan |
| `seo` | SEO uyumlu, anahtar kelime odaklı |
| `blog` | Kişisel deneyimlerle zenginleştirilmiş |
| `haber` | Nesnel, 5N1K kuralına uygun |

**Uzunluklar (LENGTHS):**
| Anahtar | Kelime Aralığı |
|---------|----------------|
| `kisa` | 300-500 |
| `orta` | 500-1000 |
| `uzun` | 1000-2000 |
| `cok_uzun` | 2000-4000 |

**Metotlar:**
- `generate(topic, tone, length, keywords, target_audience, custom_instructions)` — Ana üretim metodu (AI var → AI, yok → şablon)
- `_build_prompt(...)` — OpenAI için prompt oluşturur
- `_generate_with_ai(...)` — `client.chat.completions.create()` ile gpt-4o'dan makale üretir
- `_generate_with_template(...)` — API key olmadan şablon tabanlı makale üretir
- `_generate_title(topic)` — 8 farklı başlık şablonundan random seçer
- `_generate_template_content(...)` — 5 ana bölüm + giriş + sonuç üretir (Nedir?, Neden Önemli?, Temel Bilgiler, Pratik İpuçları, SSS)
- `_parse_result(text)` — AI yanıtını BASLIK: / --- formatından ayrıştırır

**AI Entegrasyonu:**
```python
response = self.client.chat.completions.create(
    model='gpt-4o',
    messages=[
        {"role": "system", "content": "Sen profesyonel bir Türkçe içerik yazarısın..."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.7,
    max_tokens=4000
)
```

---

### 5. `collector.py` — İçerik Toplayıcı (395 satır)

**Sınıf:** `ContentCollector`

**Sabitler:**
- `HEADERS` — User-Agent: 'MakaleUretici/1.0'
- `REQUEST_TIMEOUT` — 10 saniye

**Reddit Kategori Eşlemeleri (REDDIT_SUBS):**
| Kategori | Subreddit'ler |
|----------|---------------|
| `teknoloji` | technology, programming, webdev, artificial, MachineLearning |
| `bilim` | science, space, Physics, biology, EverythingScience |
| `finans` | finance, investing, CryptoCurrency, economics, personalfinance |
| `tasarim` | design, web_design, UI_Design, graphic_design |
| `girisimcilik` | startups, Entrepreneur, smallbusiness, SideProject |
| `genel` | worldnews, todayilearned, explainlikeimfive, AskReddit, Futurology |
| `saglik` | Health, nutrition, Fitness, mentalhealth |
| `egitim` | learnprogramming, datascience, AskAcademia, education |

**Kaynaklar ve API'lar:**

| Kaynak | API URL | Method | Detay |
|--------|---------|--------|-------|
| **Reddit** | `reddit.com/r/{sub}/top.json?t=day` | GET | Her kategoriden max 3 subreddit, 0.5s rate limit |
| **Hacker News** | `hacker-news.firebaseio.com/v0/topstories.json` | GET | Top story ID'leri + paralel item fetch (max_workers=10) |
| **Dev.to** | `dev.to/api/articles?per_page={n}&top=1` | GET | Popüler makaleler |
| **Lobste.rs** | `lobste.rs/hottest.json` | GET | En sıcak hikayeler |
| **ProductHunt** | `reddit.com/r/SideProject/top.json?t=week` | GET | PH API OAuth gerektirdiği için SideProject subreddit proxy |
| **GitHub** | `api.github.com/search/repositories?q=created:>...&sort=stars` | GET | Son 7 gün en çok yıldız alan repolar |
| **Lemmy** | `lemmy.world/api/v3/post/list?sort=TopDay` | GET | Fediverse günün en popülerleri |

**Her Kaynak İçin Standardize Edilen Alanlar:**
```python
{
    'id': str,              # MD5 hash (source + item_id)[:12]
    'source': str,          # 'Reddit', 'Hacker News', 'Dev.to', vb.
    'source_icon': str,     # 'fab fa-reddit-alien', vb.
    'source_color': str,    # 'text-orange-500', vb.
    'category': str,        # 'teknoloji', 'bilim', vb.
    'title': str,           # İçerik başlığı
    'url': str,             # Tartışma URL'i
    'external_url': str,    # Harici kaynak URL
    'score': int,           # Oy/yıldız sayısı
    'comments': int,        # Yorum sayısı
    'author': str,          # Yazar
    'created': str,         # Tarih
    'selftext': str,        # Açıklama (max 300 karakter)
    'engagement': int,      # score + (comments * 2) — sıralama puanı
}
```

**Paralel Çalışma:**
- `collect_all()` → `ThreadPoolExecutor(max_workers=8)` ile 7 kaynağı eşzamanlı çeker
- Hacker News kendi içinde de `ThreadPoolExecutor(max_workers=10)` ile item'ları paralel çeker

**Yardımcı Metotlar:**
- `_ts_to_date(ts)` — Unix timestamp → tarih string
- `_make_id(source, item_id)` — MD5 hash ile benzersiz ID
- `get_all_categories()` — Tüm Reddit kategorilerini döndürür

---

### 6. `templates/base.html` — Ana Layout (234 satır)

**Head:**
- Tailwind CSS CDN + özel config (brand renkleri, animasyonlar, keyframes)
- Google Fonts — Inter (300-900)
- Font Awesome 6.5.1
- Alpine.js 3.x + collapse + intersect plugins
- Custom CSS (style.css)

**Tailwind Config (inline):**
```javascript
colors: {
    brand: {
        50: '#eef2ff', 100: '#e0e7ff', 200: '#c7d2fe',
        300: '#a5b4fc', 400: '#818cf8', 500: '#6366f1',
        600: '#4f46e5', 700: '#4338ca', 800: '#3730a3',
        900: '#312e81', 950: '#1e1b4b'
    }
}
animations: float, float-delayed, float-slow, gradient, fade-up, slide-right, pulse-soft
```

**Navbar:** Fixed top, `bg-white/95 backdrop-blur-xl`, logo (M gradient square + "Makale Üretici"), 
- Desktop: Yeni Makale, Makalelerim, Trend İçerikler, Üret (CTA)
- Mobile: Hamburger menu (Alpine.js x-data mobileMenu)

**Flash Messages:** x-data show, 5 saniye sonra otomatik kaybolur, success/danger/warning/info renkleri

**Footer:** `bg-gray-950`, gradient separator, logo, nav linkleri, sosyal medya ikonları, "© 2026 Makale Üretici — Emare Finance"

**Block'lar:** `{% block title %}`, `{% block extra_css %}`, `{% block content %}`, `{% block extra_js %}`

---

### 7. `templates/index.html` — Ana Sayfa (190 satır)

**Hero Section:**
- Animated gradient background (dark brand colors)
- Radial gradient overlay + floating blobs (animate-float)
- Büyük başlık: "Otomatik **Makale** Üret"
- Alt metin + 2 CTA buton (Hemen Başla → #formSection, Makalelerim)

**Form Section:**
- Section header: "Makale Oluştur" gradient text
- Form card: `bg-white rounded-3xl border shadow-lg`
- Alpine.js `x-data="{ loading: false }"` ile loading state

**Form Alanları:**
| Alan | Input | Detay |
|------|-------|-------|
| Konu* | text input | required, max 200, `value="{{ request.args.get('topic', '') }}"` (trend'den gelen topic) |
| Yazım Tonu | select | Profesyonel, Samimi, Akademik, SEO, Blog, Haber (emoji prefix) |
| Makale Uzunluğu | select | Kısa, Orta (default), Uzun, Çok Uzun |
| Anahtar Kelimeler | text input | Virgülle ayrılmış |
| Hedef Kitle | text input | default "Genel okuyucu" |
| Özel Talimatlar | textarea | Opsiyonel, 3 satır |

**Submit:** Gradient buton, loading durumunda spinning SVG + "Makale Üretiliyor..."

**Features Section:** 3 kart — Hızlı Üretim (bolt), Kolay Paylaşım (share-nodes), Tam Özelleştirme (sliders). Hover'da ikon rengi gradient'e dönüşür + scale + rotate.

---

### 8. `templates/article.html` — Makale Görüntüleme (167 satır)

**Toolbar:** Geri Dön, Kopyala, İndir, Paylaş/Yayınla, Sil
- Yayınlanmamışsa "Yayınla" butonu (POST form)
- Yayınlanmışsa "Paylaş" butonu (navigator.share API veya clipboard)

**Article Card:** 
- Başlık (h1), meta etiketler (konu, ton, tarih, kelime sayısı, yayın durumu, görüntülenme)
- Keyword badge'leri (#tag formatında)
- İçerik alanı (article-content class ile tipografi)

**Share Section (yayınlanmışsa):**
- Paylaşım URL input + Kopyala butonu
- Sosyal medya butonları: Twitter/X, LinkedIn, WhatsApp, Telegram, E-posta

**JavaScript:**
- `copyArticle()` — İçeriği panoya kopyalar
- `copyShareLink()` — URL'yi panoya kopyalar
- `shareArticle(url)` — Web Share API veya fallback clipboard
- `showToast(msg)` — Yeşil toast bildirim (2.5 saniye)

---

### 9. `templates/articles.html` — Makale Listesi (155 satır)

**Header:** "Makalelerim" gradient text + Yeni Makale CTA

**Filter Bar (Alpine.js):**
- search (text arama), filterTone (select), filterStatus (published/draft select)
- Canlı filtreleme — x-show ile anında güncelleme

**Articles Grid:** 2 sütunlu grid, her kart:
- Konu badge, yayın durumu badge
- Başlık (tıklanabilir), önizleme (ilk 150 karakter)
- Tarih, kelime sayısı, görüntüle/sil butonları

**Stats Dashboard:** 4 metrik kartı:
- Toplam Makale, Yayındaki, Toplam Kelime, Toplam Görüntülenme

**Empty State:** İkon + "Henüz makale yok" + CTA

---

### 10. `templates/share.html` — Paylaşılan Makale (80 satır)

**Gradient Header:** Animated gradient bg + başlık, meta bilgiler
**Content:** Keyword badge'leri + article-content
**Footer:** Logo + "Makale Üretici ile oluşturuldu" + Twitter/LinkedIn/WhatsApp paylaşım ikonları

---

### 11. `templates/trending.html` — Trend İçerikler (247 satır)

**Hero:** Fire ikonu, "Trend İçerikler" gradient text

**Category Filter Bar (sticky):**
- Checkbox'lar (teknoloji, bilim, finans, tasarim, girisimcilik, genel, saglik, egitim)
- "Güncelle" butonu (form GET submit)

**Tab Bar (Alpine.js):**
- "Hepsi" tab'ı + her kaynak için ayrı tab (Reddit, HN, Dev.to, Lobsters, GitHub, Lemmy, PH)
- Tab sayaçları parantez içinde

**Search:** Canlı arama input

**İçerik Kartları:**
- Engagement score (büyük gradient rakam)
- Kaynak ikonu + rengi
- Başlık (tıklanabilir → harici link), açıklama
- Score, comments, author, tarih, tags
- Action butonlar: Kaynağa Git, Bu Konuda Makale Üret, Tartışmayı Gör

**Empty State:** "İçerik yüklenemedi" + Tekrar Dene

**ÖNEMLİ NOT:** `source_data['items']` kullanılmalı (dict.items() metodu ile çakışmamak için), `source_data.items` DEĞİL!

---

### 12. `static/css/style.css` — Özel Stiller (141 satır)

- `.gradient-text` — brand gradient text
- `@keyframes gradient` — Arka plan gradient animasyonu
- `.scroll-reveal` / `.scroll-reveal.revealed` — Scroll'da ortaya çıkma animasyonu
- `.article-content` — Makale içerik tipografisi:
  - h1: 1.875rem bold, h2: 1.5rem bold + brand-colored border-bottom, h3: 1.25rem semibold
  - p: 1.25rem margin-bottom
  - ul/ol: 1.5rem padding-left
  - blockquote: brand-colored left border + arka plan
  - a: brand-colored underline
  - code: gri arka plan, brand renkli yazı
  - pre: `bg-brand-950` koyu arka plan
- `.line-clamp-2` — 2 satır sonrası kırp
- Scrollbar: brand renkli
- Selection: brand renk arka plan

---

### 13. `static/js/main.js` — JavaScript (32 satır)

- `initScrollReveal()` — IntersectionObserver ile `.scroll-reveal` elementleri ekranda göründüğünde `.revealed` class'ı ekler (threshold: 0.15)

---

## 🎨 EMARE FİNANCE DESIGN SYSTEM

### Renk Paleti
| Token | Hex | Kullanım |
|-------|-----|----------|
| brand-50 | #eef2ff | Hafif arka planlar |
| brand-100 | #e0e7ff | Badge arka planları |
| brand-200 | #c7d2fe | Border'lar |
| brand-300 | #a5b4fc | Hover efektleri |
| brand-400 | #818cf8 | İkincil vurgular |
| brand-500 | #6366f1 | **ANA MARKA RENGİ** |
| brand-600 | #4f46e5 | Buton hover |
| brand-700 | #4338ca | Metin vurgu |
| brand-800 | #3730a3 | Koyu vurgu |
| brand-900 | #312e81 | Koyu arka plan |
| brand-950 | #1e1b4b | En koyu (footer, code blokları) |

### Gradient'ler
- **Ana CTA:** `bg-gradient-to-r from-brand-500 to-purple-600`
- **Hero BG:** `linear-gradient(-45deg, #0f0a2e, #1e1b4b, #1e1b4b, #312e81)` animated
- **Text Gradient:** `from-brand-600 via-purple-600 to-violet-600`
- **Engagement Score:** `from-brand-500 to-purple-600` (vertical)

### Animasyonlar
| Ad | Süre | Açıklama |
|----|------|----------|
| float | 6s ease-in-out infinite | Y ekseninde 20px yukarı-aşağı |
| float-delayed | 6s + 2s delay | Gecikmeli float |
| float-slow | 8s + 1s delay | Yavaş float |
| gradient | 8s ease infinite | Background position kayması |
| fadeUp | 0.6s ease-out | Aşağıdan yukarı fade-in |
| slideRight | 0.6s ease-out | Soldan sağa slide-in |
| pulseSoft | 3s ease-in-out infinite | Opacity 1 ↔ 0.7 |

### Komponent Kalıpları
- **Kartlar:** `bg-white rounded-3xl border border-gray-100 shadow-lg shadow-gray-100/50`
- **CTA Butonlar:** `rounded-xl bg-gradient-to-r from-brand-500 to-purple-600 shadow-lg shadow-brand-500/30 hover:shadow-brand-500/50 hover:scale-105`
- **Input'lar:** `rounded-xl border border-gray-200 focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20`
- **Badge'ler:** `rounded-full text-xs font-medium px-3 py-1`
- **Navbar:** `fixed top-0 bg-white/95 backdrop-blur-xl shadow-sm`

---

## 🛤️ ROUTE HARİTASI (URL YAPISI)

```
GET  /                          → Ana sayfa (makale oluşturma formu)
POST /generate                  → Makale üret ve kaydet
GET  /article/<uuid>            → Makale görüntüle
GET  /articles                  → Tüm makaleleri listele
POST /article/<uuid>/publish    → Makaleyi yayınla
GET  /s/<slug>                  → Paylaşılan makale (public)
GET  /article/<uuid>/download   → Makaleyi .md olarak indir
POST /article/<uuid>/delete     → Makaleyi sil
GET  /trending                  → Trend içerikler
GET  /trending?category=x&y     → Kategoriye göre trend

API:
GET  /api/trending              → Trend JSON
POST /api/generate              → Makale üret (JSON)
GET  /api/articles              → Tüm makaleler JSON
GET  /api/article/<uuid>        → Tek makale JSON
```

---

## ⚙️ KURULUM & ÇALIŞTIRMA

### Gereksinimler
- Python 3.9+
- pip ile paketler

### Kurulum
```bash
cd /Users/emre/Desktop/makale
pip3 install -r requirements.txt
```

### Çalıştırma
```bash
# macOS'ta Python 3.9 PATH sorunu için:
export PATH="$HOME/Library/Python/3.9/bin:$PATH"
python3 app.py
```

### OpenAI API (Opsiyonel)
```bash
# .env dosyası oluştur veya çevre değişkeni ata:
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="gpt-4o"  # varsayılan gpt-4o

# Sonra uygulamayı başlat
python3 app.py
```

> **API key yoksa:** Şablon tabanlı üretim otomatik devreye girer. Temel yapıda ama çalışan makaleler üretir.

### Bilinen Uyarılar
- `NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently 'LibreSSL 2.8.3'` — macOS'ta yaygın, işlevselliği etkilemez

---

## 🐛 BİLİNEN SORUNLAR & ÇÖZÜMLER

### 1. Flask PATH Sorunu (macOS)
**Sorun:** `flask` komutu bulunamıyor  
**Çözüm:** `export PATH="$HOME/Library/Python/3.9/bin:$PATH"` ile PATH'e ekle

### 2. Jinja2 dict.items() Çakışması
**Sorun:** Template'de `source_data.items` yazılınca Python dict'in `.items()` metoduna erişiyor  
**Çözüm:** `source_data['items']` bracket notation kullanılmalı (trending.html'de düzeltildi)

### 3. onclick Tırnak Çakışması
**Sorun:** `onclick='shareArticle("{{ url_for("...") }}")'` — iç içe tırnaklar bozuluyor  
**Çözüm:** `{% set share_url = url_for(...) %}` ile önce değişkene ata (article.html'de düzeltildi)

---

## 🔮 GELİŞTİRME PLANI (YAPILMAMIŞ ÖZELLIKLER)

- [ ] Makale düzenleme (edit) sayfası
- [ ] Makale kategorileri sistemi
- [ ] Toplu makale üretimi (batch)
- [ ] Zamanlanmış içerik toplama (scheduler)
- [ ] Dışa aktarım (PDF, DOCX)
- [ ] Kullanıcı giriş sistemi (authentication)
- [ ] Makale versiyonlama
- [ ] SEO analiz skoru
- [ ] RSS feed çıktısı
- [ ] Dark mode toggle

---

## 📊 PROJE İSTATİSTİKLERİ

| Metrik | Değer |
|--------|-------|
| Toplam Python kodu | ~1,055 satır |
| Toplam HTML template | ~1,073 satır |
| Toplam CSS | 141 satır |
| Toplam JS | 32 satır |
| Toplam dosya | 13 |
| Veritabanı tablosu | 2 (articles, templates) |
| API endpoint | 4 |
| Web route | 9 |
| Dış kaynak (collector) | 7 |
| Reddit kategori | 8 |
| Makale tonu | 6 |
| Makale uzunluğu | 4 |

---

## 🔑 HIZLI REFERANS

```bash
# Projeyi başlat
cd /Users/emre/Desktop/makale
export PATH="$HOME/Library/Python/3.9/bin:$PATH"
python3 app.py

# Tarayıcıda aç
http://127.0.0.1:5000

# API ile makale üret (curl)
curl -X POST http://127.0.0.1:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "Yapay Zeka", "tone": "profesyonel", "length": "orta"}'

# Tüm makaleleri listele
curl http://127.0.0.1:5000/api/articles

# Trend içerikleri çek
curl "http://127.0.0.1:5000/api/trending?category=teknoloji&category=bilim"
```

---

> **Bu dosya projenin tam hafızasıdır. Taşıdığınız her yere yanınıza alın — kaldığınız yerden devam edebilmeniz için tüm detaylar burada.**
