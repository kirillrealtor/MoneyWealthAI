-- =====================================================================
-- 008_notifications_rls — SQLite compatible version.
-- =====================================================================

ALTER TABLE alerts                  ADD COLUMN tenant_id TEXT REFERENCES tenants(tenant_id);
ALTER TABLE notification_preferences ADD COLUMN tenant_id TEXT REFERENCES tenants(tenant_id);

UPDATE alerts SET tenant_id = (
  SELECT tenant_id FROM users WHERE users.user_id = alerts.user_id
);
UPDATE notification_preferences SET tenant_id = (
  SELECT tenant_id FROM users WHERE users.user_id = notification_preferences.user_id
);

UPDATE alerts                   SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL;
UPDATE notification_preferences SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL;

CREATE INDEX idx_alerts_tenant ON alerts(tenant_id);

CREATE TABLE notification_outbox (
  outbox_id   TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab', 1 + (abs(random()) % 4), 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
  user_id     TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  tenant_id   TEXT NOT NULL REFERENCES tenants(tenant_id),
  alert_id    TEXT REFERENCES alerts(alert_id) ON DELETE SET NULL,
  channel     TEXT NOT NULL,
  status      TEXT NOT NULL DEFAULT 'pending',
  dedupe_key  TEXT NOT NULL,
  attempts    INTEGER NOT NULL DEFAULT 0,
  error       TEXT,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  sent_at     DATETIME,
  UNIQUE (dedupe_key, channel)
);

CREATE INDEX idx_outbox_pending ON notification_outbox(status) WHERE status = 'pending';
CREATE INDEX idx_outbox_tenant ON notification_outbox(tenant_id);
