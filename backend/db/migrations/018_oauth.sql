-- =====================================================================
-- 018_oauth — Social login (Google "Continue with Google").
--
-- OAuth users authenticate via the provider and have NO local password;
-- the provider already verified their email, so they are created verified.
--   1. password_hash becomes optional (OAuth accounts have none).
--   2. auth_provider records how the account signs in ('password' | 'google').
--   3. oauth_sub stores the provider's stable subject id (one identity = one
--      account per tenant).
-- Additive + backfilled, so it's safe on a live table.
-- =====================================================================

ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;

ALTER TABLE users ADD COLUMN auth_provider VARCHAR(20) NOT NULL DEFAULT 'password';
ALTER TABLE users ADD COLUMN oauth_sub VARCHAR(255);

-- A given provider identity maps to exactly one account within a tenant.
CREATE UNIQUE INDEX idx_users_oauth_sub
  ON users (tenant_id, auth_provider, oauth_sub)
  WHERE oauth_sub IS NOT NULL;
