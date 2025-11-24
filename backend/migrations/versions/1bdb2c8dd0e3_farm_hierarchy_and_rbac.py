"""Farm hierarchy and RBAC tables"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1bdb2c8dd0e3'
down_revision = '8f3d184d9c4a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'farm',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('code', sa.String(length=12), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_farm_code'), 'farm', ['code'], unique=True)

    op.create_table(
        'area',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('farm_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['farm_id'], ['farm.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'shed',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('area_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['area_id'], ['area.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'pen',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('shed_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['shed_id'], ['shed.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'user_farm_role',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('farm_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['farm_id'], ['farm.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'farm_id', name='_user_farm_uc')
    )
    op.create_index(op.f('ix_user_farm_role_status'), 'user_farm_role', ['status'], unique=False)

    op.add_column('sheep', sa.Column('pen_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'sheep', 'pen', ['pen_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint(None, 'sheep', type_='foreignkey')
    op.drop_column('sheep', 'pen_id')
    op.drop_index(op.f('ix_user_farm_role_status'), table_name='user_farm_role')
    op.drop_table('user_farm_role')
    op.drop_table('pen')
    op.drop_table('shed')
    op.drop_table('area')
    op.drop_index(op.f('ix_farm_code'), table_name='farm')
    op.drop_table('farm')

