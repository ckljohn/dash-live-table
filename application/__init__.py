"""Initialize app."""
from flask import Flask

"""Construct the core application."""
app = Flask(__name__,
            instance_relative_config=False)
# app.config.from_object('config.Config')

with app.app_context():

    # Import main Blueprint
    from application import routes
    app.register_blueprint(routes.main_bp, url_prefix='/dash-apps')

    # Import Dash application
    from application.dash_application import tcpdump
    app = tcpdump.add_dash(app)

    # Compile assets
    # from application.assets import compile_assets
    # compile_assets(app)
