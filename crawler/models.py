from sqlalchemy import create_engine, Column, Integer, String, DateTime,TEXT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Erstellen einer Engine und Verbindung zur Datenbank
#engine = create_engine('sqlite:///mitteilungen.db')
engine = create_engine('sqlite:///green-ai-projekte.db')

# Erstellen einer Basisklasse für SQLAlchemy-Modelle
Base = declarative_base()


class Mitteilung(Base):
    __tablename__ = 'mitteilungen'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False,unique=True)
    content = Column(TEXT, nullable=False)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)

class Projekt(Base):
    __tablename__ = 'projekte'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False,unique=True)
    content = Column(TEXT, nullable=False)

# Erstellen der Datenbanktabellen, falls sie nicht vorhanden sind
Base.metadata.create_all(engine)

# Erstellen einer Sitzung, um mit der Datenbank zu interagieren
Session = sessionmaker(bind=engine)
session = Session()