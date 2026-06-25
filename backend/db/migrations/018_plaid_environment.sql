-- Add environment column to plaid_items to support dynamic Plaid environments (sandbox vs real/development/production)
ALTER TABLE plaid_items ADD COLUMN environment VARCHAR(50) NOT NULL DEFAULT 'sandbox';
