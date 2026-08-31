
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'devices',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('device_id', sa.String(100), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('sensor_type', sa.String(50), nullable=False),
        sa.Column('location', sa.String(200), nullable=True),
        sa.Column('building', sa.String(100), nullable=True),
        sa.Column('floor', sa.Integer(), nullable=True),
        sa.Column('room', sa.String(50), nullable=True),
        sa.Column('installation_date', sa.Date(), nullable=True),
        sa.Column('firmware_version', sa.String(20), nullable=True),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.Column('metadata', JSONB(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('device_id')
    )
    
    op.create_index('idx_devices_type', 'devices', ['sensor_type'])
    op.create_index('idx_devices_status', 'devices', ['status'])
    op.create_index('idx_devices_location', 'devices', ['location'])
    op.create_index('idx_devices_device_id', 'devices', ['device_id'])

def downgrade() -> None:
    op.drop_table('devices')