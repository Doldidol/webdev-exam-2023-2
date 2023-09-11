from flask import Flask, render_template, request, redirect, session, url_for, flash, abort, send_from_directory
from flask_login import login_required, current_user
from sqlalchemy import MetaData
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from datetime import datetime, timedelta

app = Flask(__name__)
application = app

app.config.from_pyfile('config.py')

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(app, metadata=metadata)
migrate = Migrate(app, db)

from models import Book, Genre, Image, Review, BookVisits, LastBookVisits
from auth import init_login_manager, check_rights, bp as auth_bp
from reviews import bp as reviews_bp
from logs import bp as logs_bp

init_login_manager(app)

app.register_blueprint(auth_bp)
app.register_blueprint(reviews_bp)
app.register_blueprint(logs_bp)


# Функция для получнеия последних 5 книг
# Функция нужна, для корректного отображения
# для анонимных пользователей
def get_five_last_books():
    # Если пользователь вошел в систему
    if current_user.is_authenticated:
        # Получаем последние 5 книг
        last_books = (LastBookVisits.query
                            .filter_by(user_id=current_user.id)
                            .order_by(LastBookVisits.created_at.desc())
                            .limit(5)
                            .all())
    else:
        last_books = session.get("last_books")
    result = []
    if last_books:
        if current_user.is_authenticated:
            for book_log in last_books:
                result.append(Book.query.get(book_log.book_id))
        else:
            for book_log in last_books:
                result.append(Book.query.get(book_log))
    return result

def get_top_five_books():
    start_time = datetime.now() - timedelta(days=3 * 30)
    top_five_books = (db.session
                        .query(BookVisits.book_id, db.func.count(BookVisits.id))
                        .filter(start_time <= BookVisits.created_at)
                        .group_by(BookVisits.book_id)
                        .order_by(db.func.count(BookVisits.id).desc())
                        .limit(5).all())
    result = []
    for i, book_item in enumerate(top_five_books):
        book = Book.query.get(top_five_books[i][0])
        result.append((book, top_five_books[i][1]))
    return result

@app.route('/')
def index():
    last_books = get_five_last_books()
    top_five_books = get_top_five_books()

    page = request.args.get('page', 1, type=int)
    books = Book.query.order_by(Book.id.desc())
    pagination = books.paginate(page=page, per_page=app.config['PER_PAGE'])
    books = pagination.items
    if last_books == [None, None]:
        last_books = []
    return render_template("index.html", pagination=pagination, books=books,
                           last_books = last_books,
                           top_five_books = top_five_books)

@app.route('/images/<image_id>')
def image(image_id):
    img = Image.query.get(image_id)
    if img is None:
        abort(404)
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               img.file_name)

from tool import ImageSaver

def extract_params(dict):
    return {p: request.form.get(p) for p in dict}

BOOKS_PARAMS = [
    'name', 'author', 'publisher', 'year_release', 'pages_volume',
    'short_desc',
]

@app.route('/new', methods=["POST", "GET"])
@login_required
@check_rights('create')
def new():
    if request.method == "POST":
        f = request.files.get('background_img')
        if f and f.filename:
            img = ImageSaver(f).save()
            params = extract_params(BOOKS_PARAMS)
            params['year_release'] = int(params['year_release'])
            params['pages_volume'] = int(params['pages_volume'])
            genres = request.form.getlist('genres')
            genres_list = []
            for i in genres:
                genre = Genre.query.filter_by(id=i).first()
                genres_list.append(genre)

            book = Book(**params, image_id=img.id)
            book.prepare_to_save()
            book.genres = genres_list
            try:
                db.session.add(book)
                db.session.commit()
                flash('Книга успешно добавлена', 'success')
                return redirect(url_for('index'))
            except:
                db.session.rollback()
                flash(
                    'При сохранении данных возникла ошибка. Проверьте корректность введённых данных.', 'success')

        if not (f and f.filename):
            flash('У книги должна быть обложка', 'danger')
    
    '''
    Сохранение книги в базу данных
    '''
    
    
    genres = Genre.query.all()
    return render_template('books/create_edit.html',
                        action_category='create',
                        genres=genres,
                        book={})


@app.route('/<int:book_id>/edit', methods=["POST", "GET"])
@login_required
@check_rights('edit')
def edit(book_id):
    if request.method == "POST":
        params = extract_params(BOOKS_PARAMS)
        params['year_release'] = int(params['year_release'])
        params['pages_volume'] = int(params['pages_volume'])
        genres = request.form.getlist('genres')
        genres_list = []
        book = Book.query.get(book_id)
        book.name = params['name']
        book.author = params['author']
        book.publisher = params['publisher']
        book.year_release = params['year_release']
        book.pages_volume = params['pages_volume']
        book.short_desc = params['short_desc']

        for i in genres:
            genre = Genre.query.filter_by(id=i).first()
            genres_list.append(genre)
        book.genres = genres_list
        try:
            db.session.add(book)
            db.session.commit()
            flash('Книга успешно обновлена', 'success')
            return redirect(url_for('index'))
        except:
            db.session.rollback()

        flash('При обновления данных возникла ошибка. Проверьте корректность введённых данных.', 'danger')

    book = Book.query.get(book_id)
    genres = Genre.query.all()
    return render_template('books/create_edit.html',
                           action_category='edit',
                           genres=genres,
                           book=book,)


