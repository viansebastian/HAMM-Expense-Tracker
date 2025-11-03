# API Controller file
import models
from db import engine
from flask import Flask
from controllers.user_controller import user_bp
from controllers.transact_controller import transact_bp
from controllers.budget_controller import budget_bp
from controllers.category_controller import category_bp


app = Flask(__name__)

# # create tables if not exist
models.Base.metadata.create_all(bind=engine)

# Register Blueprints
app.register_blueprint(user_bp)
app.register_blueprint(transact_bp)
app.register_blueprint(category_bp)
app.register_blueprint(budget_bp)
    

if __name__ == "__main__":
    app.run(debug=True)
