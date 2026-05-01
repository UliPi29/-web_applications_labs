from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Для доступа к этой странице необходимо войти.'
login_manager.login_message_category = 'info'

users = {'user': {'password': 'qwerty'}}

class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(username):
    if username in users:
        return User(username)
    return None

@app.template_filter('pluralize')
def pluralize_visits(count):
    if count % 10 == 1:
        return 'раз'
    elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):
        return 'раза'
    else:
        return 'раз'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/counter')
def counter():
    if 'visits' in session:
        session['visits'] += 1
    else:
        session['visits'] = 1
    return render_template('counter.html', visits=session['visits'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user, remember=remember)
            flash('Вы успешно вошли!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Неверный логин или пароль', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/secret')
@login_required
def secret():
    return render_template('secret.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))