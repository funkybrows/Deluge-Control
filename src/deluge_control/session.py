import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def get_engine(echo=False, pg_name=os.environ.get("PG_NAME")):
    return create_engine(
        f"postgresql+{os.environ.get('PG_DRIVER')}://{os.environ.get('PG_USER')}"
        f":{os.environ.get('PG_PASSWORD')}@{os.environ.get('PG_HOST')}:{os.environ.get('PG_PORT', 5432)}/{pg_name}",
        echo=echo,
        future=True,
    )


def get_session(engine=None):
    return sessionmaker(engine or get_engine())
