# 🚀 Emare Makale — Geliştirme Planı

> **Tarih:** 4 Mart 2026  
> **Amaç:** Mevcut projeyi Emare ekosistemindeki diğer projelerden öğrenilen en iyi pratiklerle geliştirmek

---

## 📦 Diğer Projelerden Alınacak Özellikler

### 1. **Kullanıcı Kimlik Doğrulama Sistemi**
**Kaynak:** Emare Finance, EmareCloud  
**Özellikler:**
- Session tabanlı login/logout
- Kullanıcı rolleri (admin, editor, viewer)
- Her kullanıcının kendi makaleleri
- Çoklu kullanıcı desteği

**Yeni Dosyalar:**
```python
# auth.py - Authentication middleware
from functools import wraps
from flask import session, redirect, url_for

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function
```

**Yeni Model:**
```python
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')  # admin, editor, user
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # İlişkiler
    articles = db.relationship('Article', backref='author', lazy=True)
```

---

### 2. **Dark Mode Toggle**
**Kaynak:** Emare Finance Design System  
**Uygulama:** Alpine.js + localStorage

```html
<!-- base.html'e eklenecek -->
<div x-data="{ darkMode: localStorage.getItem('darkMode') === 'true' }"
     x-init="$watch('darkMode', val => localStorage.setItem('darkMode', val))"
     :class="darkMode ? 'dark' : ''">
    
    <!-- Dark mode toggle butonu -->
    <button @click="darkMode = !darkMode" 
            class="fixed bottom-6 right-6 z-50 w-12 h-12 rounded-full bg-brand-500 text-white shadow-lg hover:scale-110 transition-transform">
        <i class="fas" :class="darkMode ? 'fa-sun' : 'fa-moon'"></i>
    </button>
</div>
```

**Tailwind Dark Mode Config:**
```javascript
// tailwind.config eklenecek
darkMode: 'class',
```

---

### 3. **Rate Limiting & API Security**
**Kaynak:** Emare Asistan, EmareCloud  
**Kütüphane:** Flask-Limiter

```python
# requirements.txt'e ekle
Flask-Limiter==3.5.0

# app.py'ye ekle
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# API route'larına ekle
@app.route('/api/generate', methods=['POST'])
@limiter.limit("10 per hour")  # Saat başı max 10 makale
def api_generate():
    # ...
```

---

### 4. **Makale Düzenleme (Edit) Özelliği**
**Kaynak:** Emare Team, EmareCloud

```python
@app.route('/article/<article_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_article(article_id):
    """Makale düzenleme sayfası."""
    article = Article.query.get_or_404(article_id)
    
    # Yetki kontrolü
    if article.user_id != session.get('user_id') and session.get('role') != 'admin':
        flash('Bu makaleyi düzenleme yetkiniz yok.', 'danger')
        return redirect(url_for('articles_list'))
    
    if request.method == 'POST':
        article.title = request.form.get('title', '').strip()
        article.content = request.form.get('content', '').strip()
        article.keywords = request.form.get('keywords', '').strip()
        article.updated_at = datetime.utcnow()
        article.word_count = len(article.content.split())
        
        db.session.commit()
        flash('Makale güncellendi!', 'success')
        return redirect(url_for('view_article', article_id=article.id))
    
    return render_template('edit_article.html', article=article)
```

---

### 5. **Makale Kategorileri Sistemi**
**Kaynak:** Emare Finance, Emare Log

```python
# models.py'ye ekle
class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, default='')
    icon = db.Column(db.String(50), default='fa-folder')
    color = db.Column(db.String(20), default='brand')
    
    # İlişkiler
    articles = db.relationship('Article', backref='category', lazy=True)

# Article modeline ekle
category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
```

---

### 6. **Export Özellikleri (PDF, DOCX)**
**Kaynak:** Emare Team, Emare Katip

```python
# requirements.txt'e ekle
reportlab==4.0.9
python-docx==1.1.0

# export.py - Yeni dosya
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from docx import Document

def export_to_pdf(article):
    """Makaleyi PDF olarak döndürür."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Başlık
    story.append(Paragraph(article.title, styles['Heading1']))
    story.append(Spacer(1, 12))
    
    # İçerik
    for line in article.content.split('\n'):
        if line.strip():
            story.append(Paragraph(line, styles['BodyText']))
            story.append(Spacer(1, 6))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def export_to_docx(article):
    """Makaleyi DOCX olarak döndürür."""
    doc = Document()
    doc.add_heading(article.title, 0)
    
    for line in article.content.split('\n'):
        if line.strip():
            doc.add_paragraph(line)
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer
```

