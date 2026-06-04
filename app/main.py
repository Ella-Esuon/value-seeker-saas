import os
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import models
from database import Base, engine, get_db
from routers import members, contributions, loans

os.makedirs("/data", exist_ok=True)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="VALUE SEEKER Financial Management")

app.include_router(members.router)
app.include_router(contributions.router)
app.include_router(loans.router)


@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db)):
    all_members = db.query(models.Member).all()
    all_contributions = db.query(models.Contribution).all()
    all_loans = db.query(models.Loan).all()

    total_contributions = sum(c.amount for c in all_contributions)
    active_loans = [l for l in all_loans if l.status == "active"]
    active_loan_balance = sum(
        max(0, l.principal * (1 + l.interest_rate / 100) - sum(r.amount for r in l.repayments))
        for l in active_loans
    )
    total_disbursed = sum(l.principal for l in all_loans)
    total_repaid = sum(r.amount for l in all_loans for r in l.repayments)

    return {
        "total_members": len(all_members),
        "total_contributions": round(total_contributions, 2),
        "active_loans_count": len(active_loans),
        "active_loan_balance": round(active_loan_balance, 2),
        "total_loans_disbursed": round(total_disbursed, 2),
        "total_repaid": round(total_repaid, 2),
    }


app.mount("/", StaticFiles(directory="/static", html=True), name="static")
