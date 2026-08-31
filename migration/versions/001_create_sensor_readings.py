
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create table
    op.create_table(
        'sensor_readings',
        sa.Column('id', sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column('time', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('sensor_type', sa.String(50), nullable=False),
        sa.Column('device_id', sa.String(100), nullable=False),
        sa.Column('value', sa.Numeric(15, 6), nullable=False),
        sa.Column('unit', sa.String(20), nullable=False),
        sa.Column('quality', sa.Integer(), server_default='100'),
        sa.Column('metadata', JSONB(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('time', 'id')
    )
    
    # Create indexes
    op.create_index('idx_sensor_readings_type_time', 'sensor_readings', ['sensor_type', sa.text('time DESC')])
    op.create_index('idx_sensor_readings_device_time', 'sensor_readings', ['device_id', sa.text('time DESC')])
    op.create_index('idx_sensor_readings_time', 'sensor_readings', [sa.text('time DESC')])
    op.create_index('idx_sensor_readings_metadata_gin', 'sensor_readings', ['metadata'], postgresql_using='gin')
    
   
    op.execute("SELECT create_hypertable('sensor_readings', 'time', chunk_time_interval => INTERVAL '7 days')")

def downgrade() -> None:
    op.drop_table('sensor_readings')