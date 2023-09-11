from flask import Blueprint, render_template, request
from flask_login import login_required
from app import db, app
from models import BookVisits, Book
from auth import check_rights

bp = Blueprint('logs', __name__, url_prefix='/logs')


# Статистика по пользователям
@bp.route('/users_statistics')
@login_required
@check_rights('get_logs')
def users_statistics():
    page = request.args.get('page', 1, type=int)
    logs = BookVisits.query.order_by(BookVisits.created_at.desc())
    pagination = logs.paginate(page=page, per_page=app.config['LOGS_PER_PAGE'])
    logs = pagination.items
    return render_template('logs/users_statistics.html',
                           logs=logs,
                           pagination=pagination)


# Статистика по книгам
@bp.route('/books_statistics')
@login_required
@check_rights('get_logs')
def books_statistics():
    page = request.args.get('page', 1, type=int)
    books_stat_data = db.session.query(BookVisits.book_id, db.func.count(BookVisits.id)).group_by(BookVisits.book_id).order_by(db.func.count(BookVisits.id).desc())
    pagination = books_stat_data.paginate(page=page, per_page=app.config['LOGS_PER_PAGE'])
    books_stat_data = pagination.items
    data_for_render = []
    for book_id, count in  books_stat_data:
        data_for_render.append((Book.query.get(book_id), count))

    print(data_for_render)
    
    return render_template('logs/books_statistics.html',
                           logs=data_for_render,
                           pagination=pagination)