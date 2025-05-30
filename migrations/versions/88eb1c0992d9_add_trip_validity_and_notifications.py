"""Add trip validity and notifications

Revision ID: 88eb1c0992d9
Revises: 6524f743495f
Create Date: 2025-05-01 09:06:27.157876

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '88eb1c0992d9'
down_revision = '6524f743495f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('trip', schema=None) as batch_op:
        batch_op.add_column(sa.Column('start_time', sa.Time(), nullable=False))
        batch_op.add_column(sa.Column('check_in_time', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('trip', schema=None) as batch_op:
        batch_op.drop_column('check_in_time')
        batch_op.drop_column('start_time')

    # ### end Alembic commands ###
