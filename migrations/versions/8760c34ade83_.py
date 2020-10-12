"""empty message

Revision ID: 8760c34ade83
Revises: 216accd1ab9d
Create Date: 2020-10-12 08:35:33.141882

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8760c34ade83'
down_revision = '216accd1ab9d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('venues', sa.Column('test', sa.ARRAY(sa.String()), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('venues', 'test')
    # ### end Alembic commands ###