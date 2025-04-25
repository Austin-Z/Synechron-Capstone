from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint, Enum, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Fund(Base):
    """Fund table for storing basic fund information."""
    __tablename__ = 'funds'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    fund_type = Column(Enum('fund_of_funds', 'underlying_fund', name='fund_type'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    filings = relationship("Filing", back_populates="fund")
    holdings_as_parent = relationship("FundRelationship", 
                                    foreign_keys="FundRelationship.parent_fund_id",
                                    back_populates="parent_fund")
    holdings_as_child = relationship("FundRelationship", 
                                   foreign_keys="FundRelationship.child_fund_id",
                                   back_populates="child_fund")

    def __repr__(self):
        return f"<Fund(ticker='{self.ticker}', name='{self.name}', type='{self.fund_type}')>"

class Filing(Base):
    """NPORT filing metadata."""
    __tablename__ = 'filings'
    
    id = Column(Integer, primary_key=True)
    fund_id = Column(Integer, ForeignKey('funds.id'), nullable=False)
    filing_date = Column(DateTime, nullable=False)
    period_end_date = Column(DateTime, nullable=False)
    total_assets = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    fund = relationship("Fund", back_populates="filings")
    holdings = relationship("Holding", back_populates="filing")
    
    # Ensure one filing per fund per period
    __table_args__ = (UniqueConstraint('fund_id', 'period_end_date', name='unique_fund_filing'),)

class Holding(Base):
    """Individual holdings within a filing."""
    __tablename__ = 'holdings'
    
    id = Column(Integer, primary_key=True)
    filing_id = Column(Integer, ForeignKey('filings.id'), nullable=False)
    cusip = Column(String(9))
    ticker = Column(String(10))
    name = Column(String(255))
    title = Column(String(255))
    value = Column(Float)
    percentage = Column(Float)
    asset_type = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    filing = relationship("Filing", back_populates="holdings")

class FundRelationship(Base):
    """Tracks fund of funds relationships over time."""
    __tablename__ = 'fund_relationships'
    
    id = Column(Integer, primary_key=True)
    parent_fund_id = Column(Integer, ForeignKey('funds.id'), nullable=False)
    child_fund_id = Column(Integer, ForeignKey('funds.id'), nullable=False)
    filing_id = Column(Integer, ForeignKey('filings.id'), nullable=False)
    percentage = Column(Float)
    value = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    parent_fund = relationship("Fund", foreign_keys=[parent_fund_id], back_populates="holdings_as_parent")
    child_fund = relationship("Fund", foreign_keys=[child_fund_id], back_populates="holdings_as_child")
    filing = relationship("Filing")
    
    # Ensure unique relationship per filing
    __table_args__ = (UniqueConstraint('parent_fund_id', 'child_fund_id', 'filing_id', 
                                      name='unique_fund_relationship'),) 