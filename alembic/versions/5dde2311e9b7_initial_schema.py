"""initial schema

Revision ID: 5dde2311e9b7
Revises: 
Create Date: 2025-02-17
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '5dde2311e9b7'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create funds table
    op.create_table(
        'funds',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('ticker', sa.String(10), unique=True, nullable=False),
        sa.Column('name', sa.String(255)),
        sa.Column('fund_type', sa.String(50)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    )

    # Create filings table
    op.create_table(
        'filings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('fund_id', sa.Integer(), sa.ForeignKey('funds.id'), nullable=False),
        sa.Column('filing_date', sa.DateTime(), nullable=False),
        sa.Column('period_end_date', sa.DateTime(), nullable=False),
        sa.Column('total_assets', sa.Float()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('fund_id', 'period_end_date', name='unique_fund_filing')
    )

    # Create holdings table
    op.create_table(
        'holdings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('filing_id', sa.Integer(), sa.ForeignKey('filings.id'), nullable=False),
        sa.Column('cusip', sa.String(9)),
        sa.Column('ticker', sa.String(10)),
        sa.Column('name', sa.String(255)),
        sa.Column('title', sa.String(255)),
        sa.Column('value', sa.Float()),
        sa.Column('percentage', sa.Float()),
        sa.Column('asset_type', sa.String(50)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # Create fund_relationships table
    op.create_table(
        'fund_relationships',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('parent_fund_id', sa.Integer(), sa.ForeignKey('funds.id'), nullable=False),
        sa.Column('child_fund_id', sa.Integer(), sa.ForeignKey('funds.id'), nullable=False),
        sa.Column('filing_id', sa.Integer(), sa.ForeignKey('filings.id'), nullable=False),
        sa.Column('percentage', sa.Float()),
        sa.Column('value', sa.Float()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('parent_fund_id', 'child_fund_id', 'filing_id', name='unique_fund_relationship')
    )

def downgrade():
    op.drop_table('fund_relationships')
    op.drop_table('holdings')
    op.drop_table('filings')
    op.drop_table('funds') 