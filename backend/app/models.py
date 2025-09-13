# This file helps us remember things in a database
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# Think of this as the blueprint for our filing cabinet
Base = declarative_base()

# This is like a drawer in our filing cabinet for storing BLAST results
class BlastCache(Base):
    __tablename__ = 'blast_cache'
    
    id = Column(Integer, primary_key=True)  # Like a ticket number
    sequence = Column(String, unique=True, index=True)  # The DNA sequence
    lineage = Column(String)  # What creature it is (like "fish > goldfish")
    confidence = Column(Float)  # How sure we are (0-100%)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)

# This creates our database connection (like opening the filing cabinet)
def get_database():
    engine = create_engine('sqlite:///database/blast_cache.db', echo=False)
    Base.metadata.create_all(engine)  # Creates the drawers if they don't exist
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal(), engine
