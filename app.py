"""
Makale Üretici - Otomatik Makale Yazma ve Paylaşma Sistemi
Flask tabanlı web uygulaması
"""

import os
import uuid
import markdown
import bleach
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, Response, session
from models import db, Article, ArticleTemplate, User
from generator import ArticleGenerator
from collector import ContentCollector
from config import Config
from auth import login_required, admin_required
from werkzeug.security import generate_password_hash, check_password_hash
from auth import login_required, admin_required, editor_or_admin_required

# Flask uygulaması oluştur
app = Flask(__name__)
app.config.from_object(Config)

# Veritabanı başlat
db.init_app(app)

# Makale üretici
generator = ArticleGenerator(api_key=app.config.get('OPENAI_API_KEY', ''))

# İçerik toplayıcı
collector = ContentCollector()

# Markdown dönüştürücü
md = markdown.Markdown(extensions=['extra', 'codehilite', 'toc', 'nl2br'])

# İzin verilen HTML etiketleri
ALLOWED_TAGS = list(bleach.ALLOWED_TAGS) + [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'br', 'hr',
    'ul', 'ol', 'li', 'pre', 'code', 'blockquote', 'table',
    'thead', 'tbody', 'tr', 'th', 'td', 'img', 'div', 'span',
    'strong', 'em', 'a', 'del', 'sup', 'sub'
]
ALLOWED_ATTRS = {
    '*': ['class', 'id', 'style'],
    'a': ['href', 'title', 'target'],
    'img': ['src', 'alt', 'title', 'width', 'height']
}


def markdown_to_html(text):
    """Markdown metnini güvenli HTML'e dönüştürür."""
    md.reset()
    html = md.convert(text)
    clean_html = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)
    return clean_html


# ===== Veritabanı Tablosunu Oluştur =====
with app.app_context():
    db.create_all()


