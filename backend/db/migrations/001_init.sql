-- =====================================================================
-- 001_init — Core schema (SQLite compatible version).
-- =====================================================================

-- ---------------- CORE / TENANCY ----------------
CREATE TABLE tenants (
  tenant_id      TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab', 1 + (abs(random()) % 4), 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
  name           TEXT NOT NULL,
  slug           TEXT UNIQUE NOT NULL,
  plan           TEXT NOT NULL DEFAULT 'retail',
  persona_config TEXT DEFAULT '{}',
  theme_config   TEXT DEFAULT '{}',
  api_key_hash   TEXT NOT NULL,
  webhook_secret TEXT,
  is_active      INTEGER NOT NULL DEFAULT 1,
  created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO tenants (tenant_id, name, slug, plan, api_key_hash)
VALUES ('00000000-0000-0000-0000-000000000001', 'Retail (Direct)', 'retail', 'retail', 'n/a');

CREATE TABLE users (
  user_id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab', 1 + (abs(random()) % 4), 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
  tenant_id        TEXT NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
  email            TEXT NOT NULL,
  password_hash    TEXT NOT NULL,
  full_name        TEXT,
  phone            TEXT,
  advisor_persona  TEXT NOT NULL DEFAULT 'balanced',
  tier             TEXT NOT NULL DEFAULT 'free',
  locale           TEXT NOT NULL DEFAULT 'en-US',
  display_currency TEXT NOT NULL DEFAULT 'USD',
  onboarding_step  INTEGER NOT NULL DEFAULT 0,
  is_verified      INTEGER NOT NULL DEFAULT 0,
  last_login_at    DATETIME,
  created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (tenant_id, email)
);
CREATE INDEX idx_users_tenant ON users(tenant_id);

CREATE TRIGGER trg_users_updated AFTER UPDATE ON users FOR EACH ROW
BEGIN
  UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE user_id = old.user_id;
END;

CREATE TABLE user_sessions (
  session_id   TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab', 1 + (abs(random()) % 4), 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
  user_id      TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  token_hash   TEXT NOT NULL,
  ip_address   TEXT,
  user_agent   TEXT,
  expires_at   DATETIME NOT NULL,
  revoked_at   DATETIME,
  created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_sessions_token ON user_sessions(token_hash);

-- ---------------- PLAID ----------------
CREATE TABLE plaid_items (
  item_id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab', 1 + (abs(random()) % 4), 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
  user_id          TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  plaid_item_id    TEXT UNIQUE,
  access_token_enc BLOB NOT NULL,
  item_status      TEXT NOT NULL DEFAULT 'good',
  institution_id   TEXT,
  institution_name TEXT,
  cursor           TEXT,
  last_sync_at     DATETIME,
  created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_items_user ON plaid_items(user_id);

CREATE TABLE plaid_accounts (
  account_id        TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab', 1 + (abs(random()) % 4), 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
  item_id           TEXT NOT NULL REFERENCES plaid_items(item_id) ON DELETE CASCADE,
  plaid_account_id  TEXT NOT NULL UNIQUE,
  name              TEXT,
  official_name     TEXT,
  type              TEXT,
  subtype           TEXT,
  balance_current   NUMERIC,
  balance_available NUMERIC,
  balance_limit     NUMERIC,
  currency_code     TEXT NOT NULL DEFAULT 'USD',
  synced_at         DATETIME,
  created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_accounts_item ON plaid_accounts(item_id);

CREATE TABLE transactions (
  transaction_id       TEXT NOT NULL DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab', 1 + (abs(random()) % 4), 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
  account_id           TEXT NOT NULL REFERENCES plaid_accounts(account_id) ON DELETE CASCADE,
  plaid_transaction_id TEXT NOT NULL,
  amount               NUMERIC NOT NULL,
  iso_currency_code    TEXT NOT NULL DEFAULT 'USD',
  date                 TEXT NOT NULL,
  authorized_date      TEXT,
  merchant_name        TEXT,
  plaid_category       TEXT,
  category             TEXT,
  subcategory          TEXT,
  is_recurring         INTEGER NOT NULL DEFAULT 0,
  is_duplicate         INTEGER NOT NULL DEFAULT 0,
  pending              INTEGER NOT NULL DEFAULT 0,
  created_at           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (transaction_id, date),
  UNIQUE (plaid_transaction_id, date)
);

CREATE INDEX idx_tx_account_date ON transactions(account_id, date DESC);
CREATE INDEX idx_tx_category_date ON transactions(category, date DESC);

-- ---------------- PLANNING ----------------
CREATE TABLE budgets (
  budget_id     TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab', 1 + (abs(random()) % 4), 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
  user_id       TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  category      TEXT NOT NULL,
  monthly_limit NUMERIC NOT NULL CHECK (monthly_limit > 0),
  alert_at_pct  INTEGER NOT NULL DEFAULT 80,
  is_active     INTEGER NOT NULL DEFAULT 1,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (user_id, category)
);

CREATE TABLE goals (
  goal_id        TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab', 1 + (abs(random()) % 4), 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
  user_id        TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  title          TEXT NOT NULL,
  description    TEXT,
  target_amount  NUMERIC NOT NULL CHECK (target_amount > 0),
  current_amount NUMERIC NOT NULL DEFAULT 0,
  target_date    TEXT NOT NULL,
  monthly_target NUMERIC,
  priority       INTEGER NOT NULL DEFAULT 1,
  status         TEXT NOT NULL DEFAULT 'active',
  created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_goals_user ON goals(user_id, status);

CREATE TRIGGER trg_goals_updated AFTER UPDATE ON goals FOR EACH ROW
BEGIN
  UPDATE goals SET updated_at = CURRENT_TIMESTAMP WHERE goal_id = old.goal_id;
END;

CREATE TABLE goal_milestones (
  milestone_id  TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab', 1 + (abs(random()) % 4), 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
  goal_id       TEXT NOT NULL REFERENCES goals(goal_id) ON DELETE CASCADE,
  milestone_pct INTEGER NOT NULL,
  achieved_at   DATETIME,
  notified      INTEGER NOT NULL DEFAULT 0
);

-- ---------------- PORTFOLIO / DEBT ----------------
CREATE TABLE portfolio_holdings (
  holding_id        TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab', 1 + (abs(random()) % 4), 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
  account_id        TEXT NOT NULL REFERENCES plaid_accounts(account_id) ON DELETE CASCADE,
  plaid_security_id TEXT,
  ticker            TEXT,
  name              TEXT,
  quantity          NUMERIC,
  cost_basis        NUMERIC,
  institution_price NUMERIC,
  institution_value NUMERIC,
  asset_class       TEXT,
  sector            TEXT,
  synced_at         DATETIME,
  created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_holdings_account ON portfolio_holdings(account_id);

CREATE TABLE debt_accounts (
  debt_id         TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab', 1 + (abs(random()) % 4), 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
  account_id      TEXT NOT NULL REFERENCES plaid_accounts(account_id) ON DELETE CASCADE,
  balance         NUMERIC,
  apr             NUMERIC,
  minimum_payment NUMERIC,
  last_payment_at TEXT,
  debt_type       TEXT,
  synced_at       DATETIME
);

-- ---------------- AI CONVERSATION + QUALITY ----------------
CREATE TABLE chat_sessions (
  chat_id    TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab', 1 + (abs(random()) % 4), 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
  user_id    TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  module     TEXT,
  started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  ended_at   DATETIME
);
CREATE INDEX idx_chat_user ON chat_sessions(user_id, started_at DESC);

CREATE TABLE chat_messages (
  message_id     TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab', 1 + (abs(random()) % 4), 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
  chat_id        TEXT NOT NULL REFERENCES chat_sessions(chat_id) ON DELETE CASCADE,
  role           TEXT NOT NULL,
  content        TEXT NOT NULL,
  tool_name      TEXT,
  tool_input     TEXT,
  tool_result    TEXT,
  provider       TEXT,
  prompt_version TEXT,
  tokens_used    INTEGER,
  created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_messages_chat ON chat_messages(chat_id, created_at);

CREATE TABLE financial_memory (
  chat_id          TEXT PRIMARY KEY REFERENCES chat_sessions(chat_id) ON DELETE CASCADE,
  summary          TEXT NOT NULL,
  turns_compressed INTEGER NOT NULL DEFAULT 0,
  updated_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ai_response_feedback (
  feedback_id    TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab', 1 + (abs(random()) % 4), 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
  message_id     TEXT NOT NULL REFERENCES chat_messages(message_id) ON DELETE CASCADE,
  user_id        TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  rating         INTEGER NOT NULL CHECK (rating IN (1, -1)),
  issue_type     TEXT,
  free_text      TEXT,
  prompt_version TEXT,
  created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_feedback_created ON ai_response_feedback(created_at DESC);

CREATE TABLE token_usage (
  user_id  TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  date     TEXT NOT NULL,
  tokens   INTEGER NOT NULL DEFAULT 0,
  provider TEXT,
  PRIMARY KEY (user_id, date)
);

-- ---------------- DATA PIPELINE / OPS ----------------
CREATE TABLE sync_jobs (
  sync_id             TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab', 1 + (abs(random()) % 4), 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
  user_id             TEXT REFERENCES users(user_id) ON DELETE CASCADE,
  item_id             TEXT NOT NULL REFERENCES plaid_items(item_id) ON DELETE CASCADE,
  status              TEXT NOT NULL DEFAULT 'pending',
  cursor              TEXT,
  transactions_synced INTEGER NOT NULL DEFAULT 0,
  retry_count         INTEGER NOT NULL DEFAULT 0,
  error_message       TEXT,
  started_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at        DATETIME
);
CREATE INDEX idx_syncjobs_item_status ON sync_jobs(item_id, status);

CREATE TABLE alerts (
  alert_id   TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab', 1 + (abs(random()) % 4), 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
  user_id    TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  type       TEXT NOT NULL,
  title      TEXT,
  body       TEXT,
  severity   TEXT NOT NULL DEFAULT 'info',
  is_read    INTEGER NOT NULL DEFAULT 0,
  sent_via   TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_alerts_user ON alerts(user_id, created_at DESC);

CREATE TABLE notification_preferences (
  user_id           TEXT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
  push_enabled      INTEGER NOT NULL DEFAULT 1,
  email_enabled     INTEGER NOT NULL DEFAULT 1,
  sms_opt_in        INTEGER NOT NULL DEFAULT 0,
  budget_alerts     INTEGER NOT NULL DEFAULT 1,
  goal_alerts       INTEGER NOT NULL DEFAULT 1,
  bank_error_alerts INTEGER NOT NULL DEFAULT 1,
  unusual_tx_alerts INTEGER NOT NULL DEFAULT 1,
  weekly_digest     INTEGER NOT NULL DEFAULT 1,
  monthly_report    INTEGER NOT NULL DEFAULT 1,
  marketing_emails  INTEGER NOT NULL DEFAULT 0,
  quiet_hours_start TEXT NOT NULL DEFAULT '22:00',
  quiet_hours_end   TEXT NOT NULL DEFAULT '08:00',
  timezone          TEXT NOT NULL DEFAULT 'America/New_York',
  updated_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_logs (
  log_id      TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab', 1 + (abs(random()) % 4), 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
  user_id     TEXT REFERENCES users(user_id),
  tenant_id   TEXT REFERENCES tenants(tenant_id),
  action      TEXT NOT NULL,
  resource    TEXT,
  resource_id TEXT,
  ip_address  TEXT,
  metadata    TEXT,
  timestamp   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_audit_user_time ON audit_logs(user_id, timestamp DESC);
CREATE INDEX idx_audit_tenant_time ON audit_logs(tenant_id, timestamp DESC);
