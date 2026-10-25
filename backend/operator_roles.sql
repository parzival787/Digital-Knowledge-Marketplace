-- Run once as a database administrator after application schema initialization.
-- Template for the public schema; review schema name before applying elsewhere.
-- No passwords, logins or production grants are applied by the application.
BEGIN;
CREATE ROLE dkm_recovery_operator NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
GRANT USAGE ON SCHEMA public TO dkm_recovery_operator;
GRANT SELECT ON public.payment_orders TO dkm_recovery_operator;
GRANT UPDATE (recovery_status, error, settlement_attempts, settlement_started_at,
    settlement_last_attempt_at, refund_id, updated_at)
    ON public.payment_orders TO dkm_recovery_operator;
GRANT INSERT (order_id, action, reason) ON public.payment_recovery_events TO dkm_recovery_operator;
GRANT SELECT ON public.payment_recovery_events TO dkm_recovery_operator;
GRANT USAGE ON SEQUENCE public.payment_recovery_events_id_seq TO dkm_recovery_operator;
COMMIT;

-- Administrator then creates ONE personal LOGIN per real operator (no shared user),
-- provisions its password/certificate out of band, grants database CONNECT and
-- grants membership in dkm_recovery_operator. Do not grant this group to the web
-- runtime role. SESSION_USER records the personal authenticated database login,
-- even if SET ROLE is used. Members cannot update/delete audit rows or set actor.
