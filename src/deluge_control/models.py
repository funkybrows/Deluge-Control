import datetime as dt
import enum

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import DateTime, Enum, Integer, String
from sqlalchemy.orm import declarative_base, relationship

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
    PAUSE = "Paused"


class Torrent(Base):
    __tablename__ = "torrents"
    id = Column(Integer, primary_key=True)
    torrent_id = Column(String(100), nullable=False, unique=True)
    name = Column(String(256), nullable=False)
    state = Column(Enum(StateChoices))
    time_added = Column(DateTime)
    next_check_time = Column(DateTime, default=dt.datetime.utcnow)

    snapshots = relationship(
        "TorrentSnapshot", back_populates="torrent", passive_deletes=True
    )


class TorrentSnapshot(Base):
    __tablename__ = "torrent_snapshots"
    id = Column(Integer, primary_key=True)
    torrent_id = Column(ForeignKey("torrents.id", ondelete="CASCADE"))
    total_uploaded = Column(Integer)
    total_seeds = Column(Integer)
    total_peers = Column(Integer)
    time_recorded = Column(DateTime)

    torrent = relationship("Torrent", back_populates="snapshots", single_parent=True)
