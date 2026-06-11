-- =====================================================================
-- 003_rls_app_role — SQLite compatible version.
-- =====================================================================

ALTER TABLE user_sessions ADD COLUMN tenant_id TEXT REFERENCES tenants(tenant_id);
ALTER TABLE email_verification_tokens ADD COLUMN tenant_id TEXT REFERENCES tenants(tenant_id);

UPDATE user_sessions SET tenant_id = (
  SELECT tenant_id FROM users WHERE users.user_id = user_sessions.user_id
);

UPDATE email_verification_tokens SET tenant_id = (
  SELECT tenant_id FROM users WHERE users.user_id = email_verification_tokens.user_id
);
