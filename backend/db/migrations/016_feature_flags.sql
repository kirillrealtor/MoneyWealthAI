-- 016_feature_flags — platform feature flags managed from the admin console.
-- Global config (not tenant data), so no RLS — grants locked to app_user only.
CREATE TABLE IF NOT EXISTS feature_flags (
  key         VARCHAR(80) PRIMARY KEY,
  enabled     BOOLEAN NOT NULL DEFAULT false,
  description TEXT,
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

REVOKE ALL ON feature_flags FROM PUBLIC;
GRANT SELECT, INSERT, UPDATE ON feature_flags TO app_user;

INSERT INTO feature_flags (key, enabled, description) VALUES
  ('signups_open',       true,  'Allow new user signups'),
  ('advisor_streaming',  true,  'Stream advisor responses token-by-token'),
  ('plaid_investments',  true,  'Sync investment holdings for the Portfolio dashboard'),
  ('weekly_digest',      false, 'Send the Sunday weekly digest email'),
  ('maintenance_mode',   false, 'Park the app in a read-only maintenance state')
ON CONFLICT (key) DO NOTHING;
