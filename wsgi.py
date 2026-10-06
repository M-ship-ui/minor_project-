import os
from app import app
import seed_data
import database

# Ensure database is seeded and ready upon cloud initialization
if not os.path.exists(database.DB_PATH):
    print("Cloud Deployment: Initializing database and pre-seeding records...")
    seed_data.seed_all()

if __name__ == "__main__":
    app.run()
