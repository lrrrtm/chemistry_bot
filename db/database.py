from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from db.models import Base
from dotenv import load_dotenv
from os import getenv

load_dotenv()
DATABASE_URL = f"mysql+mysqlconnector://{getenv('DB_USER')}:{getenv('DB_PASSWORD')}@{getenv('DB_HOST')}:{getenv('DB_PORT')}/{getenv('DB_NAME')}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True
)
Session = scoped_session(sessionmaker(bind=engine))

Base.metadata.create_all(engine)
