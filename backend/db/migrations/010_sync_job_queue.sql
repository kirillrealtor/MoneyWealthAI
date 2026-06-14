-- =====================================================================
-- 010_sync_job_queue — Make background Plaid sync DURABLE and FLEET-SAFE.
--
-- Before: webhooks/relinks spawned an in-process asyncio task (fire-and-forget).
-- Work was lost on any deploy/restart/crash, the concurrency limit was
-- per-instance (uncoordinated across the fleet), and it competed with request
-- handling for the web tier's tiny connection pool.
--
-- After: enqueue durably into sync_jobs (status='pending'); a worker fleet
-- claims jobs atomically with FOR UPDATE SKIP LOCKED (so N workers across N
-- instances pull DISJOINT jobs with no double-processing), runs them off the
-- request path, and a recovery sweep requeues jobs orphaned by a crash. The
-- sync_jobs table is the source of truth, so this can later be fronted by SQS
-- without changing the worker logic.
--
-- These functions are SECURITY DEFINER because the queue is necessarily
-- cross-tenant (one worker drains every tenant's jobs), and sync_jobs is
-- FORCE-RLS. They expose only job-control columns, never financial data —
-- the same trust model as resolve_plaid_item() in migration 004.
-- =====================================================================

-- Claim query support: find the oldest pending jobs fast.
CREATE INDEX IF NOT EXISTS idx_syncjobs_pending
  ON sync_jobs(started_at) WHERE status = 'pending';

-- ---- Enqueue (idempotent): don't pile up jobs for an item already queued ----
CREATE OR REPLACE FUNCTION enqueue_sync_job(p_item_id uuid, p_tenant_id uuid, p_user_id uuid)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE v_sync_id uuid;
BEGIN
  -- Coalesce duplicate triggers (multiple webhooks for the same item) into a
  -- single outstanding job, so a webhook storm can't flood the queue.
  INSERT INTO sync_jobs (item_id, tenant_id, user_id, status)
  SELECT p_item_id, p_tenant_id, p_user_id, 'pending'
  WHERE NOT EXISTS (
    SELECT 1 FROM sync_jobs
     WHERE item_id = p_item_id AND status IN ('pending', 'running')
  )
  RETURNING sync_id INTO v_sync_id;
  RETURN v_sync_id;  -- NULL if a job was already outstanding
END;
$$;

-- ---- Claim a batch atomically (FOR UPDATE SKIP LOCKED = fleet-safe queue) ----
CREATE OR REPLACE FUNCTION claim_sync_jobs(p_limit int)
RETURNS TABLE(sync_id uuid, item_id uuid, tenant_id uuid, user_id uuid)
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  UPDATE sync_jobs j
     SET status = 'running', started_at = NOW()
   WHERE j.sync_id IN (
     SELECT s.sync_id FROM sync_jobs s
      WHERE s.status = 'pending'
      ORDER BY s.started_at
      FOR UPDATE SKIP LOCKED
      LIMIT p_limit
   )
  RETURNING j.sync_id, j.item_id, j.tenant_id, j.user_id;
$$;

-- ---- Recover jobs orphaned by a crashed worker ----
-- A 'running' job whose worker died never reaches a terminal state. Past the
-- timeout, requeue it (up to p_max_retries) or mark it failed. Returns how many
-- rows it touched.
CREATE OR REPLACE FUNCTION recover_stale_sync_jobs(p_timeout_seconds int, p_max_retries int)
RETURNS int
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE v_count int;
BEGIN
  WITH stale AS (
    SELECT sync_id FROM sync_jobs
     WHERE status = 'running'
       AND started_at < NOW() - make_interval(secs => p_timeout_seconds)
     FOR UPDATE SKIP LOCKED
  )
  UPDATE sync_jobs j
     SET status = CASE WHEN j.retry_count >= p_max_retries THEN 'failed' ELSE 'pending' END,
         retry_count = j.retry_count + 1,
         error_message = CASE WHEN j.retry_count >= p_max_retries
                              THEN 'abandoned after max retries (worker crash?)' ELSE j.error_message END
    FROM stale
   WHERE j.sync_id = stale.sync_id;
  GET DIAGNOSTICS v_count = ROW_COUNT;
  RETURN v_count;
END;
$$;

REVOKE ALL ON FUNCTION enqueue_sync_job(uuid, uuid, uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION claim_sync_jobs(int) FROM PUBLIC;
REVOKE ALL ON FUNCTION recover_stale_sync_jobs(int, int) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION enqueue_sync_job(uuid, uuid, uuid) TO app_user;
GRANT EXECUTE ON FUNCTION claim_sync_jobs(int) TO app_user;
GRANT EXECUTE ON FUNCTION recover_stale_sync_jobs(int, int) TO app_user;
