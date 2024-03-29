import datetime as dt
import random
from typing import List
from unittest import mock
from sqlalchemy.sql.expression import select
from deluge_control.models import StateChoices, Torrent, TorrentRetry
from deluge_control.check_torrents import (
    check_torrents,
    check_downloading_torrents,
    check_seeding_torrents,
    split_ready_db_torrents_by_state,
    update_torrent_states,
)
from deluge_control.register_torrents import register_new_torrents
from utils import (
    get_torrents_with,
    patch_call,
    patch_torrents_status,
    encode_torrent_data,
)


def get_downloading_torrents_info(
    torrent_ids, total_seeds: List[int] = None, progress: List[int] = None
):
    return encode_torrent_data(
        {
            torrent_id: {
                "state": "Downloading",
                "total_seeds": random.choice(total_seeds)
                if total_seeds
                else random.randint(0, 600),
                "progress": random.choice(progress)
                if progress
                else random.randint(0, 100),
            }
            for torrent_id in torrent_ids
        }
    )


def get_seeding_torrents_info(torrent_ids):
    return encode_torrent_data(
        {
            torrent_id: {
                "total_uploaded": random.randint(1 * 1024**2, 1 * 1024**3),
                "total_seeds": random.randint(0, 500),
                "total_peers": random.randint(0, 500),
                "state": "Seeding",
            }
            for torrent_id in torrent_ids
        }
    )


def test_split_torrents_only_covers_ready_torrents(movie_names, db_5_sessions):
    iter_sessions = iter(db_5_sessions)
    with next(iter_sessions) as db_session:
        normal_torrent = Torrent(
            torrent_id=(normal_torrent_id := "abcd1234"),
            name=movie_names[0],
            time_added=(now := dt.datetime.utcnow()),
            state=StateChoices.SEED,
        )
        db_session.add(normal_torrent)
        delayed_torrent = Torrent(
            torrent_id=(delayed_torrent_id := "abcd4321"),
            name=movie_names[2],
            time_added=now,
            next_check_time=now + dt.timedelta(days=1),
            state=StateChoices.SEED,
        )
        db_session.add(delayed_torrent)
        db_session.commit()

    with next(iter_sessions) as db_session:
        ready_db_torrents = split_ready_db_torrents_by_state(db_session)[
            StateChoices.SEED
        ]
        assert delayed_torrent_id not in ready_db_torrents
        assert normal_torrent_id in ready_db_torrents


def test_split_torrents_by_state(deluge_client, movie_names, db_5_sessions):
    iter_sessions = iter(db_5_sessions)
    with patch_torrents_status() as mock_torrents:
        mock_torrents.return_value = {
            **get_torrents_with(2, movie_names[0:2], ("Downloading",)),
            **get_torrents_with(2, movie_names[2:], ("Seeding",)),
        }
        register_new_torrents(deluge_client, next(iter_sessions))
        torrents = next(iter_sessions).execute(select(Torrent)).scalars().all()
        torrents_by_state = split_ready_db_torrents_by_state(next(iter_sessions))

        for torrent in torrents:
            assert isinstance(
                torrents_by_state[torrent.state][torrent.torrent_id], Torrent
            )


def test_generate_retry(deluge_client, movie_names, db_5_sessions):
    """
    Confirm Retry obj created for a downloading obj at 0 progress
    """
    iter_sessions = iter(db_5_sessions)
    with patch_torrents_status() as mock_torrents:
        mock_torrents.return_value = get_torrents_with(
            1, movie_names[1], ("Downloading",)
        )
        register_new_torrents(deluge_client, next(iter_sessions))
        with next(iter_sessions) as db_session:
            db_downloading_torrents = split_ready_db_torrents_by_state(db_session)[
                StateChoices.DL
            ]
            torrent = list(db_downloading_torrents.values())[0]

        mock_torrents.return_value = get_downloading_torrents_info(
            (torrent.torrent_id,), total_seeds=range(1, 50), progress=[0]
        )
        client_torrents = deluge_client.decode_torrent_data(
            deluge_client.get_torrents_status(
                status_keys=["state", "progress", "total_seeds"]
            )
        )
        with next(iter_sessions) as db_session:
            check_downloading_torrents(
                deluge_client,
                db_session,
                db_downloading_torrents,
                client_torrents,
            )
            db_session.commit()

        with next(iter_sessions) as db_session:
            db_session.add(torrent)
            retry = (
                db_session.execute(
                    select(TorrentRetry).where(TorrentRetry.torrent_id == torrent.id)
                )
                .scalars()
                .first()
            )
            assert (
                (now := dt.datetime.utcnow())
                < retry.torrent.next_check_time
                <= now + dt.timedelta(minutes=1)
            )


