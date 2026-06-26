import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

def load_data():
    # 1. Load env from parent directory
    base_dir = Path(__file__).parent.parent
    dotenv_path = base_dir / '.env'
    if not dotenv_path.exists():
        raise FileNotFoundError(f"Error: .env file not found at {dotenv_path}")
    
    load_dotenv(dotenv_path=dotenv_path, override=True)
    
    # 2. Get database credentials
    username = os.getenv('DB_USERNAME')
    password = os.getenv('DB_PASSWORD')
    host = os.getenv('DB_HOST')
    port = os.getenv('DB_PORT')
    database = os.getenv('DB_DATABASE')
    
    if not all([username, password, host, port, database]):
        raise ValueError("Error: Missing database credentials in .env")
        
    database_url = f'postgresql+psycopg://{username}:{password}@{host}:{port}/{database}'
    print(f"Connecting to database '{database}' on host '{host}:{port}'...")
    
    engine = create_engine(database_url)
    
    # 3. Read init_data.sql
    init_data_path = Path(__file__).parent / 'init_data.sql'
    if not init_data_path.exists():
        raise FileNotFoundError(f"Error: init_data.sql file not found at {init_data_path}")
        
    with open(init_data_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
        
    # Split sql statements (simple semicolon splitting, ignoring empty lines)
    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
    
    print(f"Found {len(statements)} SQL statements to execute.")
    
    # 4. Execute statements
    with engine.connect() as conn:
        for i, stmt in enumerate(statements, 1):
            try:
                with conn.begin():
                    conn.execute(text(stmt))
                if i % 200 == 0:
                    print(f"Executed {i}/{len(statements)} statements...")
            except IntegrityError as e:
                is_unique_violation = False
                orig_err = getattr(e, 'orig', None)
                if orig_err is not None:
                    pgcode = getattr(orig_err, 'pgcode', None)
                    sqlstate = getattr(orig_err, 'sqlstate', None)
                    if pgcode == '23505' or sqlstate == '23505' or 'unique' in str(orig_err).lower() or 'duplicate key' in str(orig_err).lower():
                        is_unique_violation = True
                
                if is_unique_violation:
                    print(f"Statement {i} skipped due to Unique index/constraint violation: {e.orig}")
                    continue
                else:
                    print(f"IntegrityError executing SQL statement {i}: {e}")
                    raise e
            except Exception as e:
                print(f"Error executing SQL statement {i}: {e}")
                raise e
    print("Data loaded successfully!")

if __name__ == '__main__':
    try:
        load_data()
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)
