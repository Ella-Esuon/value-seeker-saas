from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine, SessionLocal
from . import models
from .auth import hash_password
from .migrations import run_migrations
from .routers import auth, members, contributions, loans, dashboard, reports, tenants
from .core.config import settings

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
    admin_user = settings.ADMIN_USERNAME
    admin_pass = settings.ADMIN_PASSWORD
    sa_pass    = settings.SUPERADMIN_PASSWORD

    print(f"[seed] ADMIN_USERNAME           = {admin_user}")
    print(f"[seed] len(ADMIN_PASSWORD)      = {len(admin_pass)}")
    print(f"[seed] len(SUPERADMIN_PASSWORD) = {len(sa_pass)}")

    db = SessionLocal()
    try:
        tenant = db.query(models.Tenant).filter_by(slug="default").first()
        if not tenant:
            tenant = models.Tenant(name="Default Group", slug="default", is_active=True)
            db.add(tenant)
            db.flush()
            print("[seed] Created default tenant")
        else:
            if not tenant.is_active:
                tenant.is_active = True
                print(f"[seed] Fixed is_active=NULL on default tenant (id={tenant.id})")
            else:
                print(f"[seed] Default tenant already exists (id={tenant.id})")

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
            print(f"[seed] Created admin user '{admin_user}'")
        else:
            print(f"[seed] Admin user '{admin_user}' already exists — skipping")

        sa = db.query(models.User).filter_by(is_superadmin=True).first()
        if not sa:
            db.add(models.User(
                username="superadmin",
                hashed_password=hash_password(sa_pass),
                is_active=True,
                is_superadmin=True,
                tenant_id=None,
            ))
            print("[seed] Created superadmin user")
        else:
            print("[seed] Superadmin user already exists — skipping")

        db.commit()
        print("[seed] Seed complete")
    except Exception as exc:
        db.rollback()
        print(f"[seed] ERROR during seed: {exc}")
        raise
    finally:
        db.close()


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "VALUE SEEKER API v3"}
