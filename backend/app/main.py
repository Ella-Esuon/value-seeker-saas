import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine, SessionLocal
from . import models
from .auth import hash_password
from .migrations import run_migrations
from .routers import auth, members, contributions, loans, dashboard, reports, tenants

Base.metadata.create_all(bind=engine)
run_migrations()

app = FastAPI(title="VALUE SEEKER API", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(members.router)
app.include_router(contributions.router)
app.include_router(loans.router)
app.include_router(dashboard.router)
app.include_router(reports.router)
app.include_router(tenants.router)


@app.on_event("startup")
def seed():
    db = SessionLocal()
    try:
        # Ensure default tenant exists
        tenant = db.query(models.Tenant).filter_by(slug="default").first()
        if not tenant:
            tenant = models.Tenant(name="Default Group", slug="default")
            db.add(tenant)
            db.flush()

        # Seed tenant admin
        admin_user = os.getenv("ADMIN_USERNAME", "admin")
        admin_pass = os.getenv("ADMIN_PASSWORD", "ad123")
        exists = db.query(models.User).filter_by(username=admin_user, tenant_id=tenant.id).first()
        if not exists:
            db.add(models.User(
                username=admin_user,
                email="admin@valueseeker.com",
                hashed_password=hash_password(admin_pass),
                is_active=True,
                is_admin=True,
                tenant_id=tenant.id,
            ))

        # Seed superadmin (no tenant)
        sa = db.query(models.User).filter_by(is_superadmin=True).first()
        if not sa:
            sa_pass = os.getenv("SUPERADMIN_PASSWORD", "super123")
            db.add(models.User(
                username="superadmin",
                hashed_password=hash_password(sa_pass),
                is_active=True,
                is_superadmin=True,
                tenant_id=None,
            ))

        db.commit()
    finally:
        db.close()


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "VALUE SEEKER API v3"}
