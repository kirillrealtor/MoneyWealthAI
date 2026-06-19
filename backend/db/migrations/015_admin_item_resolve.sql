-- 015_admin_item_resolve — resolve an internal plaid item_id to its owner so the
-- admin "re-sync" action can enqueue a job with the right tenant/user context
-- (audited SECURITY DEFINER; no RLS bypass for the app role).
CREATE OR REPLACE FUNCTION admin_resolve_item(p_item_id uuid)
RETURNS TABLE(user_id uuid, tenant_id uuid)
LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
  SELECT user_id, tenant_id FROM plaid_items WHERE item_id = p_item_id
$$;

REVOKE ALL ON FUNCTION admin_resolve_item(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION admin_resolve_item(uuid) TO app_user;
