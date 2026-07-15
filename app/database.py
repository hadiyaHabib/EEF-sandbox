from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os

# Database file path configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, '../../eef_platform.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Submission Table Model with Evaluation Scores
class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, unique=True, index=True)
    github_url = Column(String)
    status = Column(String, default="Pending")
    downloaded_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    ai_feedback = Column(String, default="No feedback generated yet.")
    
    # Naye Enterprise Metrics Columns (Scores)
    code_quality_score = Column(Integer, default=0)
    architecture_score = Column(Integer, default=0)
    feature_score = Column(Integer, default=0)

def init_db():
    # Purani tables drop kar ke nayi tables banayega taake naye columns add ho sakein
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()