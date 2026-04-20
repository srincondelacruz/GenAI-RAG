"""
database.py — Conexión a la base de datos SQLite con SQLAlchemy.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./genai_rag.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # necesario para SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency que provee una sesión de DB por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