def test_preexisting_retry_given_higher_count_and_wait(
    deluge_client, db_5_sessions, movie_names
):
    """
    A torrent which already has a retry should have its retry count iterated,
    and receive a larger delay before next check.
    """
    iter_sessions = iter(db_5_sessions)
    with patch_torrents_status() as mock_torrents:
        with next(iter_sessions) as db_session:
            db_session.add(
                torrent := Torrent(
                    torrent_id="abc1234",
                    name=movie_names[1],
                    state=StateChoices.DL,
                    time_added=dt.datetime.utcnow(),
                )
            )
            db_session.commit()
            mock_torrents.return_value = get_downloading_torrents_info(
                (torrent.torrent_id,), total_seeds=range(1, 50), progress=[0]
            )
            db_downloading_torrents = split_ready_db_torrents_by_state(db_session)[
                StateChoices.DL
            ]
            client_torrents = deluge_client.decode_torrent_data(
                deluge_client.get_torrents_status(
                    status_keys=["state", "progress", "total_seeds"]
                )
            )
            check_downloading_torrents(
                deluge_client,
                db_session,
                db_downloading_torrents,
                client_torrents,
            )
            torrent.next_check_time = dt.datetime.utcnow()
            db_session.commit()

        with mock.patch("deluge_control.client.DelugeClient.force_reannounce"):
            with next(iter_sessions) as db_session:
                db_session.add(torrent)

                check_downloading_torrents(
                    deluge_client,
                    db_session,
                    db_downloading_torrents,
                    client_torrents,
                )
                assert torrent.retries[0].count == 1
                assert (
                    (now := dt.datetime.utcnow()) + dt.timedelta(seconds=30)
                    < torrent.next_check_time
                    <= now + dt.timedelta(minutes=3)
                )
                torrent.next_check_time = dt.datetime.utcnow()

            with next(iter_sessions) as db_session:
                db_session.add(torrent)
                check_downloading_torrents(
                    deluge_client,
                    db_session,
                    db_downloading_torrents,
                    client_torrents,
                )
                assert torrent.retries[0].count == 2
                assert (
                    now + dt.timedelta(minutes=5)
                    < torrent.next_check_time
                    <= now + dt.timedelta(minutes=11)
                )


def test_no_reannounce_on_retry_creation(deluge_client, movie_names, db_5_sessions):
    iter_sessions = iter(db_5_sessions)
    with patch_torrents_status() as mock_torrents:
        with next(iter_sessions) as db_session:
            db_session.add(
                torrent := Torrent(
                    torrent_id="abc1234",
                    name=movie_names[1],
                    state=StateChoices.DL,
                    time_added=dt.datetime.utcnow(),
                )
            )
            db_session.commit()
            mock_torrents.return_value = get_downloading_torrents_info(
                (torrent.torrent_id,), total_seeds=range(1, 50), progress=[0]
            )
            db_downloading_torrents = split_ready_db_torrents_by_state(db_session)[
                StateChoices.DL
            ]
            client_torrents = deluge_client.decode_torrent_data(
                deluge_client.get_torrents_status(
                    status_keys=["state", "progress", "total_seeds"]
                )
            )
            with patch_call() as mock_call:
                check_downloading_torrents(
                    deluge_client,
                    db_session,
                    db_downloading_torrents,
                    client_torrents,
                )
                mock_call.assert_not_called()


def test_reannounces(deluge_client, db_5_sessions, movie_names):
    """
    We should force reannounce for every torrent ready for check and with a retry count
    """
    iter_sessions = iter(db_5_sessions)
    with patch_torrents_status() as mock_torrents:
        torrents = []
        iter_move_names = iter(movie_names)
        with next(iter_sessions) as db_session:
            for i in range(10):
                torrents.append(
                    torrent := Torrent(
                        torrent_id=f"torrent_{i}",
                        name=next(iter_move_names),
                        state=StateChoices.DL,
                        time_added=dt.datetime.utcnow(),
                    )
                )
                torrent.retries.append(TorrentRetry(torrent_id=torrent.id, count=3))
        for torrent in torrents:
            db_session.add(torrent)
        db_session.commit()
        mock_torrents.return_value = get_downloading_torrents_info(
            (torrent.torrent_id for torrent in torrents),
            total_seeds=range(1, 50),
            progress=[0],
        )
        db_downloading_torrents = split_ready_db_torrents_by_state(db_session)[
            StateChoices.DL
        ]
        client_torrents = deluge_client.decode_torrent_data(
            deluge_client.get_torrents_status(
                status_keys=["state", "progress", "total_seeds"]
            )
        )
        with mock.patch(
            "deluge_control.client.DelugeClient.force_reannounce"
        ) as mock_reannounce:
            check_downloading_torrents(
                deluge_client,
                db_session,
                db_downloading_torrents,
                client_torrents,
            )
        mock_reannounce.assert_called_once_with(
            [torrent.torrent_id for torrent in torrents]
        )


