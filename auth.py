"""
Authentication Middleware
Kullanıcı kimlik doğrulama ve yetkilendirme dekoratörleri
"""

from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(f):
    """
    Oturum açmış kullanıcı gerektirir.
    Açmamışsa login sayfasına yönlendirir.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Bu sayfayı görüntülemek için giriş yapmalısınız.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Admin yetkisi gerektirir.
    Değilse ana sayfaya yönlendirir.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Bu sayfayı görüntülemek için giriş yapmalısınız.', 'warning')
            return redirect(url_for('login'))
        
        if session.get('role') != 'admin':
            flash('Bu işlem için admin yetkisi gereklidir.', 'danger')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function


def editor_or_admin_required(f):
    """
    Editor veya Admin yetkisi gerektirir.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Bu sayfayı görüntülemek için giriş yapmalısınız.', 'warning')
            return redirect(url_for('login'))
        
        user_role = session.get('role')
        if user_role not in ['admin', 'editor']:
            flash('Bu işlem için editor veya admin yetkisi gereklidir.', 'danger')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function
