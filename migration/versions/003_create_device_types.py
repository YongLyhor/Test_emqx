
from alembic import op
import sqlalchemy as sa

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'device_types',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('type_code', sa.String(50), nullable=False),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('default_unit', sa.String(20), nullable=False),
        sa.Column('min_value', sa.Numeric(15, 6), nullable=True),
        sa.Column('max_value', sa.Numeric(15, 6), nullable=True),
        sa.Column('alert_threshold', sa.Numeric(15, 6), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('type_code')
    )

def downgrade() -> None:
    op.drop_table('device_types')