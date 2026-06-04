from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date
from .. import models
from ..auth import get_current_user, get_tenant_id
from ..database import get_db

router = APIRouter(prefix="/api/members", tags=["members"])

MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]


def generate_membership_id(db: Session, year: int, tenant_id: int) -> str:
    prefix = f"VS-{year}-"
    existing = db.query(models.Member).filter(
        models.Member.membership_id.like(f"{prefix}%"),
        models.Member.tenant_id == tenant_id,
    ).count()
    return f"{prefix}{existing + 1:03d}"


def member_dict(m: models.Member) -> dict:
    total_contributions = sum(c.amount for c in m.contributions)
    loan_balance = 0.0
    for l in m.loans:
        if l.status in ("active", "approved"):
            repaid_principal = sum(r.principal_paid for r in l.repayments)
            loan_balance += max(0, l.amount - repaid_principal)
    return {
        "id": m.id,
        "membership_id": m.membership_id,
        "name": m.name,
        "phone": m.phone,
        "email": m.email,
        "address": m.address,
        "date_joined": str(m.date_joined),
        "status": m.status,
        "total_contributions": round(total_contributions, 2),
        "active_loan_balance": round(loan_balance, 2),
    }


class MemberCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    date_joined: date
    status: str = "active"


class MemberUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    status: Optional[str] = None


@router.get("/")
def list_members(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    q = db.query(models.Member).filter(models.Member.tenant_id == tenant_id)
    if status:
        q = q.filter(models.Member.status == status)
    return [member_dict(m) for m in q.order_by(models.Member.name).all()]


@router.get("/{member_id}")
def get_member(
    member_id: int,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    m = db.query(models.Member).filter(
        models.Member.id == member_id,
        models.Member.tenant_id == tenant_id,
    ).first()
    if not m:
        raise HTTPException(404, "Member not found")
    d = member_dict(m)
    contribs = {}
    for c in m.contributions:
        key = str(c.year)
        if key not in contribs:
            contribs[key] = {"year": c.year, "months": {}, "total": 0}
        contribs[key]["months"][c.month] = {"id": c.id, "amount": c.amount, "date_paid": str(c.date_paid)}
        contribs[key]["total"] += c.amount
    d["contribution_history"] = sorted(contribs.values(), key=lambda x: x["year"], reverse=True)
    return d


@router.post("/", status_code=201)
def create_member(
    data: MemberCreate,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    membership_id = generate_membership_id(db, data.date_joined.year, tenant_id)
    member = models.Member(membership_id=membership_id, tenant_id=tenant_id, **data.model_dump())
    db.add(member)
    db.commit()
    db.refresh(member)
    return member_dict(member)


@router.put("/{member_id}")
def update_member(
    member_id: int,
    data: MemberUpdate,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    m = db.query(models.Member).filter(
        models.Member.id == member_id,
        models.Member.tenant_id == tenant_id,
    ).first()
    if not m:
        raise HTTPException(404, "Member not found")
    for field, val in data.model_dump(exclude_none=True).items():
        setattr(m, field, val)
    db.commit()
    return member_dict(m)


@router.delete("/{member_id}")
def delete_member(
    member_id: int,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    m = db.query(models.Member).filter(
        models.Member.id == member_id,
        models.Member.tenant_id == tenant_id,
    ).first()
    if not m:
        raise HTTPException(404, "Member not found")
    db.delete(m)
    db.commit()
    return {"detail": "Deleted"}
