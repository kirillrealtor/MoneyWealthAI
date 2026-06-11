-- =====================================================================
-- 002_email_verification — SQLite compatible version.
-- =====================================================================

CREATE TABLE email_verification_tokens (
  token_id    TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab', 1 + (abs(random()) % 4), 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
  user_id     TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  token_hash  TEXT NOT NULL,
  purpose     TEXT NOT NULL DEFAULT 'verify_email',
  expires_at  DATETIME NOT NULL,
  consumed_at DATETIME,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_evt_user ON email_verification_tokens(user_id, purpose);
CREATE INDEX idx_evt_token ON email_verification_tokens(token_hash);
