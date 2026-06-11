-- =====================================================================
-- 007_planning_tenant_rls — SQLite compatible version.
-- =====================================================================

ALTER TABLE budgets         ADD COLUMN tenant_id TEXT REFERENCES tenants(tenant_id);
ALTER TABLE goals           ADD COLUMN tenant_id TEXT REFERENCES tenants(tenant_id);
ALTER TABLE goal_milestones ADD COLUMN tenant_id TEXT REFERENCES tenants(tenant_id);

UPDATE budgets SET tenant_id = (
  SELECT tenant_id FROM users WHERE users.user_id = budgets.user_id
);
UPDATE goals SET tenant_id = (
  SELECT tenant_id FROM users WHERE users.user_id = goals.user_id
);
UPDATE goal_milestones SET tenant_id = (
  SELECT tenant_id FROM goals WHERE goals.goal_id = goal_milestones.goal_id
);

-- Safety net: retail tenant.
UPDATE budgets         SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL;
UPDATE goals           SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL;
UPDATE goal_milestones SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL;

CREATE INDEX idx_budgets_tenant ON budgets(tenant_id);
CREATE INDEX idx_goals_tenant   ON goals(tenant_id);
