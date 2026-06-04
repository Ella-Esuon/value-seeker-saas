from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date
from .. import models
from ..auth import get_tenant_id
from ..database import get_db
from ..utils.amortization import calculate_monthly_installment, amortization_schedule, split_repayment

router = APIRouter(prefix="/api/loans", tags=["loans"])

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]


def loan_dict(loan: models.Loan) -> dict:
    repaid_principal = sum(r.principal_paid for r in loan.repayments)
    repaid_interest  = sum(r.interest_paid  for r in loan.repayments)
    total_repaid     = sum(r.amount          for r in loan.repayments)
    balance          = round(max(0, loan.amount - repaid_principal), 2)
    return {
        "id": loan.id,
        "member_id": loan.member_id,
        "member_name": loan.member.name,
        "membership_id": loan.member.membership_id,
        "amount": loan.amount,
        "interest_rate": loan.interest_rate,
        "term_months": loan.term_months,
        "monthly_installment": loan.monthly_installment,
        "date_applied": str(loan.date_applied),
        "date_issued": str(loan.date_issued) if loan.date_issued else None,
        "due_date": str(loan.due_date) if loan.due_date else None,
        "purpose": loan.purpose,
        "status": loan.status,
        "notes": loan.notes,
        "total_repaid": round(total_repaid, 2),
        "repaid_principal": round(repaid_principal, 2),
        "repaid_interest": round(repaid_interest, 2),
        "balance": balance,
        "payments_made": len(loan.repayments),
        "repayments": [
            {
                "id": r.id,
                "payment_number": r.payment_number,
                "amount": r.amount,
                "principal_paid": r.principal_paid,
                "interest_paid": r.interest_paid,
                "balance_after": r.balance_after,
                "date_paid": str(r.date_paid),
                "notes": r.notes,
            }
            for r in sorted(loan.repayments, key=lambda r: r.date_paid)
        ],
    }


class LoanCreate(BaseModel):
    member_id: int
    amount: float
    interest_rate: float = 0.0
    term_months: int
    date_applied: date
    purpose: Optional[str] = None
    notes: Optional[str] = None


class RepaymentCreate(BaseModel):
    amount: float
    date_paid: date
    notes: Optional[str] = None


