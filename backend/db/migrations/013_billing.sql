-- =====================================================================
-- 013_billing — Stripe subscriptions. Stripe is the source of truth for
-- subscription state; users.tier is the synced cache the app gates on. The
-- webhook (signature-verified) updates both. subscriptions is tenant-scoped
-- with FORCE RLS like every other tenant table.
-- =====================================================================

ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(64);
CREATE INDEX IF NOT EXISTS idx_users_stripe_customer ON users(stripe_customer_id);

CREATE TABLE IF NOT EXISTS subscriptions (
  subscription_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  tenant_id              UUID NOT NULL REFERENCES tenants(tenant_id),
  stripe_subscription_id VARCHAR(64) NOT NULL UNIQUE,
  stripe_customer_id     VARCHAR(64) NOT NULL,
  status                 VARCHAR(32) NOT NULL,   -- active, trialing, past_due, canceled, …
  tier                   VARCHAR(20) NOT NULL,   -- plus | premium
  current_period_end     TIMESTAMPTZ,
  cancel_at_period_end   BOOLEAN NOT NULL DEFAULT false,
  created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_tenant ON subscriptions(tenant_id);

ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_subscriptions ON subscriptions
  USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
  WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

GRANT SELECT, INSERT, UPDATE ON subscriptions TO app_user;
