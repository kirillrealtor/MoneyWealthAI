-- =====================================================================
-- 004_plaid_tenant_rls — Tenant isolation for all Plaid-owned data.
--
-- Denormalizes tenant_id onto each Plaid table (written at sync time) and
-- enforces FORCE RLS scoped by tenant, matching the users-table model. This
-- means even a bug that forgets a user_id filter cannot leak another tenant's
-- bank data — the database refuses to return it without the right tenant
-- context (set via app.with_tenant()).
--
-- Safe to add NOT NULL directly: no Plaid rows exist yet at this point.
-- =====================================================================

-- ---- Plaid's own item identifier (maps webhooks -> our rows; idempotent relink) ----
ALTER TABLE plaid_items ADD COLUMN plaid_item_id VARCHAR(100);
ALTER TABLE plaid_items ADD CONSTRAINT uq_plaid_item_id UNIQUE (plaid_item_id);

-- ---- tenant_id columns ----
ALTER TABLE plaid_items        ADD COLUMN tenant_id UUID REFERENCES tenants(tenant_id);
ALTER TABLE plaid_accounts     ADD COLUMN tenant_id UUID REFERENCES tenants(tenant_id);
ALTER TABLE transactions       ADD COLUMN tenant_id UUID REFERENCES tenants(tenant_id);
ALTER TABLE portfolio_holdings ADD COLUMN tenant_id UUID REFERENCES tenants(tenant_id);
ALTER TABLE debt_accounts      ADD COLUMN tenant_id UUID REFERENCES tenants(tenant_id);
ALTER TABLE sync_jobs          ADD COLUMN tenant_id UUID REFERENCES tenants(tenant_id);

ALTER TABLE plaid_items        ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE plaid_accounts     ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE transactions       ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE portfolio_holdings ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE debt_accounts      ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE sync_jobs          ALTER COLUMN tenant_id SET NOT NULL;

-- ---- indexes (RLS filter + tenant-wide queries) ----
CREATE INDEX idx_items_tenant      ON plaid_items(tenant_id);
CREATE INDEX idx_accounts_tenant   ON plaid_accounts(tenant_id);
CREATE INDEX idx_tx_tenant_date    ON transactions(tenant_id, date DESC);
CREATE INDEX idx_holdings_tenant   ON portfolio_holdings(tenant_id);
CREATE INDEX idx_debt_tenant       ON debt_accounts(tenant_id);
CREATE INDEX idx_syncjobs_tenant   ON sync_jobs(tenant_id);

-- ---- RLS: enable + force + tenant-scoped policy (USING + WITH CHECK) ----
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'plaid_items','plaid_accounts','transactions','portfolio_holdings','debt_accounts','sync_jobs'
  ] LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', t);
    EXECUTE format($f$
      CREATE POLICY tenant_isolation_%1$s ON %1$I
        USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
        WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
    $f$, t);
  END LOOP;
END$$;

-- ---- Webhook tenant resolver ----
-- Plaid webhooks arrive with NO tenant context, authenticated only by Plaid's
-- signature. This SECURITY DEFINER function performs the one legitimate
-- cross-tenant lookup (external plaid_item_id -> our ids) without granting the
-- app role RLS bypass. It returns only the mapping, nothing sensitive.
CREATE OR REPLACE FUNCTION resolve_plaid_item(p_plaid_item_id text)
RETURNS TABLE(item_id uuid, user_id uuid, tenant_id uuid)
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT item_id, user_id, tenant_id FROM plaid_items WHERE plaid_item_id = p_plaid_item_id
$$;

REVOKE ALL ON FUNCTION resolve_plaid_item(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION resolve_plaid_item(text) TO app_user;
