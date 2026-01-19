import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Utiliser SQLite pour le développement local, PostgreSQL pour Docker
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./pacs_local.db"  # Base de données locale SQLite
)

# Configuration adaptée selon le type de base de données
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False}  # Nécessaire pour SQLite
    )
else:
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_size=20,
        max_overflow=40,
        pool_pre_ping=True
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
