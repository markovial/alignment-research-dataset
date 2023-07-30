"""Added Pinecone model

Revision ID: ef06ffe4a632
Revises: 0a0041c28458
Create Date: 2023-07-30 14:57:41.218621

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ef06ffe4a632'
down_revision = '0a0041c28458'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('pinecone',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('article_id', sa.Integer(), nullable=False),
    sa.Column('update_required', sa.Boolean(), nullable=False),
    sa.Column('delete_required', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('pinecone')
    # ### end Alembic commands ###
