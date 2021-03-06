"""empty message

Revision ID: e5bdb234a558
Revises: 67c8f69d0aad
Create Date: 2021-02-17 00:25:59.719714

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e5bdb234a558'
down_revision = '67c8f69d0aad'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('goals',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('goal', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('goals_tutors',
    sa.Column('tutor_id', sa.Integer(), nullable=True),
    sa.Column('goal_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], ),
    sa.ForeignKeyConstraint(['tutor_id'], ['tutors.id'], )
    )
    op.drop_column('tutors', 'goals')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tutors', sa.Column('goals', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.drop_table('goals_tutors')
    op.drop_table('goals')
    # ### end Alembic commands ###
