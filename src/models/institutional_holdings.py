from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime
from src.models.database import Base

class Institute13F(Base):
    """Institutional investor table for storing 13F filers."""
    __tablename__ = 'institute13f'
    
    id = Column(Integer, primary_key=True)
    institution_name = Column(String(255))
    report_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    holdings = relationship("InstitutionalHolding", back_populates="report")
    
    def __repr__(self):
        return f"<Institute13F(id={self.id}, name='{self.institution_name}')>"

class InstitutionalHolding(Base):
    """Individual holdings within a 13F filing."""
    __tablename__ = 'institutional_holdings'
    
    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey('institute13f.id'), nullable=False)
    ticker = Column(String(10))
    cusip = Column(String(9))
    issuer_name = Column(String(255))
    security_class = Column(String(50))
    value = Column(Float)
    percentage = Column(Float)
    shares = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    report = relationship("Institute13F", back_populates="holdings")
    
    def __repr__(self):
        return f"<InstitutionalHolding(name='{self.issuer_name}', ticker='{self.ticker}', value={self.value})>"
