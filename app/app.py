from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy import MetaData
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

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

from models import Book, Genre
from auth import init_login_manager, check_rights, bp as auth_bp

init_login_manager(app)

app.register_blueprint(auth_bp)

@app.route('/')
def index():
    return render_template("index.html")

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