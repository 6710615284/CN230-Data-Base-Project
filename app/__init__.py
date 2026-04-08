from flask import Flask
from app.config import Config


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(Config)

    from app.routes.auth   import auth_bp
    from app.routes.doctor import doctor_bp
    from app.routes.lab    import lab_bp
    from app.routes.admin  import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(doctor_bp, url_prefix='/doctor')
    app.register_blueprint(lab_bp,    url_prefix='/lab')
    app.register_blueprint(admin_bp,  url_prefix='/admin')

    return app