@router.get("/")
def list_loans(
    member_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    q = db.query(models.Loan).filter(models.Loan.tenant_id == tenant_id)
    if member_id:
        q = q.filter(models.Loan.member_id == member_id)
    if status:
        q = q.filter(models.Loan.status == status)
    return [loan_dict(l) for l in q.order_by(models.Loan.date_applied.desc()).all()]


@router.get("/monthly-chart")
def loan_monthly_chart(
    year: int,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    disbursements = [0.0] * 12
    repayments    = [0.0] * 12
    loans = db.query(models.Loan).filter(
        models.Loan.tenant_id == tenant_id,
        models.Loan.date_issued != None,
    ).all()
    for l in loans:
        if l.date_issued and l.date_issued.year == year:
            disbursements[l.date_issued.month - 1] += l.amount
    all_repayments = (
        db.query(models.LoanRepayment)
        .join(models.Loan)
        .filter(models.Loan.tenant_id == tenant_id)
        .all()
    )
    for r in all_repayments:
        if r.date_paid.year == year:
            repayments[r.date_paid.month - 1] += r.amount
    return {
        "labels": MONTHS,
        "disbursements": [round(x, 2) for x in disbursements],
        "repayments": [round(x, 2) for x in repayments],
    }


@router.get("/{loan_id}")
def get_loan(
    loan_id: int,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    loan = db.query(models.Loan).filter(
        models.Loan.id == loan_id,
        models.Loan.tenant_id == tenant_id,
    ).first()
    if not loan:
        raise HTTPException(404, "Loan not found")
    return loan_dict(loan)


@router.get("/{loan_id}/schedule")
def get_amortization(
    loan_id: int,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    loan = db.query(models.Loan).filter(
        models.Loan.id == loan_id,
        models.Loan.tenant_id == tenant_id,
    ).first()
    if not loan:
        raise HTTPException(404, "Loan not found")
    schedule = amortization_schedule(loan.amount, loan.interest_rate, loan.term_months)
    total_interest = sum(p["interest"] for p in schedule)
    return {
        "loan_id": loan_id,
        "principal": loan.amount,
        "interest_rate": loan.interest_rate,
        "term_months": loan.term_months,
        "monthly_installment": loan.monthly_installment,
        "total_interest": round(total_interest, 2),
        "total_payable": round(loan.amount + total_interest, 2),
        "schedule": schedule,
    }


@router.post("/", status_code=201)
def create_loan(
    data: LoanCreate,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    member = db.query(models.Member).filter(
        models.Member.id == data.member_id,
        models.Member.tenant_id == tenant_id,
    ).first()
    if not member:
        raise HTTPException(404, "Member not found")
    installment = calculate_monthly_installment(data.amount, data.interest_rate, data.term_months)
    loan = models.Loan(monthly_installment=installment, tenant_id=tenant_id, **data.model_dump())
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return loan_dict(loan)


@router.put("/{loan_id}/approve")
def approve_loan(
    loan_id: int,
    date_issued: str,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    from datetime import date as date_type, datetime
    loan = db.query(models.Loan).filter(
        models.Loan.id == loan_id,
        models.Loan.tenant_id == tenant_id,
    ).first()
    if not loan:
        raise HTTPException(404, "Loan not found")
    if loan.status != "pending":
        raise HTTPException(400, "Only pending loans can be approved")
    issued = datetime.strptime(date_issued, "%Y-%m-%d").date()
    total_months = issued.month + loan.term_months
    due_year  = issued.year + (total_months - 1) // 12
    due_month = (total_months - 1) % 12 + 1
    loan.status     = "active"
    loan.date_issued = issued
    loan.due_date    = date_type(due_year, due_month, issued.day)
    db.commit()
    return loan_dict(loan)


@router.put("/{loan_id}/reject")
def reject_loan(
    loan_id: int,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    loan = db.query(models.Loan).filter(
        models.Loan.id == loan_id,
        models.Loan.tenant_id == tenant_id,
    ).first()
    if not loan:
        raise HTTPException(404, "Loan not found")
    loan.status = "rejected"
    db.commit()
    return loan_dict(loan)


@router.post("/{loan_id}/repayments", status_code=201)
def add_repayment(
    loan_id: int,
    data: RepaymentCreate,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    loan = db.query(models.Loan).filter(
        models.Loan.id == loan_id,
        models.Loan.tenant_id == tenant_id,
    ).first()
    if not loan:
        raise HTTPException(404, "Loan not found")
    if loan.status != "active":
        raise HTTPException(400, "Loan is not active")
    repaid_so_far   = sum(r.principal_paid for r in loan.repayments)
    current_balance = loan.amount - repaid_so_far
    principal, interest, new_balance = split_repayment(current_balance, loan.interest_rate, data.amount)
    repayment = models.LoanRepayment(
        loan_id=loan_id,
        payment_number=len(loan.repayments) + 1,
        amount=data.amount,
        principal_paid=principal,
        interest_paid=interest,
        balance_after=new_balance,
        date_paid=data.date_paid,
        notes=data.notes,
    )
    db.add(repayment)
    if new_balance <= 0.01:
        loan.status = "paid"
    db.commit()
    return loan_dict(loan)


@router.delete("/{loan_id}/repayments/{repayment_id}")
def delete_repayment(
    loan_id: int,
    repayment_id: int,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    r = db.query(models.LoanRepayment).filter(
        models.LoanRepayment.id == repayment_id,
        models.LoanRepayment.loan_id == loan_id,
    ).first()
    if not r or r.loan.tenant_id != tenant_id:
        raise HTTPException(404, "Not found")
    if r.loan.status == "paid":
        r.loan.status = "active"
    db.delete(r)
    db.commit()
    return {"detail": "Deleted"}


@router.delete("/{loan_id}")
def delete_loan(
    loan_id: int,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    loan = db.query(models.Loan).filter(
        models.Loan.id == loan_id,
        models.Loan.tenant_id == tenant_id,
    ).first()
    if not loan:
        raise HTTPException(404, "Not found")
    db.delete(loan)
    db.commit()
    return {"detail": "Deleted"}