# ===== AUTHENTICATION ROUTES =====

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Kullanıcı girişi."""
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Kullanıcı adı ve şifre gereklidir.', 'danger')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash(f'Hoş geldin, {user.username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Kullanıcı adı veya şifre hatalı.', 'danger')
            return redirect(url_for('login'))
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Yeni kullanıcı kaydı."""
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        password_confirm = request.form.get('password_confirm', '').strip()
        
        # Validasyon
        if not all([username, email, password, password_confirm]):
            flash('Tüm alanları doldurmalısınız.', 'danger')
            return redirect(url_for('register'))
        
        if password != password_confirm:
            flash('Şifreler eşleşmiyor.', 'danger')
            return redirect(url_for('register'))
        
        if len(password) < 6:
            flash('Şifre en az 6 karakter olmalıdır.', 'danger')
            return redirect(url_for('register'))
        
        # Kullanıcı zaten var mı?
        if User.query.filter_by(username=username).first():
            flash('Bu kullanıcı adı zaten kullanılıyor.', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Bu e-posta adresi zaten kayıtlı.', 'danger')
            return redirect(url_for('register'))
        
        # Yeni kullanıcı oluştur
        user = User(username=username, email=email)
        user.set_password(password)
        
        # İlk kullanıcı admin olsun
        if User.query.count() == 0:
            user.role = 'admin'
        
        db.session.add(user)
        db.session.commit()
        
        flash('Kayıt başarılı! Şimdi giriş yapabilirsiniz.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/logout')
def logout():
    """Kullanıcı çıkışı."""
    session.clear()
    flash('Başarıyla çıkış yaptınız.', 'success')
    return redirect(url_for('index'))


@app.route('/profile')
@login_required
def profile():
    """Kullanıcı profili."""
    user = User.query.get(session['user_id'])
    user_articles = Article.query.filter_by(user_id=user.id).order_by(Article.created_at.desc()).all()
    
    stats = {
        'total_articles': len(user_articles),
        'published': sum(1 for a in user_articles if a.is_published),
        'total_words': sum(a.word_count for a in user_articles),
        'total_views': sum(a.view_count for a in user_articles)
    }
    
    return render_template('profile.html', user=user, articles=user_articles, stats=stats)


# ===== ROTALAR =====

@app.route('/')
def index():
    """Ana sayfa - Makale oluşturma formu."""
    return render_template('index.html')


# ===== AUTH ROUTES =====

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Kullanıcı kayıt sayfası."""
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # Validasyon
        if not username or not email or not password:
            flash('Tüm alanları doldurun.', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Şifreler eşleşmiyor.', 'danger')
            return redirect(url_for('register'))
        
        if len(password) < 6:
            flash('Şifre en az 6 karakter olmalıdır.', 'danger')
            return redirect(url_for('register'))
        
        # Kullanıcı kontrolü
        if User.query.filter_by(username=username).first():
            flash('Bu kullanıcı adı zaten kullanılıyor.', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Bu e-posta adresi zaten kayıtlı.', 'danger')
            return redirect(url_for('register'))
        
        # Yeni kullanıcı oluştur
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Hesabınız başarıyla oluşturuldu! Giriş yapabilirsiniz.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Kullanıcı giriş sayfası."""
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Kullanıcı adı ve şifre gereklidir.', 'danger')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash(f'Hoş geldin, {user.username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Kullanıcı adı veya şifre hatalı.', 'danger')
            return redirect(url_for('login'))
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Kullanıcı çıkışı."""
    session.clear()
    flash('Çıkış yapıldı.', 'info')
    return redirect(url_for('index'))


@app.route('/generate', methods=['POST'])
@login_required
def generate():
    """Makale üretim işlemi."""
    topic = request.form.get('topic', '').strip()
    
    if not topic:
        flash('Lütfen bir konu girin.', 'danger')
        return redirect(url_for('index'))
    
    tone = request.form.get('tone', 'profesyonel')
    length = request.form.get('length', 'orta')
    keywords = request.form.get('keywords', '').strip()
    target_audience = request.form.get('target_audience', 'Genel okuyucu').strip()
    custom_instructions = request.form.get('custom_instructions', '').strip()
    
    # Makale üret
    result = generator.generate(
        topic=topic,
        tone=tone,
        length=length,
        keywords=keywords,
        target_audience=target_audience,
        custom_instructions=custom_instructions
    )
    
    if 'error' in result and result.get('word_count', 0) == 0:
        flash(f'Makale üretilirken hata oluştu: {result["error"]}', 'danger')
        return redirect(url_for('index'))
    
    # Veritabanına kaydet
    article = Article(
        title=result['title'],
        content=result['content'],
        topic=topic,
        tone=tone,
        length=length,
        keywords=keywords,
        target_audience=target_audience,
        word_count=result['word_count'],
        user_id=session.get('user_id')  # Kullanıcı ID'si eklendi
    )
    
    db.session.add(article)
    db.session.commit()
    
    flash('Makale başarıyla üretildi!', 'success')
    return redirect(url_for('view_article', article_id=article.id))


@app.route('/article/<article_id>')
@login_required
def view_article(article_id):
    """Makale görüntüleme sayfası."""
    article = Article.query.get_or_404(article_id)
    
    # Yayınlanmamış makaleyi sadece sahibi ve admin görebilir
    if not article.is_published:
        if session.get('user_id') != article.user_id and session.get('role') != 'admin':
            flash('Bu makaleyi görüntüleme yetkiniz yok.', 'danger')
            return redirect(url_for('articles_list'))
    
    article_html = markdown_to_html(article.content)
    
    return render_template('article.html', article=article, article_html=article_html)


@app.route('/article/<article_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_article(article_id):
    """Makale düzenleme sayfası."""
    article = Article.query.get_or_404(article_id)
    
    # Yetki kontrolü - sadece sahibi veya admin düzenleyebilir
    if session.get('user_id') != article.user_id and session.get('role') != 'admin':
        flash('Bu makaleyi düzenleme yetkiniz yok.', 'danger')
        return redirect(url_for('articles_list'))
    
    if request.method == 'POST':
        article.title = request.form.get('title', '').strip()
        article.content = request.form.get('content', '').strip()
        article.keywords = request.form.get('keywords', '').strip()
        article.topic = request.form.get('topic', article.topic).strip()
        article.tone = request.form.get('tone', article.tone)
        article.target_audience = request.form.get('target_audience', article.target_audience).strip()
        article.updated_at = datetime.utcnow()
        article.word_count = len(article.content.split())
        
        if not article.title or not article.content:
            flash('Başlık ve içerik boş olamaz.', 'danger')
            return redirect(url_for('edit_article', article_id=article.id))
        
        db.session.commit()
        flash('Makale güncellendi!', 'success')
        return redirect(url_for('view_article', article_id=article.id))
    
    return render_template('edit_article.html', article=article)


@app.route('/articles')
@login_required
def articles_list():
    """Tüm makalelerin listesi."""
    # Admin tüm makaleleri görebilir, diğerleri sadece kendilerininkini
    if session.get('role') == 'admin':
        articles = Article.query.order_by(Article.created_at.desc()).all()
    else:
        articles = Article.query.filter_by(user_id=session['user_id']).order_by(Article.created_at.desc()).all()
    
    return render_template('articles.html', articles=articles)


@app.route('/article/<article_id>/publish', methods=['POST'])
@login_required
def publish_article(article_id):
    """Makaleyi yayınla (paylaşım linki oluştur)."""
    article = Article.query.get_or_404(article_id)
    
    # Yetki kontrolü
    if session.get('user_id') != article.user_id and session.get('role') != 'admin':
        flash('Bu makaleyi yayınlama yetkiniz yok.', 'danger')
        return redirect(url_for('articles_list'))
    
    if not article.share_slug:
        # Benzersiz slug oluştur
        slug = f"{article.topic.lower().replace(' ', '-')[:30]}-{uuid.uuid4().hex[:8]}"
        article.share_slug = slug
    
    article.is_published = True
    db.session.commit()
    
    flash('Makale yayınlandı! Paylaşım linki oluşturuldu.', 'success')
    return redirect(url_for('view_article', article_id=article.id))


@app.route('/s/<slug>')
def shared_article(slug):
    """Paylaşılan makaleyi görüntüle."""
    article = Article.query.filter_by(share_slug=slug, is_published=True).first_or_404()
    
    # Görüntülenme sayısını artır
    article.view_count += 1
    db.session.commit()
    
    article_html = markdown_to_html(article.content)
    return render_template('share.html', article=article, article_html=article_html)


@app.route('/article/<article_id>/download')
def download_article(article_id):
    """Makaleyi Markdown dosyası olarak indir."""
    article = Article.query.get_or_404(article_id)
    
    # Markdown dosyası oluştur
    content = f"# {article.title}\n\n"
    content += f"**Konu:** {article.topic}  \n"
    content += f"**Tarih:** {article.created_at.strftime('%d.%m.%Y %H:%M')}  \n"
    if article.keywords:
        content += f"**Anahtar Kelimeler:** {article.keywords}  \n"
    content += f"\n---\n\n"
    content += article.content
    
    # Dosya adını oluştur
    filename = f"{article.topic.replace(' ', '_')[:50]}_{article.created_at.strftime('%Y%m%d')}.md"
    
    return Response(
        content,
        mimetype='text/markdown',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


@app.route('/article/<article_id>/delete', methods=['POST'])
@login_required
def delete_article(article_id):
    """Makaleyi sil."""
    article = Article.query.get_or_404(article_id)
    
    # Yetki kontrolü
    if session.get('user_id') != article.user_id and session.get('role') != 'admin':
        flash('Bu makaleyi silme yetkiniz yok.', 'danger')
        return redirect(url_for('articles_list'))
    
    db.session.delete(article)
    db.session.commit()
    
    flash('Makale silindi.', 'warning')
    return redirect(url_for('articles_list'))


# ===== TRENDING / COLLECTOR =====

@app.route('/trending')
def trending():
    """Dünya forumlarından popüler içerikleri göster."""
    # Kategorileri al
    selected_cats = request.args.getlist('category') or ['genel', 'teknoloji']
    limit = min(int(request.args.get('limit', 10)), 30)
    
    # İçerikleri topla
    results = collector.collect_all(categories=selected_cats, limit=limit)
    
    # Tüm içerikleri birleştir ve etkileşime göre sırala
    all_items = []
    for source, data in results.items():
        if isinstance(data, dict) and 'items' in data:
            all_items.extend(data['items'])
    
    all_items.sort(key=lambda x: x.get('engagement', 0), reverse=True)
    
    categories = collector.get_all_categories()
    
    return render_template('trending.html',
                           results=results,
                           all_items=all_items,
                           categories=categories,
                           selected_cats=selected_cats)


@app.route('/api/trending')
def api_trending():
    """API: Trend içerikleri JSON olarak döndür."""
    selected_cats = request.args.getlist('category') or ['genel', 'teknoloji']
    limit = min(int(request.args.get('limit', 10)), 30)
    results = collector.collect_all(categories=selected_cats, limit=limit)
    return results


# ===== API Endpoints =====

@app.route('/api/generate', methods=['POST'])
def api_generate():
    """API ile makale üret."""
    data = request.get_json()
    
    if not data or not data.get('topic'):
        return {'error': 'Konu gereklidir.'}, 400
    
    result = generator.generate(
        topic=data['topic'],
        tone=data.get('tone', 'profesyonel'),
        length=data.get('length', 'orta'),
        keywords=data.get('keywords', ''),
        target_audience=data.get('target_audience', 'Genel okuyucu'),
        custom_instructions=data.get('custom_instructions', '')
    )
    
    # Veritabanına kaydet
    article = Article(
        title=result['title'],
        content=result['content'],
        topic=data['topic'],
        tone=data.get('tone', 'profesyonel'),
        length=data.get('length', 'orta'),
        keywords=data.get('keywords', ''),
        target_audience=data.get('target_audience', 'Genel okuyucu'),
        word_count=result['word_count']
    )
    
    db.session.add(article)
    db.session.commit()
    
    return article.to_dict(), 201


@app.route('/api/articles')
def api_articles():
    """Tüm makaleleri listele."""
    articles = Article.query.order_by(Article.created_at.desc()).all()
    return {'articles': [a.to_dict() for a in articles]}


@app.route('/api/article/<article_id>')
def api_article(article_id):
    """Tek bir makaleyi getir."""
    article = Article.query.get_or_404(article_id)
    return article.to_dict()


# ===== Hata Sayfaları =====

@app.errorhandler(404)
def not_found(e):
    return render_template('base.html', content='<h2>404 - Sayfa Bulunamadı</h2>'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('base.html', content='<h2>500 - Sunucu Hatası</h2>'), 500


# ===== Uygulama Başlat =====
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
