from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from datetime import date
import models
from database import get_db

router = APIRouter(prefix="/api/members", tags=["members"])


class MemberCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    date_joined: date


class MemberUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


@router.get("/")
def list_members(db: Session = Depends(get_db)):
    members = db.query(models.Member).order_by(models.Member.name).all()
    result = []
    for m in members:
        total_contributions = sum(c.amount for c in m.contributions)
        active_loans = sum(
            l.principal - sum(r.amount for r in l.repayments)
            for l in m.loans if l.status == "active"
        )
        result.append({
            "id": m.id,
            "name": m.name,
            "email": m.email,
            "phone": m.phone,
            "date_joined": str(m.date_joined),
            "total_contributions": total_contributions,
            "active_loan_balance": active_loans,
        })
    return result


@router.post("/", status_code=201)
def create_member(data: MemberCreate, db: Session = Depends(get_db)):
    member = models.Member(**data.model_dump())
    db.add(member)
    db.commit()
    db.refresh(member)
    return {"id": member.id, "name": member.name}


@router.put("/{member_id}")
def update_member(member_id: int, data: MemberUpdate, db: Session = Depends(get_db)):
    member = db.query(models.Member).filter(models.Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(member, field, value)
    db.commit()
    return {"id": member.id, "name": member.name}


@router.delete("/{member_id}")
def delete_member(member_id: int, db: Session = Depends(get_db)):
    member = db.query(models.Member).filter(models.Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(member)
    db.commit()
    return {"detail": "Deleted"}
