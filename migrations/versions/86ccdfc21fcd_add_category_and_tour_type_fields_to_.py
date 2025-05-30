"""Add category and tour_type fields to Trip model

Revision ID: 86ccdfc21fcd
Revises: 0d2b276fd120
Create Date: 2025-05-01 15:52:42.824179

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '86ccdfc21fcd'
down_revision = '0d2b276fd120'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('trip', schema=None) as batch_op:
        batch_op.add_column(sa.Column('category', sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column('tour_type', sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column('long_tour_details', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('short_tour_details', sa.Text(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('trip', schema=None) as batch_op:
        batch_op.drop_column('short_tour_details')
        batch_op.drop_column('long_tour_details')
        batch_op.drop_column('tour_type')
        batch_op.drop_column('category')

    # ### end Alembic commands ###
