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
temp_type = sa.Enum("TEMPVAL", name="tempstatechoices")


def upgrade() -> None:
    op.execute("CREATE TYPE tempstatechoices AS ENUM ('TEMPVAL') ")
    op.alter_column(
        "torrents",
        "state",
        type_=temp_type,
        existing_type=old_type,
        postgresql_using="state::text::tempstatechoices",
    )
    op.execute("DROP TYPE statechoices")
    op.execute(
        "CREATE TYPE statechoices AS ENUM ('DL', 'SEED', 'PEND', 'CHECK', 'E', 'Q', 'ALLOC', 'MOV', 'PAUSE') "
    )
    op.alter_column(
        "torrents",
        "state",
        type_=new_type,
        existing_type=temp_type,
        postgresql_using="state::text::statechoices",
    )
    op.execute("DROP TYPE tempstatechoices")


def downgrade() -> None:
    op.execute("CREATE TYPE tempstatechoices AS ENUM ('TEMPVAL') ")
    op.alter_column(
        "torrents",
        "state",
        type_=temp_type,
        existing_type=new_type,
        postgresql_using="state::text::tempstatechoices",
    )
    op.execute("DROP TYPE statechoices")
    op.execute(
        "CREATE TYPE statechoices AS ENUM ('DL', 'SEED', 'PEND', 'CHECK', 'E', 'Q', 'ALLOC', 'MOV') "
    )
    op.alter_column(
        "torrents",
        "state",
        type_=old_type,
        existing_type=temp_type,
        postgresql_using="state::text::statechoices",
    )
    op.execute("DROP TYPE tempstatechoices")
