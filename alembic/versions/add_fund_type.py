"""add fund type column

Revision ID: 1a2b3c4d5e6f
Revises: 5dde2311e9b7
Create Date: 2024-03-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# Update down_revision to point to initial schema
revision = '1a2b3c4d5e6f'
down_revision = '5dde2311e9b7'  # Change this to match initial schema revision

def upgrade():
    # Get inspector to check existing columns
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [c['name'] for c in inspector.get_columns('funds')]
    
    # Define the enum type
    fund_type_enum = sa.Enum('fund_of_funds', 'underlying_fund', name='fund_type')
    
    # Only add column if it doesn't exist
    if 'fund_type' not in columns:
        op.add_column('funds', 
            sa.Column('fund_type', fund_type_enum, nullable=True)
        )
    
    # Update fund types using correct join through filings
    op.execute("""
    UPDATE funds f
    SET fund_type = CASE
        WHEN EXISTS (
            SELECT 1 
            FROM filings fil
            JOIN holdings h ON h.filing_id = fil.id
            WHERE fil.fund_id = f.id 
            AND h.asset_type IN ('RF EC', 'RF STIV')  -- Update these to match your actual fund categories
            GROUP BY fil.fund_id
            HAVING COUNT(*) > (
                SELECT COUNT(*) 
                FROM filings f2 
                JOIN holdings h2 ON h2.filing_id = f2.id 
                WHERE f2.fund_id = f.id
            ) / 2
        ) THEN 'fund_of_funds'
        ELSE 'underlying_fund'
    END
    WHERE fund_type IS NULL
    """)
    
    # Make non-nullable by modifying with existing type
    op.alter_column('funds', 'fund_type',
                    existing_type=fund_type_enum,
                    nullable=False)

def downgrade():
    op.drop_column('funds', 'fund_type') 