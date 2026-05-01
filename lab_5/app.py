import pytz
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Role, VisitLog
from forms import LoginForm, UserCreateForm, UserEditForm, ChangePasswordForm
from reports import bp as reports_bp
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.register_blueprint(reports_bp)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Для доступа к этой странице необходимо войти.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except ValueError:
        return None

# таблица + начальные данные при первом запросе
@app.before_request
def create_tables():
    if not hasattr(app, 'tables_created'):
        db.create_all()
        if Role.query.count() == 0:
            admin_role = Role(name='admin', description='Администратор')
            user_role = Role(name='user', description='Пользователь')
            db.session.add_all([admin_role, user_role])
            db.session.commit()
        else:
            admin_role = Role.query.filter_by(name='admin').first()
            user_role = Role.query.filter_by(name='user').first()

        if User.query.filter_by(username='admin').first() is None and admin_role:
            admin = User(username='admin', first_name='Admin', last_name='', role_id=admin_role.id)
            admin.set_password('Admin123!')  # сложный пароль
            db.session.add(admin)
            db.session.commit()
        app.tables_created = True

@app.before_request
def log_visit():
    if request.path.startswith('/static') or request.path.startswith('/reports/visits'):
        return
    user_id = current_user.id if current_user.is_authenticated else None
    log = VisitLog(path=request.path, user_id=user_id)
    db.session.add(log)
    db.session.commit()


@app.route('/')
def index():
    users = User.query.all()
    return render_template('index.html', users=users)

@app.route('/user/<int:user_id>')
def view_user(user_id):
    user = User.query.get_or_404(user_id)
    # не админ пытается посмотреть чужой профиль
    if not current_user.is_authenticated or (current_user.role.name != 'admin' and current_user.id != user_id):
        flash('У вас недостаточно прав для доступа к данной странице.', 'danger')
        return redirect(url_for('index'))
    return render_template('view_user.html', user=user)

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_user():
    form = UserCreateForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            last_name=form.last_name.data,
            first_name=form.first_name.data,
            middle_name=form.middle_name.data,
            role_id=form.role_id.data if form.role_id.data != 0 else None
        )
        user.set_password(form.password.data)
        try:
            db.session.add(user)
            db.session.commit()
            flash('Пользователь успешно создан', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при создании: {str(e)}', 'danger')
    return render_template('create_user.html', form=form)

@app.route('/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    # проверка прав: админ (edit_user) или владелец профиля (edit_own_profile)
    if not (current_user.has_permission('edit_user') or 
            (current_user.id == user_id and current_user.has_permission('edit_own_profile'))):
        flash('У вас недостаточно прав для доступа к данной странице.', 'danger')
        return redirect(url_for('index'))

    form = UserEditForm(obj=user)
    # пользователь не админ, удаляем поле выбора роли
    if not current_user.has_permission('edit_user'):
        del form.role_id

    if form.validate_on_submit():
        user.last_name = form.last_name.data
        user.first_name = form.first_name.data
        user.middle_name = form.middle_name.data
        # админ может менять роль
        if current_user.has_permission('edit_user'):
            user.role_id = form.role_id.data if form.role_id.data != 0 else None
        try:
            db.session.commit()
            flash('Данные пользователя обновлены', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении: {str(e)}', 'danger')
            return render_template('edit_user.html', form=form, user=user)
    return render_template('edit_user.html', form=form, user=user)

@app.route('/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    try:
        db.session.delete(user)
        db.session.commit()
        flash('Пользователь удалён', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении: {str(e)}', 'danger')
    return redirect(url_for('index'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.old_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Пароль успешно изменён', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверный старый пароль', 'danger')
    return render_template('change_password.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        print(f"Attempt login with username: {form.username.data}")
        user = User.query.filter_by(username=form.username.data).first()
        print(f"User found: {user}")
        if user:
            print(f"Password hash from DB: {user.password_hash}")
            print(f"Password check result: {user.check_password(form.password.data)}")
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash('Вы успешно вошли!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Неверный логин или пароль', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

@app.template_filter('localdatetime')
def localdatetime_filter(value, format='%d.%m.%Y %H:%M:%S'):
    if value is None:
        return ''
    tz = pytz.timezone('Europe/Moscow')
    value_utc = value.replace(tzinfo=pytz.utc)
    value_local = value_utc.astimezone(tz)
    return value_local.strftime(format)

if __name__ == '__main__':
    app.run(debug=True)