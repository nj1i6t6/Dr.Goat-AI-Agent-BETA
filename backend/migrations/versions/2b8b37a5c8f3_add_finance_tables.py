"""add cost and revenue tables"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2b8b37a5c8f3'
down_revision = '8f3d184d9c4a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'cost_entry',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sheep_id', sa.Integer(), sa.ForeignKey('sheep.id', ondelete='SET NULL'), nullable=True),
        sa.Column('recorded_at', sa.DateTime(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('subcategory', sa.String(length=100), nullable=True),
        sa.Column('label', sa.String(length=150), nullable=True),
        sa.Column('amount', sa.Numeric(14, 2), nullable=False),
        sa.Column('currency', sa.String(length=8), nullable=True, server_default='TWD'),
        sa.Column('breed', sa.String(length=100), nullable=True),
        sa.Column('age_months', sa.Integer(), nullable=True),
        sa.Column('lactation_number', sa.Integer(), nullable=True),
        sa.Column('production_stage', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_cost_entry_user_recorded', 'cost_entry', ['user_id', 'recorded_at'], unique=False)
    op.create_index('ix_cost_entry_user_category', 'cost_entry', ['user_id', 'category'], unique=False)
    op.create_index('ix_cost_entry_user_breed', 'cost_entry', ['user_id', 'breed'], unique=False)

    op.create_table(
        'revenue_entry',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sheep_id', sa.Integer(), sa.ForeignKey('sheep.id', ondelete='SET NULL'), nullable=True),
        sa.Column('recorded_at', sa.DateTime(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('subcategory', sa.String(length=100), nullable=True),
        sa.Column('label', sa.String(length=150), nullable=True),
        sa.Column('amount', sa.Numeric(14, 2), nullable=False),
        sa.Column('currency', sa.String(length=8), nullable=True, server_default='TWD'),
        sa.Column('breed', sa.String(length=100), nullable=True),
        sa.Column('age_months', sa.Integer(), nullable=True),
        sa.Column('lactation_number', sa.Integer(), nullable=True),
        sa.Column('production_stage', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_revenue_entry_user_recorded', 'revenue_entry', ['user_id', 'recorded_at'], unique=False)
    op.create_index('ix_revenue_entry_user_category', 'revenue_entry', ['user_id', 'category'], unique=False)
    op.create_index('ix_revenue_entry_user_breed', 'revenue_entry', ['user_id', 'breed'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_revenue_entry_user_breed', table_name='revenue_entry')
    op.drop_index('ix_revenue_entry_user_category', table_name='revenue_entry')
    op.drop_index('ix_revenue_entry_user_recorded', table_name='revenue_entry')
    op.drop_table('revenue_entry')

    op.drop_index('ix_cost_entry_user_breed', table_name='cost_entry')
    op.drop_index('ix_cost_entry_user_category', table_name='cost_entry')
    op.drop_index('ix_cost_entry_user_recorded', table_name='cost_entry')
    op.drop_table('cost_entry')
