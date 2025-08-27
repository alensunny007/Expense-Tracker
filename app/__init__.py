from flask import Flask
from .config import config
from .extensions import db,login_manager,mail
from .auth import auth_bp
from .main import main_bp
from flask_migrate import Migrate
from .services import DueExpenseMonitor
migrate=Migrate()
due_monitor=None
def create_app(config_name='default'):
    app=Flask(__name__)
    app.config.from_object(config[config_name])
    
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app,db)
    mail.init_app(app)

    app.register_blueprint(auth_bp,url_prefix='/auth')
    app.register_blueprint(main_bp)
    global due_monitor
    due_monitor=DueExpenseMonitor(app)
    due_monitor.start_monitoring()

    return app
