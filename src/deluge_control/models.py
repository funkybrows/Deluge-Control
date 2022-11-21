import enum

from sqlalchemy import Column
from sqlalchemy.types import DateTime, Enum, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class StateChoices(enum.Enum):
    DL = "Downloading"
    SEED = "Seeding"
    PEND = "Pending"
    CHECK = "Checking"
    E = "Error"
    Q = "Queued"
    ALLOC = "Allocating"
    MOV = "Moving"


class Torrent(Base):
    __tablename__ = "torrents"
    id = Column(Integer, primary_key=True)
    torrent_id = Column(String(100), nullable=False, unique=True)
    name = Column(String(256), nullable=False)
    state = Column(Enum(StateChoices))
