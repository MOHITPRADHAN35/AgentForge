from sqlmodel import create_engine, SQLModel, Session
from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)


def init_db():
    from app.database import models  # noqa: F401
    SQLModel.metadata.create_all(engine)


# Auto-initialize SQLite tables on import
init_db()


def get_session():
    with Session(engine) as session:
        yield session
