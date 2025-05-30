"""Add payment system with nullable amount

Revision ID: 6524f743495f
Revises: ee9ef1907d8e
Create Date: 2025-05-01 08:59:23.828354

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6524f743495f'
down_revision = 'ee9ef1907d8e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('trip', schema=None) as batch_op:
        batch_op.add_column(sa.Column('amount', sa.Float(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('trip', schema=None) as batch_op:
        batch_op.drop_column('amount')

    # ### end Alembic commands ###
