-- =====================================================================
-- 006_ai_tenant_rls — SQLite compatible version.
-- =====================================================================

ALTER TABLE chat_sessions        ADD COLUMN tenant_id TEXT REFERENCES tenants(tenant_id);
ALTER TABLE chat_messages        ADD COLUMN tenant_id TEXT REFERENCES tenants(tenant_id);
ALTER TABLE financial_memory     ADD COLUMN tenant_id TEXT REFERENCES tenants(tenant_id);
ALTER TABLE ai_response_feedback ADD COLUMN tenant_id TEXT REFERENCES tenants(tenant_id);
ALTER TABLE token_usage          ADD COLUMN tenant_id TEXT REFERENCES tenants(tenant_id);

UPDATE chat_sessions SET tenant_id = (
  SELECT tenant_id FROM users WHERE users.user_id = chat_sessions.user_id
);
UPDATE token_usage SET tenant_id = (
  SELECT tenant_id FROM users WHERE users.user_id = token_usage.user_id
);
UPDATE ai_response_feedback SET tenant_id = (
  SELECT tenant_id FROM users WHERE users.user_id = ai_response_feedback.user_id
);

UPDATE chat_messages SET tenant_id = (
  SELECT tenant_id FROM chat_sessions WHERE chat_sessions.chat_id = chat_messages.chat_id
);
UPDATE financial_memory SET tenant_id = (
  SELECT tenant_id FROM chat_sessions WHERE chat_sessions.chat_id = financial_memory.chat_id
);

-- Safety net: retail tenant.
UPDATE chat_sessions        SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL;
UPDATE chat_messages        SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL;
UPDATE financial_memory     SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL;
UPDATE ai_response_feedback SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL;
UPDATE token_usage          SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL;

CREATE INDEX idx_chat_sessions_tenant ON chat_sessions(tenant_id);
CREATE INDEX idx_chat_messages_tenant ON chat_messages(tenant_id);