---

### 7. **Makale Versiyonlama**
**Kaynak:** Hive Coordinator, EmareSetup

```python
class ArticleVersion(db.Model):
    __tablename__ = 'article_versions'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    article_id = db.Column(db.String(36), db.ForeignKey('articles.id'), nullable=False)
    version_number = db.Column(db.Integer, default=1)
    title = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=False)
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    change_summary = db.Column(db.String(500), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Makale düzenlendiğinde otomatik versiyon oluştur
def create_version(article, user_id, summary=''):
    version_count = ArticleVersion.query.filter_by(article_id=article.id).count()
    new_version = ArticleVersion(
        article_id=article.id,
        version_number=version_count + 1,
        title=article.title,
        content=article.content,
        changed_by=user_id,
        change_summary=summary
    )
    db.session.add(new_version)
    db.session.commit()
```

---

### 8. **SEO Analiz Skoru**
**Kaynak:** generator.py'den esinlenerek

```python
def calculate_seo_score(article):
    """Makale SEO skorunu hesaplar (0-100)."""
    score = 0
    
    # Başlık uzunluğu (50-60 karakter ideal)
    title_len = len(article.title)
    if 50 <= title_len <= 60:
        score += 15
    elif 40 <= title_len <= 70:
        score += 10
    
    # İçerik uzunluğu (min 500 kelime)
    if article.word_count >= 1500:
        score += 20
    elif article.word_count >= 800:
        score += 15
    elif article.word_count >= 500:
        score += 10
    
    # Anahtar kelime kullanımı
    if article.keywords:
        kw_list = [k.strip().lower() for k in article.keywords.split(',')]
        content_lower = article.content.lower()
        kw_usage = sum(1 for kw in kw_list if kw in content_lower)
        score += min(kw_usage * 5, 20)
    
    # Alt başlık varlığı (##)
    h2_count = article.content.count('\n## ')
    if h2_count >= 3:
        score += 15
    elif h2_count >= 1:
        score += 10
    
    # Liste kullanımı
    if '\n- ' in article.content or '\n* ' in article.content:
        score += 10
    
    # Görsel/link varlığı
    if '![' in article.content or 'http' in article.content:
        score += 10
    
    return min(score, 100)
```

---

### 9. **RSS Feed Çıktısı**
**Kaynak:** Emare Log

```python
from flask import make_response

@app.route('/rss')
def rss_feed():
    """RSS feed."""
    articles = Article.query.filter_by(is_published=True).order_by(Article.created_at.desc()).limit(20).all()
    
    rss = '<?xml version="1.0" encoding="UTF-8"?>\n'
    rss += '<rss version="2.0">\n'
    rss += '<channel>\n'
    rss += '<title>Makale Üretici — Son Makaleler</title>\n'
    rss += '<link>http://127.0.0.1:5000</link>\n'
    rss += '<description>Otomatik üretilen profesyonel makaleler</description>\n'
    
    for article in articles:
        rss += '<item>\n'
        rss += f'<title>{article.title}</title>\n'
        rss += f'<link>http://127.0.0.1:5000/s/{article.share_slug}</link>\n'
        rss += f'<description>{article.content[:200]}...</description>\n'
        rss += f'<pubDate>{article.created_at.strftime("%a, %d %b %Y %H:%M:%S +0000")}</pubDate>\n'
        rss += '</item>\n'
    
    rss += '</channel>\n'
    rss += '</rss>'
    
    response = make_response(rss)
    response.headers['Content-Type'] = 'application/rss+xml; charset=utf-8'
    return response
```

---

### 10. **Toplu Makale Üretimi (Batch Processing)**
**Kaynak:** Emarebot (Trendyol batch), collector.py (paralel fetch)

