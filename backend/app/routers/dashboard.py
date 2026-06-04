from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date
from .. import models
from ..auth import get_tenant_id
from ..database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/")
def dashboard(
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    year = date.today().year
    members = db.query(models.Member).filter(models.Member.tenant_id == tenant_id).all()
    active_members = [m for m in members if m.status == "active"]

    contributions = (
        db.query(models.Contribution)
        .filter(models.Contribution.tenant_id == tenant_id)
        .all()
    )
    annual_contributions = sum(c.amount for c in contributions if c.year == year)
    total_contributions  = sum(c.amount for c in contributions)

    loans = db.query(models.Loan).filter(models.Loan.tenant_id == tenant_id).all()
    total_disbursed  = sum(l.amount for l in loans if l.status in ("active", "paid"))
    total_repayments = sum(r.amount for l in loans for r in l.repayments)
    outstanding = sum(
        l.amount - sum(r.principal_paid for r in l.repayments)
        for l in loans if l.status == "active"
    )
    delinquent = [
        l for l in loans
        if l.status == "active" and l.due_date and l.due_date < date.today()
    ]

    return {
        "total_members": len(members),
        "active_members": len(active_members),
        "total_monthly_contributions": round(annual_contributions, 2),
        "total_annual_contributions": round(annual_contributions, 2),
        "total_contributions_all_time": round(total_contributions, 2),
        "total_loans_disbursed": round(total_disbursed, 2),
        "total_repayments_received": round(total_repayments, 2),
        "outstanding_loan_balance": round(max(0, outstanding), 2),
        "delinquent_loans_count": len(delinquent),
        "current_year": year,
    }
