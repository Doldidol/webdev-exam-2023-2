
import sqlalchemy as sa
from flask import url_for, current_app
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.dialects.mysql import YEAR
import markdown
import bleach
from app import db

books_genres = db.Table(
    "books_genres",
    db.Column("book_id", db.Integer, db.ForeignKey("books.id")),
    db.Column("genre_id", db.Integer, db.ForeignKey("genres.id")),
)


class Book(db.Model):

    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    short_desc = db.Column(db.Text, nullable=False)
    year_release = db.Column(YEAR, nullable=False)
    publisher = db.Column(db.String(256), nullable=False)
    author = db.Column(db.String(256), nullable=False)
    pages_volume = db.Column(db.Integer, nullable=False)
    image_id = db.Column(db.String(256), db.ForeignKey(
        "images.id"), nullable=False)
    rating_sum = db.Column(db.Integer, nullable=False, default=0)
    rating_num = db.Column(db.Integer, nullable=False, default=0)
    genres = db.relationship(
        "Genre", secondary=books_genres, backref="bookss")
    image = db.relationship("Image")

    def prepare_to_save(self):
        self.short_desc = bleach.clean(self.short_desc)

    def prepare_to_html(self):
        self.short_desc = markdown.markdown(self.short_desc)

    @property
    def rating(self):
        if self.rating_num > 0:
            return self.rating_sum / self.rating_num
        return 0

    def __repr__(self):
        return "<Book %r>" % self.name


class Genre(db.Model):

    __tablename__ = "genres"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True, nullable=False)

    def __repr__(self):
        return "<Genre %r>" % self.name


class Image(db.Model):

    __tablename__ = "images"

    id = db.Column(db.String(256), primary_key=True)
    file_name = db.Column(db.String(256), nullable=False)
    mime_type = db.Column(db.String(256), nullable=False)
    md5_hash = db.Column(db.String(256), nullable=False, unique=True)

    @property
    def url(self):
        return url_for("image", image_id=self.id)

    def __repr__(self):
        return "<Image %r>" % self.file_name


class Review(db.Model):

    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    rating = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False,
                           server_default=sa.sql.func.now())

    user = db.relationship("User")
    book = db.relationship("Book")

    def prepare_to_save(self):
        self.text = bleach.clean(self.text)

    def prepare_to_html(self):
        self.text = markdown.markdown(self.text)

    def __repr__(self):
        return "<Review %r>" % self.user_id


class User(db.Model, UserMixin):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(256), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    last_name = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(256), nullable=False)
    middle_name = db.Column(db.String(256))
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)

    role = db.relationship("Role")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        return " ".join([self.last_name,
                         self.first_name,
                         self.middle_name or ""])

    def __repr__(self):
        return "<User %r>" % self.login


class Role(db.Model):

    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return "<Role %r>" % self.name


class BookVisits(db.Model):

    __tablename__ = "book_visits"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False,
                           server_default=sa.sql.func.now())

    book = db.relationship("Book")
    user = db.relationship("User")

    def __repr__(self):
        return "<VisitLog %r>" % self.id
