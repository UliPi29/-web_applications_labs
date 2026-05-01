from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, Regexp, EqualTo, ValidationError
from models import User
from models import Role

# проверка сложности пароля
def validate_password_complexity(password):
    errors = []
    if not any(c.isupper() for c in password):
        errors.append('должна быть хотя бы одна заглавная буква')
    if not any(c.islower() for c in password):
        errors.append('должна быть хотя бы одна строчная буква')
    allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя0123456789~!?@#$%^&*_-+()[]{}><\/|'\".,:;")
    for ch in password:
        if ch not in allowed_chars:
            errors.append(f'недопустимый символ: {ch}')
            break
    if not any(c.isdigit() for c in password):
        errors.append('должна быть хотя бы одна цифра')
    if ' ' in password:
        errors.append('не должен содержать пробелов')
    return errors

class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember = BooleanField('Запомнить меня')

class UserCreateForm(FlaskForm):
    username = StringField('Логин', validators=[
        DataRequired(message='Поле не может быть пустым'),
        Length(min=5, message='Логин должен быть не менее 5 символов'),
        Regexp('^[A-Za-z0-9]+$', message='Логин должен состоять только из латинских букв и цифр')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Поле не может быть пустым'),
        Length(min=8, max=128, message='Пароль должен быть от 8 до 128 символов')
    ])
    last_name = StringField('Фамилия', validators=[DataRequired(message='Поле не может быть пустым')])
    first_name = StringField('Имя', validators=[DataRequired(message='Поле не может быть пустым')])
    middle_name = StringField('Отчество')
    role_id = SelectField('Роль', coerce=int, choices=[], validate_choice=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role_id.choices = [(0, '--- Выберите роль ---')] + [(r.id, r.name) for r in Role.query.all()]

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Пользователь с таким логином уже существует')

    def validate_password(self, field):
        errors = validate_password_complexity(field.data)
        if errors:
            raise ValidationError('; '.join(errors))

class UserEditForm(FlaskForm):
    last_name = StringField('Фамилия', validators=[DataRequired(message='Поле не может быть пустым')])
    first_name = StringField('Имя', validators=[DataRequired(message='Поле не может быть пустым')])
    middle_name = StringField('Отчество')
    role_id = SelectField('Роль', coerce=int, choices=[], validate_choice=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role_id.choices = [(0, '--- Выберите роль ---')] + [(r.id, r.name) for r in Role.query.all()]

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Старый пароль', validators=[DataRequired()])
    new_password = PasswordField('Новый пароль', validators=[
        DataRequired(),
        Length(min=8, max=128, message='Пароль должен быть от 8 до 128 символов')
    ])
    confirm_password = PasswordField('Повторите новый пароль', validators=[
        DataRequired(),
        EqualTo('new_password', message='Пароли не совпадают')
    ])

    def validate_new_password(self, field):
        errors = validate_password_complexity(field.data)
        if errors:
            raise ValidationError('; '.join(errors))