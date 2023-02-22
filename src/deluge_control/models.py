import datetime as dt
import enum
import logging

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import DateTime, Enum, Integer, String
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

logger = logging.getLogger("deluge.models")


class StateChoices(enum.Enum):
    DL = "Downloading"
    DEL = "Deleted"
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

    retries = relationship(
        "TorrentRetry", back_populates="torrent", passive_deletes=True
    )
    snapshots = relationship(
        "TorrentSnapshot", back_populates="torrent", passive_deletes=True
    )

    def set_state(self, name):
        logger.debug(
            "setting state of %s from %s to %s",
            self.torrent_id,
            self.state,
            StateChoices(name),
        )
        self.state = StateChoices(name)


class TorrentRetry(Base):
    __tablename__ = "torrent_retries"
    id = Column(Integer, primary_key=True)
    torrent_id = Column(ForeignKey("torrents.id", ondelete="CASCADE"))
    count = Column(Integer, default=0)
    last_check = Column(DateTime, default=dt.datetime.utcnow)

    torrent = relationship("Torrent", back_populates="retries", single_parent=True)

class TorrentSnapshot(Base):
    __tablename__ = "torrent_snapshots"
    id = Column(Integer, primary_key=True)
    torrent_id = Column(ForeignKey("torrents.id", ondelete="CASCADE"))
    total_uploaded = Column(Integer)
    total_seeds = Column(Integer)
    total_peers = Column(Integer)
    time_recorded = Column(DateTime)

    torrent = relationship("Torrent", back_populates="snapshots", single_parent=True)
