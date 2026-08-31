
from alembic import op
import sqlalchemy as sa

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'data_aggregations',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('sensor_type', sa.String(50), nullable=False),
        sa.Column('device_id', sa.String(100), nullable=True),
        sa.Column('time_bucket', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('period', sa.String(20), nullable=False),
        sa.Column('avg_value', sa.Numeric(15, 6), nullable=True),
        sa.Column('max_value', sa.Numeric(15, 6), nullable=True),
        sa.Column('min_value', sa.Numeric(15, 6), nullable=True),
        sa.Column('count', sa.Integer(), nullable=True),
        sa.Column('sum_value', sa.Numeric(15, 6), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_aggregations_type_bucket', 'data_aggregations', ['sensor_type', sa.text('time_bucket DESC')])
    op.create_index('idx_aggregations_period', 'data_aggregations', ['period'])
    op.create_index('idx_aggregations_device', 'data_aggregations', ['device_id'])

def downgrade() -> None:
    op.drop_table('data_aggregations')