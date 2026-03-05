import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'makale-gizli-anahtar-2026')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///makaleler.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # OpenAI API Ayarları
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o')
    
    # Makale Ayarları
    DEFAULT_LANGUAGE = 'tr'
    MAX_ARTICLE_LENGTH = 5000
    MIN_ARTICLE_LENGTH = 500
