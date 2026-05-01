import re
from flask import Flask, render_template, request, make_response, redirect, url_for

app = Flask(__name__)

def validate_phone(phone_str):
    allowed = set('0123456789 ()-.+')
    for ch in phone_str:
        if ch not in allowed:
            return False, "Недопустимый ввод. В номере телефона встречаются недопустимые символы.", None
    digits = re.findall(r'\d', phone_str)
    num_digits = len(digits)
    stripped = phone_str.strip()
    if stripped.startswith('+7') or stripped.startswith('8'):
        expected = 11
    else:
        expected = 10
    if num_digits != expected:
        return False, "Недопустимый ввод. Неверное количество цифр.", None
    if expected == 11:
        digits = digits[1:]
    digits_with_8 = ['8'] + digits
    formatted = (
        f"{digits_with_8[0]}-"
        f"{''.join(digits_with_8[1:4])}-"
        f"{''.join(digits_with_8[4:7])}-"
        f"{''.join(digits_with_8[7:9])}-"
        f"{''.join(digits_with_8[9:11])}"
    )
    return True, None, formatted


@app.route('/')
def index():
    return redirect(url_for('request_data'))


@app.route('/request-data', methods=['GET', 'POST'])
def request_data():
    if request.method == 'POST' and 'username' in request.form:
        username = request.form.get('username')
        resp = make_response(render_template('request_data.html'))
        if username:
            resp.set_cookie('auth_user', username)
        return resp
    return render_template('request_data.html')


@app.route('/phone', methods=['GET', 'POST'])
def phone():
    if request.method == 'POST':
        phone_number = request.form.get('phone', '')
        valid, error_msg, formatted = validate_phone(phone_number)
        if not valid:
            return render_template('phone.html', error=error_msg)
        else:
            return render_template('phone.html', formatted_number=formatted)
    return render_template('phone.html')


if __name__ == '__main__':
    app.run(debug=True)