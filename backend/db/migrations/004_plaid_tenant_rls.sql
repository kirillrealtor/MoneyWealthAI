-- =====================================================================
-- 004_plaid_tenant_rls — SQLite compatible version.
-- =====================================================================

-- plaid_item_id is already defined in 001_init.sql due to SQLite alter table UNIQUE limitation.
-- ALTER TABLE plaid_items ADD COLUMN plaid_item_id TEXT UNIQUE;

ALTER TABLE plaid_items        ADD COLUMN tenant_id TEXT REFERENCES tenants(tenant_id);
ALTER TABLE plaid_accounts     ADD COLUMN tenant_id TEXT REFERENCES tenants(tenant_id);
ALTER TABLE transactions       ADD COLUMN tenant_id TEXT REFERENCES tenants(tenant_id);
ALTER TABLE portfolio_holdings ADD COLUMN tenant_id TEXT REFERENCES tenants(tenant_id);
ALTER TABLE debt_accounts      ADD COLUMN tenant_id TEXT REFERENCES tenants(tenant_id);
ALTER TABLE sync_jobs          ADD COLUMN tenant_id TEXT REFERENCES tenants(tenant_id);

CREATE INDEX idx_items_tenant      ON plaid_items(tenant_id);
CREATE INDEX idx_accounts_tenant   ON plaid_accounts(tenant_id);
CREATE INDEX idx_tx_tenant_date    ON transactions(tenant_id, date DESC);
CREATE INDEX idx_holdings_tenant   ON portfolio_holdings(tenant_id);
CREATE INDEX idx_debt_tenant       ON debt_accounts(tenant_id);
CREATE INDEX idx_syncjobs_tenant   ON sync_jobs(tenant_id);
