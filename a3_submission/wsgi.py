from app.app import app, init_db

# Ensure database tables exist when the process boots on hosted platforms.
init_db()
