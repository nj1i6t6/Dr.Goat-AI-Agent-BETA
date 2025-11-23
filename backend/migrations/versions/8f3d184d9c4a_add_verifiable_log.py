"""add verifiable log table"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '8f3d184d9c4a'
down_revision = 'c4cffb3b2498'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'verifiable_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(length=80), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('event_data', sa.JSON(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('previous_hash', sa.String(length=64), nullable=True),
        sa.Column('current_hash', sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_verifiable_log_entity', 'verifiable_log', ['entity_type', 'entity_id', 'id'], unique=False)
    op.create_index('ix_verifiable_log_current_hash', 'verifiable_log', ['current_hash'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_verifiable_log_current_hash', table_name='verifiable_log')
    op.drop_index('ix_verifiable_log_entity', table_name='verifiable_log')
    op.drop_table('verifiable_log')
