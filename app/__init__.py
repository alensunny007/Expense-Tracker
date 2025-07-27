from flask import Flask
from .config import config
from .extensions import db,login_manager
from .auth import auth_bp
from .main import main_bp
def create_app(config_name='default'):
    app=Flask(__name__)
    app.config.from_object(config[config_name])
    
    db.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(auth_bp,url_prefix='/auth')
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()
    return app
