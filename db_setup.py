from login_app import *

with app.app_context():
	db.create_all()
