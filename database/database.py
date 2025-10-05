from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from .models import Base
from config import Config

engine = create_engine(Config.DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    _add_is_active_column_if_missing()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _add_is_active_column_if_missing():
    inspector = inspect(engine)
    columns = inspector.get_columns('groups')
    col_names = [col['name'] for col in columns]

    if 'is_active' not in col_names:
        with engine.connect() as conn:
            conn.execute(text('ALTER TABLE groups ADD COLUMN is_active BOOLEAN DEFAULT 1'))
        print("✅ Coluna 'is_active' adicionada na tabela 'groups'.")
    else:
        print("ℹ️ Coluna 'is_active' já existe na tabela 'groups'.")