```python
@app.route('/batch-generate', methods=['GET', 'POST'])
@login_required
@admin_required
def batch_generate():
    """Toplu makale üretimi."""
    if request.method == 'POST':
        topics = request.form.get('topics', '').strip().split('\n')
        tone = request.form.get('tone', 'profesyonel')
        length = request.form.get('length', 'orta')
        
        results = []
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(generator.generate, topic.strip(), tone, length): topic for topic in topics if topic.strip()}
            
            for future in as_completed(futures):
                topic = futures[future]
                try:
                    result = future.result()
                    article = Article(
                        title=result['title'],
                        content=result['content'],
                        topic=topic,
                        tone=tone,
                        length=length,
                        word_count=result['word_count'],
                        user_id=session.get('user_id')
                    )
                    db.session.add(article)
                    results.append({'topic': topic, 'status': 'success'})
                except Exception as e:
                    results.append({'topic': topic, 'status': 'error', 'error': str(e)})
        
        db.session.commit()
        return render_template('batch_results.html', results=results)
    
    return render_template('batch_generate.html')
```

---

### 11. **Zamanlanmış İçerik Toplama (Scheduler)**
**Kaynak:** Emarebot, collector.py

```python
# requirements.txt'e ekle
APScheduler==3.10.4

# scheduler.py - Yeni dosya
from apscheduler.schedulers.background import BackgroundScheduler
from collector import ContentCollector
import json

scheduler = BackgroundScheduler()
collector = ContentCollector()

def scheduled_content_collection():
    """Her 6 saatte bir trend içerikleri topla ve kaydet."""
    results = collector.collect_all(categories=['genel', 'teknoloji'], limit=10)
    
    # JSON dosyasına kaydet
    with open('instance/cached_trends.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Trend içerikler güncellendi: {datetime.now()}")

def start_scheduler():
    """Scheduler'ı başlat."""
    scheduler.add_job(
        scheduled_content_collection,
        'interval',
        hours=6,
        id='trend_collector',
        replace_existing=True
    )
    scheduler.start()

# app.py'ye ekle
from scheduler import start_scheduler
if __name__ == '__main__':
    start_scheduler()
    app.run(debug=True, host='0.0.0.0', port=5000)
```

---

### 12. **Webhook & Notification Sistemi**
**Kaynak:** Emare Asistan (WhatsApp), EmareCloud (notification)

```python
# notifications.py - Yeni dosya
import requests

def send_discord_notification(article):
    """Yeni makale Discord'a bildirilir."""
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL', '')
    if not webhook_url:
        return
    
    payload = {
        "embeds": [{
            "title": f"🎉 Yeni Makale: {article.title}",
            "description": article.content[:200] + "...",
            "color": 0x6366f1,
            "fields": [
                {"name": "Konu", "value": article.topic, "inline": True},
                {"name": "Kelime Sayısı", "value": str(article.word_count), "inline": True}
            ],
            "footer": {"text": "Emare Makale Üretici"}
        }]
    }
    
    try:
        requests.post(webhook_url, json=payload, timeout=5)
    except:
        pass

# Makale oluşturulduktan sonra çağrılır
def send_telegram_notification(article):
    """Telegram bildirimi."""
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
    
    if not bot_token or not chat_id:
        return
    
    message = f"📝 *Yeni Makale*\n\n*{article.title}*\n\nKonu: {article.topic}\nKelime: {article.word_count}"
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        requests.post(url, json=payload, timeout=5)
    except:
        pass
```

---

### 13. **Analytics Dashboard**
**Kaynak:** Emare Finance Dashboard, EmareCloud stats

```html
<!-- analytics.html - Yeni sayfa -->
<section class="py-12">
    <div class="max-w-7xl mx-auto px-4">
        <h1 class="text-3xl font-bold mb-8">📊 İstatistikler</h1>
        
        <!-- Grafikler -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <!-- Günlük makale üretimi (Chart.js) -->
            <div class="bg-white rounded-2xl p-6 shadow-lg">
                <h3 class="font-semibold mb-4">Son 7 Gün Makale Üretimi</h3>
                <canvas id="articleChart"></canvas>
            </div>
            
            <!-- Ton dağılımı (Pie chart) -->
            <div class="bg-white rounded-2xl p-6 shadow-lg">
                <h3 class="font-semibold mb-4">Ton Dağılımı</h3>
                <canvas id="toneChart"></canvas>
            </div>
        </div>
    </div>
</section>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
```

---

## 🗂️ Yeni Dosya Yapısı

