from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user
from models import ROLE_PERMISSIONS

def check_rights(*required_permissions):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('У вас недостаточно прав для доступа к данной странице.', 'danger')
                return redirect(url_for('index'))
            # получаем роль
            role_name = current_user.role.name if current_user.role else None
            user_permissions = ROLE_PERMISSIONS.get(role_name, set())
            # проверяем права
            if not all(perm in user_permissions for perm in required_permissions):
                flash('У вас недостаточно прав для доступа к данной странице.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator