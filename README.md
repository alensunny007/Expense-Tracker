add categories of expense in your database like this or you can use custom route or flask-migrate.

flask shell(command)
in flask shell

from app.models.category import Category
from app.extensions import db

categories=['Food','Transportation','Entertainment','Utilities','Healthcare','Education','Bills','Other']
for cat_name in categories:
    if not Category.query.filter_by(name=cat_name).first():
        category = Category(name=cat_name)
        db.session.add(category)

db.session.commit()
