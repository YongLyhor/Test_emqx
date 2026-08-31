
from alembic import op
import sqlalchemy as sa

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'alerts',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('device_id', sa.String(100), nullable=False),
        sa.Column('sensor_type', sa.String(50), nullable=False),
        sa.Column('alert_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('value', sa.Numeric(15, 6), nullable=True),
        sa.Column('threshold_value', sa.Numeric(15, 6), nullable=True),
        sa.Column('resolved', sa.Boolean(), server_default='false'),
        sa.Column('resolved_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_alerts_device', 'alerts', ['device_id'])
    op.create_index('idx_alerts_created', 'alerts', [sa.text('created_at DESC')])
    op.create_index('idx_alerts_resolved', 'alerts', ['resolved'])
    op.create_index('idx_alerts_severity', 'alerts', ['severity'])

def downgrade() -> None:
    op.drop_table('alerts')