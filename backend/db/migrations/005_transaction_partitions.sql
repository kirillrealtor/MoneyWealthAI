-- =====================================================================
-- 005_transaction_partitions — Make partitioning actually work.
--
-- Problem fixed: only 3 months of partitions existed, so Plaid's 24-month
-- backfill landed almost entirely in transactions_default — defeating the
-- partitioning. This pre-creates monthly partitions across the realistic
-- range and adds a function the monthly cron calls to stay ahead.
-- =====================================================================

-- Pre-create monthly partitions: 2024-01 .. 2027-12 (covers 24mo history +
-- forward runway). CREATE ... IF NOT EXISTS skips the few that 001 made.
DO $$
DECLARE d date := date '2024-01-01';
BEGIN
  WHILE d < date '2028-01-01' LOOP
    EXECUTE format(
      'CREATE TABLE IF NOT EXISTS transactions_%s PARTITION OF transactions FOR VALUES FROM (%L) TO (%L)',
      to_char(d, 'YYYY_MM'), d, (d + interval '1 month')::date
    );
    d := (d + interval '1 month')::date;
  END LOOP;
END$$;

-- Idempotent helper for the scheduled job (EventBridge/cron) to create next
-- month's partition ahead of time. Runs as owner (DDL); app may call it.
CREATE OR REPLACE FUNCTION ensure_transactions_partition(p_month date)
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE start_d date := date_trunc('month', p_month);
BEGIN
  EXECUTE format(
    'CREATE TABLE IF NOT EXISTS transactions_%s PARTITION OF transactions FOR VALUES FROM (%L) TO (%L)',
    to_char(start_d, 'YYYY_MM'), start_d, (start_d + interval '1 month')::date
  );
END$$;

GRANT EXECUTE ON FUNCTION ensure_transactions_partition(date) TO app_user;
