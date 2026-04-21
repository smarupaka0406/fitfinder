from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import Config

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)
Base = declarative_base()

def init_db():
    import models  # noqa: F401

    Base.metadata.create_all(engine)
    print("Database initialized")

def get_session():
    return Session()
