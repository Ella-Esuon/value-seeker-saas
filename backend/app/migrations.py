from sqlalchemy import text
from .database import engine


def run_migrations():
    with engine.connect() as conn:
        # ── tenants table ────────────────────────────────────────────────────
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS tenants (
                id         SERIAL PRIMARY KEY,
                name       VARCHAR NOT NULL,
                slug       VARCHAR UNIQUE NOT NULL,
                is_active  BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        conn.commit()

        conn.execute(text("""
            INSERT INTO tenants (name, slug, is_active)
            VALUES ('Default Group', 'default', TRUE)
            ON CONFLICT (slug) DO UPDATE SET is_active = TRUE
        """))
        conn.commit()

        # ── users: new columns ───────────────────────────────────────────────
        conn.execute(text("""
            ALTER TABLE users
                ADD COLUMN IF NOT EXISTS is_superadmin BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS tenant_id INTEGER REFERENCES tenants(id)
        """))
        conn.commit()

        # Drop old global unique on username (replaced by per-tenant constraint)
        conn.execute(text("""
            ALTER TABLE users DROP CONSTRAINT IF EXISTS users_username_key
        """))
        conn.commit()

        # Backfill existing users → default tenant
        conn.execute(text("""
            UPDATE users
            SET tenant_id = (SELECT id FROM tenants WHERE slug = 'default')
            WHERE tenant_id IS NULL AND is_superadmin = FALSE
        """))
        conn.commit()

        # ── members: tenant_id ───────────────────────────────────────────────
        conn.execute(text("""
            ALTER TABLE members ADD COLUMN IF NOT EXISTS tenant_id INTEGER REFERENCES tenants(id)
        """))
        conn.commit()

        conn.execute(text("""
            UPDATE members
            SET tenant_id = (SELECT id FROM tenants WHERE slug = 'default')
            WHERE tenant_id IS NULL
        """))
        conn.commit()

        conn.execute(text("""
            ALTER TABLE members ALTER COLUMN tenant_id SET NOT NULL
        """))
        conn.commit()

        # ── contributions: tenant_id ─────────────────────────────────────────
        conn.execute(text("""
            ALTER TABLE contributions ADD COLUMN IF NOT EXISTS tenant_id INTEGER REFERENCES tenants(id)
        """))
        conn.commit()

        conn.execute(text("""
            UPDATE contributions
            SET tenant_id = (SELECT id FROM tenants WHERE slug = 'default')
            WHERE tenant_id IS NULL
        """))
        conn.commit()

        conn.execute(text("""
            ALTER TABLE contributions ALTER COLUMN tenant_id SET NOT NULL
        """))
        conn.commit()

        # ── loans: tenant_id ─────────────────────────────────────────────────
        conn.execute(text("""
            ALTER TABLE loans ADD COLUMN IF NOT EXISTS tenant_id INTEGER REFERENCES tenants(id)
        """))
        conn.commit()

        conn.execute(text("""
            UPDATE loans
            SET tenant_id = (SELECT id FROM tenants WHERE slug = 'default')
            WHERE tenant_id IS NULL
        """))
        conn.commit()

        conn.execute(text("""
            ALTER TABLE loans ALTER COLUMN tenant_id SET NOT NULL
        """))
        conn.commit()

        # ── drop old global unique constraints ───────────────────────────────
        conn.execute(text("""
            ALTER TABLE members DROP CONSTRAINT IF EXISTS members_membership_id_key
        """))
        conn.commit()

        # ── users: full_name column (profile feature) ────────────────────────
        conn.execute(text("""
            ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR
        """))
        conn.commit()

        # ── add scoped unique constraints (idempotent) ───────────────────────
        conn.execute(text("""
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'uq_member_tenant_membership'
                ) THEN
                    ALTER TABLE members
                        ADD CONSTRAINT uq_member_tenant_membership UNIQUE (tenant_id, membership_id);
                END IF;
            END $$
        """))
        conn.commit()

        conn.execute(text("""
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'uq_user_tenant_username'
                ) THEN
                    ALTER TABLE users
                        ADD CONSTRAINT uq_user_tenant_username UNIQUE (tenant_id, username);
                END IF;
            END $$
        """))
        conn.commit()
