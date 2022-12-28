"""Add PAUSE to accepted states

Revision ID: e3ee18d1d8d1
Revises: 475a0bc646c1
Create Date: 2022-11-21 19:31:27.180250-05:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e3ee18d1d8d1"
down_revision = "475a0bc646c1"
branch_labels = None
depends_on = None

old_values = ("DL", "SEED", "PEND", "CHECK", "E", "Q", "ALLOC", "MOV")
new_values = ("PAUSE", *old_values)
old_type = sa.Enum(*old_values, name="statechoices")
new_type = sa.Enum(*new_values, name="statechoices")
new_tmp_type = sa.Enum(*new_values, name="tmpstatechoices")
old_tmp_type = sa.Enum(*old_values, name="tmpstatechoices")


def upgrade() -> None:
    op.execute(f"CREATE TYPE tmpstatechoices AS ENUM {new_values}")
    op.alter_column(
        "torrents",
        "state",
        type_=new_tmp_type,
        existing_type=old_type,
        postgresql_using="state::text::tmpstatechoices",
    )
    op.execute(f"DROP TYPE IF EXISTS statechoices")
    op.execute(f"CREATE TYPE statechoices AS ENUM {new_values}")
    op.alter_column(
        "torrents",
        "state",
        type_=new_type,
        existing_type=new_tmp_type,
        postgresql_using="state::text::statechoices",
    )
    op.execute(f"DROP TYPE tmpstatechoices")


def downgrade() -> None:
    op.execute("DELETE FROM torrents WHERE state='PAUSE'")
    op.execute(f"CREATE TYPE tmpstatechoices AS ENUM {old_values}")
    op.alter_column(
        "torrents",
        "state",
        type_=old_tmp_type,
        existing_type=new_type,
        postgresql_using="state::text::tmpstatechoices",
    )
    op.execute(f"DROP TYPE IF EXISTS statechoices")
    op.execute(f"CREATE TYPE statechoices AS ENUM {old_values}")
    op.alter_column(
        "torrents",
        "state",
        type_=old_type,
        existing_type=old_tmp_type,
        postgresql_using="state::text::statechoices",
    )
    op.execute(f"DROP TYPE tmpstatechoices")