def test_update_dl_torrent_to_deleted(deluge_client, db_5_sessions, movie_names):
    iter_sessions = iter(db_5_sessions)
    with patch_torrents_status() as mock_torrents:
        with next(iter_sessions) as db_session:
            db_session.add(
                torrent := Torrent(
                    torrent_id=f"abcd1234",
                    name=movie_names[0],
                    state=StateChoices.DL,
                    time_added=dt.datetime.utcnow(),
                )
            )
            db_session.commit()
            mock_torrents.return_value = {}

        with next(iter_sessions) as db_session:
            db_session.add(torrent)
            db_torrents = split_ready_db_torrents_by_state(db_session)
            client_torrents = deluge_client.decode_torrent_data(
                deluge_client.get_torrents_status(
                    status_keys=["state", "progress", "total_seeds"]
                )
            )
            update_torrent_states(db_session, db_torrents, client_torrents)
            db_session.commit()

        assert (
            next(iter_sessions)
            .execute(select(Torrent.state).where(Torrent.torrent_id == "abcd1234"))
            .scalars()
            .first()
            == StateChoices.DEL
        )


def test_update_dl_torrent_to_seed(deluge_client, db_5_sessions, movie_names):
    iter_sessions = iter(db_5_sessions)
    with patch_torrents_status() as mock_torrents:
        with next(iter_sessions) as db_session:
            db_session.add(
                torrent := Torrent(
                    torrent_id=f"abcd1234",
                    name=movie_names[0],
                    state=StateChoices.DL,
                    time_added=dt.datetime.utcnow(),
                )
            )
            db_session.commit()

            mock_torrents.return_value = get_seeding_torrents_info(
                (torrent.torrent_id,)
            )

        with next(iter_sessions) as db_session:
            db_session.add(torrent)
            db_torrents = split_ready_db_torrents_by_state(db_session)
            client_torrents = deluge_client.decode_torrent_data(
                deluge_client.get_torrents_status(
                    status_keys=["state", "progress", "total_seeds"]
                )
            )
            update_torrent_states(db_session, db_torrents, client_torrents)
            db_session.commit()

        assert (
            next(iter_sessions)
            .execute(select(Torrent.state).where(Torrent.torrent_id == "abcd1234"))
            .scalars()
            .first()
            == StateChoices.SEED
        )


def test_check_seeding_torrent(deluge_client, movie_names, db_5_sessions):
    """
    Confirm torrent snapshot generated for ready and seeding torrent
    """
    with patch_torrents_status() as mock_torrents:
        iter_sessions = iter(db_5_sessions)
        mock_torrents.return_value = get_torrents_with(1, movie_names[1], ("Seeding",))
        register_new_torrents(deluge_client, next(iter_sessions))

        with next(iter_sessions) as db_session:
            torrent = db_session.execute(select(Torrent)).scalars().all()[0]
            assert not torrent.snapshots

            mock_torrents.return_value = get_seeding_torrents_info(
                (torrent.torrent_id,)
            )
            db_seeding_torrents = split_ready_db_torrents_by_state(db_session)[
                StateChoices.SEED
            ]
            client_torrents = deluge_client.decode_torrent_data(
                deluge_client.get_torrents_status(
                    ["total_uploaded", "total_seeds", "total_peers", "state"]
                )
            )
            check_seeding_torrents(db_session, db_seeding_torrents, client_torrents)
            db_session.commit()

        with next(iter_sessions) as db_session:
            db_session.add(torrent)
            assert torrent.snapshots[0]


def test_change_seeding_to_paused(deluge_client, movie_names, db_5_sessions):
    with patch_torrents_status() as mock_torrents:
        iter_sessions = iter(db_5_sessions)
        mock_torrents.return_value = get_torrents_with(1, movie_names[:1], ("Seeding",))
        register_new_torrents(deluge_client, next(iter_sessions))
        with next(iter_sessions) as db_session:
            torrent_name, torrent_state = db_session.execute(
                select(Torrent.name, Torrent.state)
            ).all()[0]
            assert torrent_name and torrent_state == StateChoices.SEED
            db_torrents = split_ready_db_torrents_by_state(db_session)
            mock_torrents.return_value = encode_torrent_data(
                {
                    db_torrent_id: {"state": "Paused"}
                    for db_torrent_id in db_torrents[StateChoices.SEED]
                }
            )

            client_torrents = deluge_client.decode_torrent_data(
                deluge_client.get_torrents_status(
                    ["total_uploaded", "total_seeds", "total_peers", "state"]
                )
            )
            update_torrent_states(db_session, db_torrents, client_torrents)
            db_session.commit()

        with next(iter_sessions) as db_session:
            torrent = db_session.execute(select(Torrent)).scalars().first()
            assert torrent.state == StateChoices.PAUSE and torrent.name == torrent_name


@mock.patch("deluge_control.check_torrents.check_seeding_torrents")
@mock.patch("deluge_control.check_torrents.check_downloading_torrents")
@mock.patch("deluge_control.check_torrents.update_torrent_states")
@mock.patch("deluge_control.client.DelugeClient.get_torrents_status")
def test_check_torrents(
    mock_get_status,
    mock_update_state,
    mock_check_downloading_torrents,
    mock_check_seeding_torrents,
    deluge_client,
    db_session,
):
    """
    Assert expected calls are made in this conglomerate function
    """
    check_torrents(deluge_client, db_session)
    mock_get_status.assert_called_once()
    mock_update_state.assert_called_once()
    mock_check_downloading_torrents.assert_called_once()
    mock_check_seeding_torrents.assert_called_once()
