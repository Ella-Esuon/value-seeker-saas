from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date
import models
from database import get_db

router = APIRouter(prefix="/api/loans", tags=["loans"])


class LoanCreate(BaseModel):
    member_id: int
    principal: float
    interest_rate: float = 0.0
    date_issued: date
    due_date: Optional[date] = None
    notes: Optional[str] = None


class LoanStatusUpdate(BaseModel):
    status: str


class RepaymentCreate(BaseModel):
    amount: float
    date_paid: date
    notes: Optional[str] = None


def loan_to_dict(loan: models.Loan) -> dict:
    total_repaid = sum(r.amount for r in loan.repayments)
    interest_amount = loan.principal * (loan.interest_rate / 100)
    total_due = loan.principal + interest_amount
    balance = max(0.0, total_due - total_repaid)
    return {
        "id": loan.id,
        "member_id": loan.member_id,
        "member_name": loan.member.name,
        "principal": loan.principal,
        "interest_rate": loan.interest_rate,
        "interest_amount": round(interest_amount, 2),
        "total_due": round(total_due, 2),
        "total_repaid": round(total_repaid, 2),
        "balance": round(balance, 2),
        "date_issued": str(loan.date_issued),
        "due_date": str(loan.due_date) if loan.due_date else None,
        "status": loan.status,
        "notes": loan.notes,
        "repayments": [
            {
                "id": r.id,
                "amount": r.amount,
                "date_paid": str(r.date_paid),
                "notes": r.notes,
            }
            for r in sorted(loan.repayments, key=lambda x: x.date_paid, reverse=True)
        ],
    }


@router.get("/")
def list_loans(
    member_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Loan)
    if member_id:
        query = query.filter(models.Loan.member_id == member_id)
    if status:
        query = query.filter(models.Loan.status == status)
    loans = query.order_by(models.Loan.date_issued.desc()).all()
    return [loan_to_dict(l) for l in loans]


@router.get("/{loan_id}")
def get_loan(loan_id: int, db: Session = Depends(get_db)):
    loan = db.query(models.Loan).filter(models.Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    return loan_to_dict(loan)


@router.post("/", status_code=201)
def create_loan(data: LoanCreate, db: Session = Depends(get_db)):
    member = db.query(models.Member).filter(models.Member.id == data.member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    loan = models.Loan(**data.model_dump())
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return loan_to_dict(loan)


@router.put("/{loan_id}/status")
def update_loan_status(loan_id: int, data: LoanStatusUpdate, db: Session = Depends(get_db)):
    loan = db.query(models.Loan).filter(models.Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    if data.status not in ("active", "paid", "defaulted"):
        raise HTTPException(status_code=400, detail="Invalid status")
    loan.status = data.status
    db.commit()
    return loan_to_dict(loan)


@router.post("/{loan_id}/repayments", status_code=201)
def add_repayment(loan_id: int, data: RepaymentCreate, db: Session = Depends(get_db)):
    loan = db.query(models.Loan).filter(models.Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    repayment = models.LoanRepayment(loan_id=loan_id, **data.model_dump())
    db.add(repayment)
    total_repaid = sum(r.amount for r in loan.repayments) + data.amount
    total_due = loan.principal * (1 + loan.interest_rate / 100)
    if total_repaid >= total_due:
        loan.status = "paid"
    db.commit()
    return loan_to_dict(loan)


@router.delete("/{loan_id}/repayments/{repayment_id}")
def delete_repayment(loan_id: int, repayment_id: int, db: Session = Depends(get_db)):
    r = db.query(models.LoanRepayment).filter(
        models.LoanRepayment.id == repayment_id,
        models.LoanRepayment.loan_id == loan_id,
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="Repayment not found")
    db.delete(r)
    db.commit()
    return {"detail": "Deleted"}


@router.delete("/{loan_id}")
def delete_loan(loan_id: int, db: Session = Depends(get_db)):
    loan = db.query(models.Loan).filter(models.Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    db.delete(loan)
    db.commit()
    return {"detail": "Deleted"}