```
Emaremakale/
├── app.py                      # Ana uygulama (genişletilecek)
├── config.py                   # Config (yeni ayarlar)
├── models.py                   # Modeller (User, Category, Version eklenecek)
├── generator.py                # Makale üretici
├── collector.py                # İçerik toplayıcı
├── auth.py                     # 🆕 Authentication middleware
├── export.py                   # 🆕 PDF/DOCX export
├── notifications.py            # 🆕 Discord/Telegram webhook
├── scheduler.py                # 🆕 APScheduler jobs
├── seo_analyzer.py             # 🆕 SEO scoring
├── requirements.txt            # Güncellenecek
├── .env.example                # 🆕 ENV template
├── instance/
│   ├── makaleler.db            # Database
│   └── cached_trends.json      # 🆕 Cached trends
├── migrations/                 # 🆕 Flask-Migrate
├── tests/                      # 🆕 Unit tests
│   ├── test_generator.py
│   ├── test_auth.py
│   └── test_api.py
├── templates/
│   ├── base.html               # Dark mode eklenecek
│   ├── index.html
│   ├── article.html
│   ├── articles.html
│   ├── share.html
│   ├── trending.html
│   ├── login.html              # 🆕
│   ├── register.html           # 🆕
│   ├── edit_article.html       # 🆕
│   ├── batch_generate.html     # 🆕
│   ├── analytics.html          # 🆕
│   └── profile.html            # 🆕
└── static/
    ├── css/
    │   └── style.css           # Dark mode stilleri
    └── js/
        ├── main.js
        └── analytics.js        # 🆕 Chart.js logic
```

---

## 📝 Öncelik Sıralaması

### Phase 1 — Temel Geliştirmeler (1 hafta)
1. ✅ Kullanıcı sistemi (User model + auth.py)
2. ✅ Login/Register sayfaları
3. ✅ Makale düzenleme özelliği
4. ✅ Dark mode toggle

### Phase 2 — Üretkenlik Araçları (1 hafta)
5. ✅ Kategori sistemi
6. ✅ SEO analiz skoru
7. ✅ Toplu makale üretimi
8. ✅ Rate limiting

### Phase 3 — Export & Sharing (3 gün)
9. ✅ PDF/DOCX export
10. ✅ RSS feed
11. ✅ Webhook bildirimleri

### Phase 4 — İleri Özellikler (1 hafta)
12. ✅ Makale versiyonlama
13. ✅ Analytics dashboard
14. ✅ Zamanlanmış content collector
15. ✅ Unit tests

---

## 🎯 Hedef Mimari

```
┌─────────────────────────────────────────┐
│      Emare Makale v2.0 Architecture     │
├─────────────────────────────────────────┤
│                                         │
│  Frontend (Tailwind + Alpine.js)       │
│  ├── Dark Mode Support                 │
│  ├── Real-time Analytics Charts        │
│  └── Rich Text Editor (optional)       │
│                                         │
│  Backend (Flask 3.0)                    │
│  ├── User Authentication               │
│  ├── Role-based Access Control         │
│  ├── API Rate Limiting                 │
│  └── Background Jobs (APScheduler)     │
│                                         │
│  Database (SQLite)                      │
│  ├── users                              │
│  ├── articles (+ user_id FK)           │
│  ├── categories                         │
│  ├── article_versions                   │
│  └── api_keys (optional)               │
│                                         │
│  External Services                      │
│  ├── OpenAI GPT-4o (article gen)      │
│  ├── Discord Webhook (notifications)   │
│  ├── Telegram Bot (notifications)      │
│  └── Content Collectors (7 sources)    │
│                                         │
└─────────────────────────────────────────┘
```

---

## 📊 Beklenen İyileştirmeler

| Metrik | Şu An | Hedef (v2.0) |
|--------|-------|--------------|
| Kullanıcı sistemi | ❌ | ✅ Multi-user |
| Dark mode | ❌ | ✅ Toggle |
| API güvenliği | ⚠️ Basit | ✅ Rate limit + auth |
| Export seçenekleri | Markdown | Markdown + PDF + DOCX |
| SEO analizi | ❌ | ✅ 0-100 skor |
| Batch üretim | ❌ | ✅ Paralel processing |
| Versiyonlama | ❌ | ✅ Git-like |
| Analytics | Temel sayaçlar | ✅ Chart.js dashboard |
| Notification | ❌ | ✅ Discord + Telegram |
| Scheduled tasks | ❌ | ✅ APScheduler |

---

**Son Güncelleme:** 4 Mart 2026  
**Hazırlayan:** AI-MAKALE (Emare AI Collective)
