from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date
import models
from database import get_db

router = APIRouter(prefix="/api/contributions", tags=["contributions"])

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


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
):
    query = db.query(models.Contribution)
    if member_id:
        query = query.filter(models.Contribution.member_id == member_id)
    if year:
        query = query.filter(models.Contribution.year == year)
    contributions = query.order_by(
        models.Contribution.year.desc(), models.Contribution.month.desc()
    ).all()
    return [
        {
            "id": c.id,
            "member_id": c.member_id,
            "member_name": c.member.name,
            "amount": c.amount,
            "month": c.month,
            "month_name": MONTHS[c.month - 1],
            "year": c.year,
            "date_paid": str(c.date_paid),
            "notes": c.notes,
        }
        for c in contributions
    ]


@router.get("/yearly-grid")
def yearly_grid(year: int, db: Session = Depends(get_db)):
    members = db.query(models.Member).order_by(models.Member.name).all()
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
            "date_joined": str(m.date_joined),
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


@router.get("/summary")
def contributions_summary(db: Session = Depends(get_db)):
    members = db.query(models.Member).order_by(models.Member.name).all()
    return [
        {
            "member_id": m.id,
            "member_name": m.name,
            "total": sum(c.amount for c in m.contributions),
            "count": len(m.contributions),
        }
        for m in members
    ]


@router.post("/", status_code=201)
def create_contribution(data: ContributionCreate, db: Session = Depends(get_db)):
    member = db.query(models.Member).filter(models.Member.id == data.member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    contribution = models.Contribution(**data.model_dump())
    db.add(contribution)
    db.commit()
    db.refresh(contribution)
    return {"id": contribution.id}


@router.delete("/{contribution_id}")
def delete_contribution(contribution_id: int, db: Session = Depends(get_db)):
    c = db.query(models.Contribution).filter(models.Contribution.id == contribution_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Contribution not found")
    db.delete(c)
    db.commit()
    return {"detail": "Deleted"}
