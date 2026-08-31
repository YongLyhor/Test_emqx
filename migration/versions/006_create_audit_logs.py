
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, INET

revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('table_name', sa.String(50), nullable=False),
        sa.Column('record_id', sa.String(100), nullable=False),
        sa.Column('action', sa.String(20), nullable=False),
        sa.Column('old_data', JSONB(), nullable=True),
        sa.Column('new_data', JSONB(), nullable=True),
        sa.Column('performed_by', sa.String(100), nullable=True),
        sa.Column('ip_address', INET(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_audit_table', 'audit_logs', ['table_name'])
    op.create_index('idx_audit_record', 'audit_logs', ['record_id'])
    op.create_index('idx_audit_created', 'audit_logs', [sa.text('created_at DESC')])
    op.create_index('idx_audit_action', 'audit_logs', ['action'])

def downgrade() -> None:
    op.drop_table('audit_logs')