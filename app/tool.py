import hashlib
import uuid
import os
from werkzeug.utils import secure_filename
from models import Image
from app import db, app

class ImageSaver:
    def __init__(self, file):
        self.file = file

    def save(self):
        self.img = self.__find_by_md5_hash()
        if self.img is not None:
            return self.img
        _, file_extension = os.path.splitext(self.file.filename)
        uniq_id_name = str(uuid.uuid4())
        self.img = Image(
            id=uniq_id_name,
            file_name=uniq_id_name + file_extension,
            mime_type=self.file.mimetype,
            md5_hash=self.md5_hash)
        self.file.save(
            os.path.join(app.config['UPLOAD_FOLDER'],
                         self.img.file_name))
        db.session.add(self.img)
        db.session.commit()
        return self.img

    def __find_by_md5_hash(self):
        self.md5_hash = hashlib.md5(self.file.read()).hexdigest()
        self.file.seek(0)
        return Image.query.filter(Image.md5_hash == self.md5_hash).first()
