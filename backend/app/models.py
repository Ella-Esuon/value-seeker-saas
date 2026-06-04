from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Boolean, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class Tenant(Base):
    __tablename__ = "tenants"
    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String, nullable=False)
    slug       = Column(String, unique=True, index=True)
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users   = relationship("User",   back_populates="tenant")
    members = relationship("Member", back_populates="tenant")


class User(Base):
    __tablename__ = "users"
    id              = Column(Integer, primary_key=True, index=True)
    tenant_id       = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    username        = Column(String, nullable=False)
    email           = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active       = Column(Boolean, default=True)
    is_admin        = Column(Boolean, default=False)
    is_superadmin   = Column(Boolean, default=False)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="users")

    __table_args__ = (
        UniqueConstraint("tenant_id", "username", name="uq_user_tenant_username"),
    )


class Member(Base):
    __tablename__ = "members"
    id            = Column(Integer, primary_key=True, index=True)
    tenant_id     = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    membership_id = Column(String, index=True)
    name          = Column(String, nullable=False)
    phone         = Column(String)
    email         = Column(String)
    address       = Column(Text)
    date_joined   = Column(Date, nullable=False)
    status        = Column(String, default="active")
    created_at    = Column(DateTime(timezone=True), server_default=func.now())

    tenant        = relationship("Tenant", back_populates="members")
    contributions = relationship("Contribution", back_populates="member", cascade="all, delete-orphan")
    loans         = relationship("Loan",         back_populates="member", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("tenant_id", "membership_id", name="uq_member_tenant_membership"),
    )


class Contribution(Base):
    __tablename__ = "contributions"
    id        = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    amount    = Column(Float, nullable=False)
    month     = Column(Integer, nullable=False)
    year      = Column(Integer, nullable=False)
    date_paid = Column(Date, nullable=False)
    notes     = Column(Text)

    member = relationship("Member", back_populates="contributions")


class Loan(Base):
    __tablename__ = "loans"
    id                  = Column(Integer, primary_key=True, index=True)
    tenant_id           = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    member_id           = Column(Integer, ForeignKey("members.id"), nullable=False)
    amount              = Column(Float, nullable=False)
    interest_rate       = Column(Float, default=0.0)
    term_months         = Column(Integer, nullable=False)
    monthly_installment = Column(Float)
    date_applied        = Column(Date, nullable=False)
    date_issued         = Column(Date)
    due_date            = Column(Date)
    purpose             = Column(Text)
    status              = Column(String, default="pending")
    notes               = Column(Text)

    member     = relationship("Member",        back_populates="loans")
    repayments = relationship("LoanRepayment", back_populates="loan", cascade="all, delete-orphan")


class LoanRepayment(Base):
    __tablename__ = "loan_repayments"
    id             = Column(Integer, primary_key=True, index=True)
    loan_id        = Column(Integer, ForeignKey("loans.id"), nullable=False)
    payment_number = Column(Integer)
    amount         = Column(Float, nullable=False)
    principal_paid = Column(Float, default=0.0)
    interest_paid  = Column(Float, default=0.0)
    balance_after  = Column(Float, default=0.0)
    date_paid      = Column(Date, nullable=False)
    notes          = Column(Text)

    loan = relationship("Loan", back_populates="repayments")
