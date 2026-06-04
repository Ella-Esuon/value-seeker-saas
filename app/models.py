from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    phone = Column(String, nullable=True)
    date_joined = Column(Date, nullable=False)

    contributions = relationship("Contribution", back_populates="member", cascade="all, delete-orphan")
    loans = relationship("Loan", back_populates="member", cascade="all, delete-orphan")


class Contribution(Base):
    __tablename__ = "contributions"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    amount = Column(Float, nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    date_paid = Column(Date, nullable=False)
    notes = Column(String, nullable=True)

    member = relationship("Member", back_populates="contributions")


class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    principal = Column(Float, nullable=False)
    interest_rate = Column(Float, default=0.0)
    date_issued = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    status = Column(String, default="active")  # active | paid | defaulted
    notes = Column(String, nullable=True)

    member = relationship("Member", back_populates="loans")
    repayments = relationship("LoanRepayment", back_populates="loan", cascade="all, delete-orphan")


class LoanRepayment(Base):
    __tablename__ = "loan_repayments"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loans.id"), nullable=False)
    amount = Column(Float, nullable=False)
    date_paid = Column(Date, nullable=False)
    notes = Column(String, nullable=True)

    loan = relationship("Loan", back_populates="repayments")
