"""add deleted to accepted states

Revision ID: 1354b7b51eb2
Revises: e3ee18d1d8d1
Create Date: 2022-12-27 20:50:55.323873-05:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1354b7b51eb2"
down_revision = "e3ee18d1d8d1"
branch_labels = None
depends_on = "e3ee18d1d8d1"

old_values = ("PAUSE", "DL", "SEED", "PEND", "CHECK", "E", "Q", "ALLOC", "MOV")
new_values = ("DEL", *old_values)
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
    op.execute("DROP TYPE IF EXISTS statechoices")
    op.execute(f"CREATE TYPE statechoices AS ENUM {new_values}")
    op.alter_column(
        "torrents",
        "state",
        type_=new_type,
        existing_type=new_tmp_type,
        postgresql_using="state::text::statechoices",
    )
    op.execute("DROP TYPE tmpstatechoices")


def downgrade() -> None:
    op.execute("DELETE FROM torrents WHERE state='DEL'")
    op.execute(f"CREATE TYPE tmpstatechoices AS ENUM {old_values}")
    op.alter_column(
        "torrents",
        "state",
        type_=old_tmp_type,
        existing_type=new_type,
        postgresql_using="state::text::tmpstatechoices",
    )
    op.execute("DROP TYPE IF EXISTS statechoices")
    op.execute(f"CREATE TYPE statechoices AS ENUM {old_values}")
    op.alter_column(
        "torrents",
        "state",
        type_=old_type,
        existing_type=old_tmp_type,
        postgresql_using="state::text::statechoices",
    )
    op.execute("DROP TYPE tmpstatechoices")
