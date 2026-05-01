from flask import flash, redirect, render_template, request, Response, url_for
from flask_login import login_required, current_user
import csv
from io import StringIO
from models import VisitLog, User, ROLE_PERMISSIONS, db
from decorators import check_rights
from . import bp

@bp.route('/visits')
@login_required
def visit_logs():
    # админ (view_visit_logs) | пользователь (view_own_visit_logs)
    if not (current_user.has_permission('view_visit_logs') or 
            current_user.has_permission('view_own_visit_logs')):
        flash('У вас недостаточно прав для доступа к данной странице.', 'danger')
        return redirect(url_for('index'))

    page = request.args.get('page', 1, type=int)
    per_page = 10

    if current_user.has_permission('view_visit_logs'):
        # админ видит все записи
        query = VisitLog.query.order_by(VisitLog.created_at.desc())
    else:
        # обычный только свои записи
        query = VisitLog.query.filter_by(user_id=current_user.id).order_by(VisitLog.created_at.desc())

    logs = query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template('reports/visit_logs.html', logs=logs)

@bp.route('/stats/pages')
@login_required
@check_rights('view_stats')
def page_stats():
    # статистика по страницам
    from sqlalchemy import func
    stats = db.session.query(
        VisitLog.path,
        func.count(VisitLog.id).label('count')
    ).group_by(VisitLog.path).order_by(func.count(VisitLog.id).desc()).all()
    return render_template('reports/page_stats.html', stats=stats)

@bp.route('/stats/users')
@login_required
@check_rights('view_stats')
def user_stats():
    # статистика по пользователям
    from sqlalchemy import func
    stats = db.session.query(
        VisitLog.user_id,
        func.count(VisitLog.id).label('count')
    ).group_by(VisitLog.user_id).order_by(func.count(VisitLog.id).desc()).all()
    # user_id - ФИО | "Неаутентифицированный пользователь"
    results = []
    for user_id, cnt in stats:
        if user_id is None:
            user_name = "Неаутентифицированный пользователь"
        else:
            user = User.query.get(user_id)
            user_name = f"{user.last_name or ''} {user.first_name} {user.middle_name or ''}".strip() or user.username
        results.append((user_name, cnt))
    return render_template('reports/user_stats.html', stats=results)

@bp.route('/export/pages.csv')
@login_required
@check_rights('view_stats')
def export_pages_csv():
    from sqlalchemy import func
    stats = db.session.query(
        VisitLog.path,
        func.count(VisitLog.id).label('count')
    ).group_by(VisitLog.path).order_by(func.count(VisitLog.id).desc()).all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Страница', 'Количество посещений'])
    for path, count in stats:
        writer.writerow([path, count])
    output.seek(0)
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=page_stats.csv'}
    )

@bp.route('/export/users.csv')
@login_required
@check_rights('view_stats')
def export_users_csv():
    from sqlalchemy import func
    stats = db.session.query(
        VisitLog.user_id,
        func.count(VisitLog.id).label('count')
    ).group_by(VisitLog.user_id).order_by(func.count(VisitLog.id).desc()).all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Пользователь', 'Количество посещений'])
    for user_id, cnt in stats:
        if user_id is None:
            user_name = "Неаутентифицированный пользователь"
        else:
            user = User.query.get(user_id)
            user_name = f"{user.last_name or ''} {user.first_name} {user.middle_name or ''}".strip() or user.username
        writer.writerow([user_name, cnt])
    output.seek(0)
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=user_stats.csv'}
    )