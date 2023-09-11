from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required
from app import db
from models import Review, Book
from auth import check_rights

bp = Blueprint('reviews', __name__, url_prefix='/reviews')

@bp.route('/<int:book_id>/new', methods=["POST", "GET"])
@login_required
@check_rights('review')
def new(book_id):
    # Получаем отзыв пользователя 
    review = Review.query.filter_by(user_id=current_user.id).filter_by(book_id=book_id).all()
    if request.method == "POST":
        # Если рецензия не была написана
        if not review:
            params = {
                'book_id': book_id,
                'user_id': current_user.id,
                'rating': request.form.get('rating'),
                'text': request.form.get('text'),
            }
            review = Review(**params)
            review.prepare_to_save()

            try:

                book = Book.query.filter_by(id=book_id).first()   
                book.rating_sum += int(params['rating'])
                book.rating_num += 1
                db.session.add(review)
                db.session.add(book)
                db.session.commit()
                flash('Рецензия успешно опубликована', 'success')
            except:
                db.session.rollback()
                flash('Во время публикации рецензии проихошла ошибка', 'danger')
                return render_template('reviews/create_edit.html', book_id=book_id)
        else:
            flash('Вы уже оставили рецензию к этой книге', 'warning')
        return redirect(url_for('show', book_id=book_id))

    # Если рецензия уже существует
    if review:
        flash('Вы уже оставили рецензию к этой книге', 'warning')
        return redirect(url_for('show', book_id=book_id))
    return render_template('reviews/create_edit.html', book_id=book_id)
  
