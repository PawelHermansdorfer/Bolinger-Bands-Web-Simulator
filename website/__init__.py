from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'AA_PAWELEK'
    
    from .views import views
    from .error_handler import errors
    
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(errors, url_prefix='/')
    
    return app