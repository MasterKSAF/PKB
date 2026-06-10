import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

def load_data():
    # 1. Load env from parent directory
    base_dir = Path(__file__).parent.parent
    dotenv_path = base_dir / '.env'
    if not dotenv_path.exists():
        print(f"Error: .env file not found at {dotenv_path}")
        sys.exit(1)
    
    load_dotenv(dotenv_path=dotenv_path, override=True)
    
    # 2. Get database credentials
    username = os.getenv('DB_USERNAME')
    password = os.getenv('DB_PASSWORD')
    host = os.getenv('DB_HOST')
    port = os.getenv('DB_PORT')
    database = os.getenv('DB_DATABASE')
    
    if not all([username, password, host, port, database]):
        print("Error: Missing database credentials in .env")
        sys.exit(1)
        
    database_url = f'postgresql+psycopg://{username}:{password}@{host}:{port}/{database}'
    print(f"Connecting to database '{database}' on host '{host}:{port}'...")
    
    engine = create_engine(database_url)
    
    # 3. Read init_data.sql
    init_data_path = Path(__file__).parent / 'init_data.sql'
    if not init_data_path.exists():
        print(f"Error: init_data.sql file not found at {init_data_path}")
        sys.exit(1)
        
    with open(init_data_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
        
    # Split sql statements (simple semicolon splitting, ignoring empty lines)
    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
    
    print(f"Found {len(statements)} SQL statements to execute.")
    
    # 4. Execute statements
    try:
        with engine.begin() as conn:
            for i, stmt in enumerate(statements, 1):
                conn.execute(text(stmt))
                if i % 200 == 0:
                    print(f"Executed {i}/{len(statements)} statements...")
        print("Data loaded successfully!")
    except Exception as e:
        print(f"Error executing SQL statements: {e}")
        sys.exit(1)

if __name__ == '__main__':
    load_data()
