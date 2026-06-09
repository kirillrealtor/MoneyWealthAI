-- =====================================================================
-- 006_ai_tenant_rls — Bring the AI/chat tables to schema parity: tenant_id
-- + FORCE RLS, so conversation data has the same database-level isolation
-- backstop as users and Plaid data (not app-layer checks alone).
--
-- Backfill reads users with FORCE RLS temporarily lifted (migrations run as
-- the owner). Pre-launch there are only dev rows under the retail tenant.
-- =====================================================================

ALTER TABLE chat_sessions       ADD COLUMN tenant_id UUID REFERENCES tenants(tenant_id);
ALTER TABLE chat_messages       ADD COLUMN tenant_id UUID REFERENCES tenants(tenant_id);
ALTER TABLE financial_memory    ADD COLUMN tenant_id UUID REFERENCES tenants(tenant_id);
ALTER TABLE ai_response_feedback ADD COLUMN tenant_id UUID REFERENCES tenants(tenant_id);
ALTER TABLE token_usage         ADD COLUMN tenant_id UUID REFERENCES tenants(tenant_id);

-- Backfill from users (lift FORCE so the owner can read users during the copy).
ALTER TABLE users NO FORCE ROW LEVEL SECURITY;
UPDATE chat_sessions s        SET tenant_id = u.tenant_id FROM users u WHERE u.user_id = s.user_id;
UPDATE token_usage t          SET tenant_id = u.tenant_id FROM users u WHERE u.user_id = t.user_id;
UPDATE ai_response_feedback f SET tenant_id = u.tenant_id FROM users u WHERE u.user_id = f.user_id;
ALTER TABLE users FORCE ROW LEVEL SECURITY;

-- Child tables derive tenant from their chat session.
UPDATE chat_messages m    SET tenant_id = s.tenant_id FROM chat_sessions s WHERE s.chat_id = m.chat_id;
UPDATE financial_memory fm SET tenant_id = s.tenant_id FROM chat_sessions s WHERE s.chat_id = fm.chat_id;

-- Safety net for any orphaned rows: retail tenant.
UPDATE chat_sessions        SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL;
UPDATE chat_messages        SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL;
UPDATE financial_memory     SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL;
UPDATE ai_response_feedback SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL;
UPDATE token_usage          SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL;

ALTER TABLE chat_sessions        ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE chat_messages        ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE financial_memory     ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE ai_response_feedback ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE token_usage          ALTER COLUMN tenant_id SET NOT NULL;

CREATE INDEX idx_chat_sessions_tenant ON chat_sessions(tenant_id);
CREATE INDEX idx_chat_messages_tenant ON chat_messages(tenant_id);

DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'chat_sessions','chat_messages','financial_memory','ai_response_feedback','token_usage'
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
