import os
import faker
import random
import pytest
from unittest import mock

from sqlalchemy import create_engine
from deluge_control.client import DelugeClient
from deluge_control.models import Base
from deluge_control.session import get_session, get_engine

fake = faker.Faker()

video_qualities = ["480p", "720p", "1080p", "2160p"]


def get_test_engine(echo=True):
    return get_engine(echo=echo, pg_name=f"test-{os.environ.get('PG_NAME')}")


@pytest.fixture(scope="module")
def session():
    return get_session(get_test_engine())


@pytest.fixture
def setup_database():
    Base.metadata.bind = get_test_engine()
    Base.metadata.create_all()
    yield

    Base.metadata.drop_all()


@pytest.fixture
def db_session(setup_database, session):
    yield (test_session := session())
    test_session.rollback()
    test_session.close()


@pytest.fixture
def db_5_sessions(setup_database, session):
    yield (test_sessions := [session() for _ in range(10)])
    for test_session in test_sessions:
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


@pytest.fixture(scope="session")
def mock_xseed_request():
    with mock.patch("deluge_control.xseed.XSeedClient.cross_seed") as mock_request:
        yield mock_request