# Удаление книги

@app.route('/<int:book_id>/delete', methods=['POST'])
@login_required
@check_rights('delete')
def delete(book_id):
    book = Book.query.get(book_id)
    # Проверка зависимости у обложки
    references = len(Book.query.filter_by(image_id=book.image.id).all())
       
    try:
         # Удаление всех зависимостей
        for item in BookVisits.query.filter_by(book_id=book_id):
            db.session.delete(item)
        for item in LastBookVisits.query.filter_by(book_id=book_id):
            db.session.delete(item)
        for item in Review.query.filter_by(book_id=book_id):
            db.session.delete(item)

        db.session.delete(book)
        # Если зависимость единственная, то обложку можно удалить
        if references == 1:
            image = Image.query.get(book.image.id)
            delete_path = os.path.join(
                app.config['UPLOAD_FOLDER'],
                image.file_name)
            db.session.delete(image)
            os.remove(delete_path)
        db.session.commit()
        flash('Удаление книги прошло успешно', 'success')
    except:
        db.session.rollback()
        flash('Во время удаления книги произошла ошибка', 'danger')

    return redirect(url_for('index'))

# Просмотр книги
@app.route('/<int:book_id>')
def show(book_id):
    book = Book.query.get(book_id)
    book.prepare_to_html()
    # Получаем все рецензии
    reviews = Review.query.filter_by(book_id=book_id)
    # Каждую из рецензий подготавливаем для отображения
    for review in reviews:
        review.prepare_to_html()
    # Заглушка, т.к. у пользователя может не быть рецензии
    user_review = None
    # Если у пользователя есть идентификатор
    if current_user.get_id():
        # Извлекаем рецензии пользователя
        user_review = reviews.filter_by(user_id=current_user.id).first()
    # Получаем все рецензии
    reviews.all()
    return render_template('books/show.html',
                           book=book,
                           reviews=reviews,
                           user_review=user_review)


#  Создание логов для книги
def creating_book_visits(user_id, book_id):
    try:
        visit_log_params = {
            'user_id': user_id,
            'book_id': book_id,
        }
        db.session.add(BookVisits(**visit_log_params))
        db.session.commit()
    except:
        db.session.rollback()


def creating_last_book_log(book_id, user_id):
    new_log = None

    # Извлекаем данные, когда пользователь последний раз получал доступ
    book_log = (LastBookVisits.query
                   # Фильтруем по конкретной книге
                   .filter_by(book_id=book_id)  
                   # Фильтруем по конкретному пользователю
                   .filter_by(user_id=current_user.id) 
                   .first())
    if book_log:
        # У найденой записи обновляем время доступа
        book_log.created_at = db.func.now()
    # Если пользователь еще не получал доступа к книге,
    # то создаем новую запись
    else:
        new_log = LastBookVisits(book_id=book_id, user_id=user_id)
   
    # Если была создана запись
    if new_log:
        try:
            db.session.add(new_log)
            db.session.commit()
        except:
            db.session.rollback()


def save_last_books(book_id):
    data_from_cookies = session.get('last_books')

    if data_from_cookies:
        if book_id in data_from_cookies:
            data_from_cookies.remove(book_id)
            data_from_cookies.insert(0, book_id)
        else:
            data_from_cookies.insert(0, book_id)
    
    # Если логов ранее не было сохранено
    if not data_from_cookies:
        data_from_cookies = [book_id]

    session['last_books'] = data_from_cookies

@app.before_request
def loger():
    if (request.endpoint == 'static'
        or request.endpoint == 'image'
            or request.endpoint == 'users_statistics'):
        return
    if request.endpoint == 'show':
        # Если пользователь анонимен, то необходимо
        # лог запись сохранять в куки
        if current_user.is_anonymous:
            save_last_books(request.view_args.get('book_id'))
        if current_user.is_authenticated:
            creating_last_book_log(request.view_args.get('book_id'),
                                   current_user.id)
        book_visit_logs_params = {
            'user_id': current_user.get_id(),
            'book_id': request.view_args.get('book_id'),
        }
        start = datetime.now() - timedelta(days=1)
        today_visits = (BookVisits.query
                        .filter_by(book_id=request.view_args.get('book_id'))
                        .filter(start <= BookVisits.created_at))
        if current_user.is_authenticated:
            today_visits = today_visits.filter_by(
                user_id=current_user.get_id())
        else:
            today_visits = today_visits.filter(BookVisits.user_id.is_(None))
        today_visits_int = len(today_visits.all())
        # < 10, т.к. нумерация идет с 0
        if today_visits_int < 10:
            try:
                db.session.add(BookVisits(**book_visit_logs_params))
                db.session.commit()
            except:
                db.session.rollback()
    
