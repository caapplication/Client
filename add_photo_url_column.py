"""
Script to add photo_url column to clients table
Run this once to update the database schema
"""
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("Error: DATABASE_URL not found in environment variables")
    sys.exit(1)

try:
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if column already exists
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='clients' AND column_name='photo_url'
        """)
        result = conn.execute(check_query)
        if result.fetchone():
            print("Column 'photo_url' already exists in 'clients' table")
        else:
            # Add the column
            alter_query = text("""
                ALTER TABLE clients 
                ADD COLUMN photo_url VARCHAR
            """)
            conn.execute(alter_query)
            conn.commit()
            print("Successfully added 'photo_url' column to 'clients' table")
    
    print("Database migration completed successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

