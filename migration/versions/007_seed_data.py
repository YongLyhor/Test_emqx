
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Seed device_types
    op.execute("""
        INSERT INTO device_types (type_code, display_name, description, default_unit, min_value, max_value, alert_threshold) VALUES
            ('water', 'Water Meter', 'Measures water consumption in cubic meters.', 'm³', 0, 999999.999999, 5000),
            ('electricity', 'Electricity Meter', 'Measures electrical energy consumption.', 'kWh', 0, 99999999.999999, 50000),
            ('gas', 'Gas Meter', 'Measures natural gas consumption.', 'm³/h', 0, 99999.999999, 1000),
            ('cooling', 'Cooling Meter', 'Measures cooling energy consumption.', 'kW', 0, 99999.999999, 800)
        ON CONFLICT (type_code) DO NOTHING
    """)
    
    # Seed sample devices
    op.execute("""
        INSERT INTO devices (device_id, name, sensor_type, location, building, floor, room, status, metadata) VALUES
            ('WTR-001-BLDG-A', 'Main Water Meter - Building A', 'water', 'Basement - Utility Room 101', 'Building A', -1, 'Utility Room 101', 'active', 
             '{"manufacturer": "Siemens", "model": "Sitrans F M230", "serial_number": "SN-2025-001234"}'::jsonb),
            ('ELC-003-FLOOR-2', 'Smart Meter - Tower A Floor 2', 'electricity', 'Electrical Room - Floor 2', 'Tower A', 2, 'Room 2A-45', 'active',
             '{"manufacturer": "Schneider Electric", "model": "PowerLogic ION 8800", "serial_number": "SE-2025-004567"}'::jsonb),
            ('GAS-002-KITCHEN', 'Gas Meter - Main Kitchen', 'gas', 'Kitchen - Ground Floor', 'Building B', 0, 'Kitchen', 'active',
             '{"manufacturer": "Elster", "model": "G250", "serial_number": "EL-2025-007890"}'::jsonb),
            ('CLG-005-CHILLER', 'Chiller Cooling Meter - Plant Room', 'cooling', 'Chiller Plant Room - Basement', 'Building C', -2, 'Plant Room PR-001', 'active',
             '{"manufacturer": "Danfoss", "model": "SonoSelect 4", "serial_number": "DN-2025-009876"}'::jsonb)
        ON CONFLICT (device_id) DO NOTHING
    """)

def downgrade() -> None:
    op.execute("DELETE FROM devices")
    op.execute("DELETE FROM device_types")