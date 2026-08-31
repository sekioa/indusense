from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Créer une fabrique de sessions courtes et explicites."""

    return sessionmaker(
        bind=engine,
        class_=Session,
        expire_on_commit=False,
    )
