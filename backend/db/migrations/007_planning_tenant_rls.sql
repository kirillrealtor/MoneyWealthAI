-- =====================================================================
-- 007_planning_tenant_rls — tenant_id + FORCE RLS on the planning tables
-- (budgets, goals, goal_milestones) for parity with the rest of the schema.
-- =====================================================================

ALTER TABLE budgets         ADD COLUMN tenant_id UUID REFERENCES tenants(tenant_id);
ALTER TABLE goals           ADD COLUMN tenant_id UUID REFERENCES tenants(tenant_id);
ALTER TABLE goal_milestones ADD COLUMN tenant_id UUID REFERENCES tenants(tenant_id);

-- Backfill from users (lift FORCE so the owner can read users during the copy).
ALTER TABLE users NO FORCE ROW LEVEL SECURITY;
UPDATE budgets b SET tenant_id = u.tenant_id FROM users u WHERE u.user_id = b.user_id;
UPDATE goals g   SET tenant_id = u.tenant_id FROM users u WHERE u.user_id = g.user_id;
ALTER TABLE users FORCE ROW LEVEL SECURITY;

UPDATE goal_milestones m SET tenant_id = g.tenant_id FROM goals g WHERE g.goal_id = m.goal_id;

-- Safety net: retail tenant for any orphans.
UPDATE budgets         SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL;
UPDATE goals           SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL;
UPDATE goal_milestones SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL;

ALTER TABLE budgets         ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE goals           ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE goal_milestones ALTER COLUMN tenant_id SET NOT NULL;

CREATE INDEX idx_budgets_tenant ON budgets(tenant_id);
CREATE INDEX idx_goals_tenant   ON goals(tenant_id);

DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['budgets','goals','goal_milestones'] LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', t);
    EXECUTE format($f$
      CREATE POLICY tenant_isolation_%1$s ON %1$I
        USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
        WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
    $f$, t);
  END LOOP;
END$$;
