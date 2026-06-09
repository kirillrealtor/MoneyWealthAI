-- =====================================================================
-- 002_email_verification — single-use tokens for email verification and
-- (future) password reset. Token value is never stored; only its SHA-256.
-- =====================================================================

CREATE TABLE email_verification_tokens (
  token_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  token_hash  VARCHAR NOT NULL,                 -- SHA-256 of the emailed token
  purpose     VARCHAR(30) NOT NULL DEFAULT 'verify_email', -- verify_email | reset_password
  expires_at  TIMESTAMPTZ NOT NULL,
  consumed_at TIMESTAMPTZ,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_evt_user ON email_verification_tokens(user_id, purpose);
CREATE INDEX idx_evt_token ON email_verification_tokens(token_hash);
