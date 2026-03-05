from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')  # admin, editor, user
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # İlişkiler
    articles = db.relationship('Article', backref='author', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Şifreyi hashleyerek sakla."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Şifreyi kontrol et."""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.strftime('%d.%m.%Y %H:%M')
        }


class Article(db.Model):
    __tablename__ = 'articles'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    tone = db.Column(db.String(50), default='profesyonel')
    length = db.Column(db.String(20), default='orta')
    keywords = db.Column(db.String(500), default='')
    target_audience = db.Column(db.String(200), default='genel')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Nullable for backward compatibility
    
    # Meta bilgiler
    word_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=False)
    share_slug = db.Column(db.String(100), unique=True, nullable=True)
    view_count = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<Article {self.title[:50]}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'topic': self.topic,
            'tone': self.tone,
            'length': self.length,
            'keywords': self.keywords,
            'target_audience': self.target_audience,
            'word_count': self.word_count,
            'created_at': self.created_at.strftime('%d.%m.%Y %H:%M'),
            'is_published': self.is_published,
            'share_slug': self.share_slug,
            'view_count': self.view_count,
            'author': self.author.username if self.author else None
        }


class ArticleTemplate(db.Model):
    __tablename__ = 'templates'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    prompt_template = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), default='genel')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Template {self.name}>'
