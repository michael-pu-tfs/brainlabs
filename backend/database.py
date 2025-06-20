import sqlite3
from contextlib import contextmanager
import os
import datetime
import shutil
import time
import threading
import schedule
import sqlalchemy
from sqlalchemy import create_engine

# Configuration
DB_CONFIG = {"dbname": "tf-db.sqlite", "backup_dir": "backups"}


def backup_to_cloud_storage():
    from google.cloud import storage

    client = storage.Client()  # No need to specify credentials
    bucket = client.bucket("db-backup")
    blob = bucket.blob(
        f"db-backups/tf-db-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.sqlite"
    )

    # Upload the DB file to Cloud Storage
    blob.upload_from_filename(DB_CONFIG["dbname"])


@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = sqlite3.connect(DB_CONFIG["dbname"])
        conn.row_factory = sqlite3.Row  # This mimics RealDictCursor behavior
        yield conn
    finally:
        if conn is not None:
            conn.close()


@contextmanager
def get_db_cursor():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        finally:
            cursor.close()


def dict_factory(cursor, row):
    """Convert sqlite3.Row to dictionary (mimics RealDictCursor)"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def init_db():
    """Initialize database tables"""
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                hashed_password TEXT,
                is_active INTEGER DEFAULT 1,
                is_google_account INTEGER DEFAULT 0
            )
        """
        )


def test_db_connection():
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT 1")
            print("Database connection test successful")
            return True
    except Exception as e:
        print(f"Database connection test failed: {str(e)}")
        return False


def create_db_backup():
    """Create a backup of the SQLite database"""
    try:
        # Ensure backup directory exists
        if not os.path.exists(DB_CONFIG["backup_dir"]):
            os.makedirs(DB_CONFIG["backup_dir"])

        # Generate backup filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{DB_CONFIG['backup_dir']}/tf-db_backup_{timestamp}.sqlite"

        # Copy the database file to create a backup
        shutil.copy2(DB_CONFIG["dbname"], backup_filename)

        print(f"Database backup created: {backup_filename}")

        # Optional: Remove old backups (keep last 7 for example)
        cleanup_old_backups(7)

        return True
    except Exception as e:
        print(f"Database backup failed: {str(e)}")
        return False


def cleanup_old_backups(keep_count):
    """Remove old backups, keeping only the most recent ones"""
    try:
        if not os.path.exists(DB_CONFIG["backup_dir"]):
            return

        # List all backup files
        backup_files = [
            os.path.join(DB_CONFIG["backup_dir"], f)
            for f in os.listdir(DB_CONFIG["backup_dir"])
            if f.startswith("tf-db_backup_") and f.endswith(".sqlite")
        ]

        # Sort by modification time (newest first)
        backup_files.sort(key=os.path.getmtime, reverse=True)

        # Remove older backups
        for old_backup in backup_files[keep_count:]:
            os.remove(old_backup)
            print(f"Removed old backup: {old_backup}")

    except Exception as e:
        print(f"Cleanup of old backups failed: {str(e)}")


def schedule_daily_backup():
    """Schedule a daily backup at midnight"""
    schedule.every().day.at("00:00").do(create_db_backup)

    # Run the scheduler in a background thread
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    # Start the scheduler thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    # backup_to_cloud_storage()
    print("Daily database backup scheduled for 12:00 AM")


def connect_sqlalchemy() -> sqlalchemy.engine.base.Engine:
    """Initialize SQLAlchemy engine for SQLite database"""
    engine = create_engine(f"sqlite:///{DB_CONFIG['dbname']}")
    return engine


# Start the backup scheduler when the module is imported
schedule_daily_backup()

# Initialize the database if it doesn't exist
if not os.path.exists(DB_CONFIG["dbname"]):
    init_db()
    print(f"Database initialized: {DB_CONFIG['dbname']}")
