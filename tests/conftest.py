import os
import faker
import random
import pytest

from sqlalchemy import create_engine
from deluge_control.client import DelugeClient
from deluge_control.models import Base
from deluge_control.session import get_session

fake = faker.Faker()

video_qualities = ["480p", "720p", "1080p", "2160p"]


def get_engine(echo=True):
    return create_engine(
        f"postgresql+{os.environ.get('PG_TEST_DRIVER')}://{os.environ.get('PG_TEST_USER')}"
        f":{os.environ.get('PG_TEST_PASSWORD')}@{os.environ.get('PG_TEST_HOST')}:{os.environ.get('PG_TEST_PORT')}/{os.environ.get('PG_TEST_NAME')}",
        echo=echo,
        future=True,
    )


@pytest.fixture(scope="module")
def session():
    return get_session(get_engine())


@pytest.fixture
def setup_database():
    Base.metadata.bind = get_engine()
    Base.metadata.create_all()
    yield

    Base.metadata.drop_all()


@pytest.fixture
def db_session(setup_database, session):
    yield (test_session := session())
    test_session.rollback()
    test_session.close()


@pytest.fixture(scope="session")
def deluge_client():
    return DelugeClient()


@pytest.fixture(scope="module")
def movie_names():
    ret = []
    format_choices = ["BluRay", "DVD"]

    for _ in range(10):
        ret.append(
            ".".join((fake.word() for _ in range(4)))
            + "."
            + ".".join(
                (
                    fake.date("%Y"),
                    random.choice(video_qualities),
                    random.choice(format_choices),
                )
            )
            + "."
            + ".".join((fake.word().upper() for _ in range(3)))
        )
    return ret
