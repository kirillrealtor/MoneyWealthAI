-- =====================================================================
-- 011_sync_job_dedup — Make sync-job enqueue idempotency a HARD guarantee.
--
-- enqueue_sync_job() used INSERT ... WHERE NOT EXISTS to coalesce duplicate
-- triggers (a webhook storm for one item). Under READ COMMITTED that check has
-- a race: two concurrent enqueues can both see "no outstanding job" and both
-- insert. The redis per-item lock still prevents a concurrent *sync*, so no
-- data is corrupted — but a duplicate 'pending' row is wasted work, and the
-- function advertises itself as idempotent. Enforce it at the database with a
-- partial unique index (only one pending/running job per item) and have the
-- function swallow the resulting conflict.
-- =====================================================================

CREATE UNIQUE INDEX IF NOT EXISTS uq_syncjobs_active_item
  ON sync_jobs(item_id) WHERE status IN ('pending', 'running');

CREATE OR REPLACE FUNCTION enqueue_sync_job(p_item_id uuid, p_tenant_id uuid, p_user_id uuid)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE v_sync_id uuid;
BEGIN
  -- Fast path: skip the insert when a job is already outstanding.
  INSERT INTO sync_jobs (item_id, tenant_id, user_id, status)
  SELECT p_item_id, p_tenant_id, p_user_id, 'pending'
  WHERE NOT EXISTS (
    SELECT 1 FROM sync_jobs
     WHERE item_id = p_item_id AND status IN ('pending', 'running')
  )
  RETURNING sync_id INTO v_sync_id;
  RETURN v_sync_id;  -- NULL if a job was already outstanding
EXCEPTION
  -- Lost the race against a concurrent enqueue: the partial unique index
  -- rejected the second row. That's the desired coalescing — report "already
  -- queued" (NULL) rather than erroring the webhook/exchange request.
  WHEN unique_violation THEN
    RETURN NULL;
END;
$$;
