-- =====================================================================
-- 009_user_scoped_rls — Defense-in-depth: add a per-USER isolation backstop
-- on top of the existing per-TENANT RLS.
--
-- Why: all retail users share one tenant, so tenant RLS alone does NOT
-- isolate users from each other at the database layer — that relies entirely
-- on every query carrying `WHERE user_id = $1`. A single forgotten predicate
-- is a cross-user data leak (IDOR/BOLA). This migration makes the database
-- enforce user scoping too, so the app-layer filter is a backstop, not the
-- only line of defense.
--
-- Design: a RESTRICTIVE policy keyed on a second GUC, `app.current_user_id`,
-- set transaction-locally by db.with_tenant(tenant_id, user_id). RESTRICTIVE
-- policies AND with the existing permissive tenant policy, so a row must match
-- BOTH tenant and (when a user is in context) user.
--
-- The policy NO-OPS when `app.current_user_id` is unset/empty. That keeps
-- legitimate system paths working unchanged — signup (user not created yet),
-- email verification, webhook tenant resolution, cross-user admin sweeps —
-- which call with_tenant() without a user. Adoption is therefore incremental
-- and safe: setting the user GUC only ever tightens access, never loosens it.
-- =====================================================================

DO $$
DECLARE t text;
BEGIN
  -- Tables with a direct user_id column that are read/written in the context
  -- of a single authenticated user. (Child tables like transactions,
  -- chat_messages, portfolio_holdings derive ownership through a parent and are
  -- covered transitively; adding per-row subquery policies there would cost
  -- more than it protects at scale.)
  FOREACH t IN ARRAY ARRAY[
    'budgets','goals','alerts','notification_preferences',
    'chat_sessions','token_usage','ai_response_feedback','plaid_items'
  ] LOOP
    -- Cast NULLIF(setting, '') — NOT the raw setting — so an unset/empty GUC
    -- becomes NULL (policy no-ops) instead of raising "invalid input syntax for
    -- type uuid". Postgres does not guarantee OR short-circuits before the cast,
    -- so guarding with a separate `IS NULL OR ...::uuid` clause is not enough.
    EXECUTE format($f$
      CREATE POLICY user_isolation_%1$s ON %1$I AS RESTRICTIVE
        USING (
          NULLIF(current_setting('app.current_user_id', true), '') IS NULL
          OR user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
        )
        WITH CHECK (
          NULLIF(current_setting('app.current_user_id', true), '') IS NULL
          OR user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
        )
    $f$, t);
  END LOOP;
END$$;
