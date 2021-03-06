"""empty message

Revision ID: 322c84e86758
Revises: 
Create Date: 2018-05-20 20:18:44.632558

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '322c84e86758'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('identifier', sa.Integer(), nullable=False),
    sa.Column('token_hash', sa.String(length=128), nullable=True),
    sa.Column('readable_name', sa.String(length=32), nullable=True),
    sa.PrimaryKeyConstraint('identifier')
    )
    op.create_table('list_entry',
    sa.Column('identifier', sa.Integer(), nullable=False),
    sa.Column('content', sa.String(length=256), nullable=True),
    sa.Column('author', sa.Integer(), nullable=True),
    sa.Column('creation_time', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['author'], ['user.identifier'], ),
    sa.PrimaryKeyConstraint('identifier')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('list_entry')
    op.drop_table('user')
    # ### end Alembic commands ###
