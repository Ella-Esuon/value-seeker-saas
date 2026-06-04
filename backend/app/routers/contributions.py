from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date
from .. import models
from ..auth import get_tenant_id
from ..database import get_db

router = APIRouter(prefix="/api/contributions", tags=["contributions"])

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]


class ContributionCreate(BaseModel):
    member_id: int
    amount: float
    month: int
    year: int
    date_paid: date
    notes: Optional[str] = None


@router.get("/")
def list_contributions(
    member_id: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    q = db.query(models.Contribution).filter(models.Contribution.tenant_id == tenant_id)
    if member_id:
        q = q.filter(models.Contribution.member_id == member_id)
    if year:
        q = q.filter(models.Contribution.year == year)
    return [
        {
            "id": c.id,
            "member_id": c.member_id,
            "member_name": c.member.name,
            "membership_id": c.member.membership_id,
            "amount": c.amount,
            "month": c.month,
            "month_name": MONTHS[c.month - 1],
            "year": c.year,
            "date_paid": str(c.date_paid),
            "notes": c.notes,
        }
        for c in q.order_by(models.Contribution.year.desc(), models.Contribution.month.desc()).all()
    ]


@router.get("/yearly-grid")
def yearly_grid(
    year: int,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    members = (
        db.query(models.Member)
        .filter(models.Member.tenant_id == tenant_id)
        .order_by(models.Member.name)
        .all()
    )
    rows = []
    col_totals = {m: 0.0 for m in range(1, 13)}
    for m in members:
        months = {}
        year_total = 0.0
        cumulative_total = sum(c.amount for c in m.contributions)
        for c in m.contributions:
            if c.year == year:
                if c.month not in months:
                    months[c.month] = {"ids": [], "amount": 0.0}
                months[c.month]["ids"].append(c.id)
                months[c.month]["amount"] += c.amount
                year_total += c.amount
                col_totals[c.month] += c.amount
        rows.append({
            "member_id": m.id,
            "member_name": m.name,
            "membership_id": m.membership_id,
            "status": m.status,
            "months": months,
            "year_total": round(year_total, 2),
            "cumulative_total": round(cumulative_total, 2),
        })
    return {
        "year": year,
        "members": rows,
        "col_totals": {str(k): round(v, 2) for k, v in col_totals.items()},
        "grand_year_total": round(sum(r["year_total"] for r in rows), 2),
        "grand_cumulative": round(sum(r["cumulative_total"] for r in rows), 2),
    }


@router.get("/monthly-chart")
def monthly_chart(
    year: int,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    data = [0.0] * 12
    contribs = (
        db.query(models.Contribution)
        .filter(
            models.Contribution.tenant_id == tenant_id,
            models.Contribution.year == year,
        )
        .all()
    )
    for c in contribs:
        data[c.month - 1] += c.amount
    return {"year": year, "data": [round(x, 2) for x in data], "labels": MONTHS}


@router.post("/", status_code=201)
def create_contribution(
    data: ContributionCreate,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    member = db.query(models.Member).filter(
        models.Member.id == data.member_id,
        models.Member.tenant_id == tenant_id,
    ).first()
    if not member:
        raise HTTPException(404, "Member not found")
    c = models.Contribution(tenant_id=tenant_id, **data.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"id": c.id}


@router.delete("/{contribution_id}")
def delete_contribution(
    contribution_id: int,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    c = db.query(models.Contribution).filter(
        models.Contribution.id == contribution_id,
        models.Contribution.tenant_id == tenant_id,
    ).first()
    if not c:
        raise HTTPException(404, "Not found")
    db.delete(c)
    db.commit()
    return {"detail": "Deleted"}
