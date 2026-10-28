-- Sonny ONE hosted storage prototype, schema v1.
-- NOT a deployment migration. Requires independent security review.
-- PostgreSQL database must be encrypted at rest by its managed provider.
-- Application connections must not use the table-owner role.
BEGIN;

CREATE TABLE IF NOT EXISTS sonny_accounts (
    id uuid PRIMARY KEY,
    username text NOT NULL UNIQUE,
    password_hash text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sonny_sessions (
    id_hash text PRIMARY KEY,
    account_id uuid NOT NULL REFERENCES sonny_accounts(id) ON DELETE CASCADE,
    expires_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS sonny_sessions_account ON sonny_sessions(account_id);

CREATE TABLE IF NOT EXISTS sonny_workspaces (
    account_id uuid PRIMARY KEY REFERENCES sonny_accounts(id) ON DELETE CASCADE,
    goal text NOT NULL,
    version bigint NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS sonny_memories (
    id uuid PRIMARY KEY,
    account_id uuid NOT NULL REFERENCES sonny_accounts(id) ON DELETE CASCADE,
    statement text NOT NULL CHECK (length(statement) BETWEEN 1 AND 500),
    source text NOT NULL,
    revision integer NOT NULL DEFAULT 1 CHECK (revision > 0),
    approved_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS sonny_memories_account ON sonny_memories(account_id);

CREATE TABLE IF NOT EXISTS sonny_messages (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    account_id uuid NOT NULL REFERENCES sonny_accounts(id) ON DELETE CASCADE,
    role text NOT NULL CHECK (role IN ('user','assistant')),
    body text NOT NULL CHECK (length(body) BETWEEN 1 AND 16000),
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS sonny_messages_account_id ON sonny_messages(account_id, id);

CREATE TABLE IF NOT EXISTS sonny_turns (
    account_id uuid NOT NULL REFERENCES sonny_accounts(id) ON DELETE CASCADE,
    request_id uuid NOT NULL,
    request_body text NOT NULL,
    response_json jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (account_id, request_id)
);

-- A transaction-scoped account identity is mandatory. Missing/invalid identity
-- causes NULL and denies access. The API must SET LOCAL sonny.account_id only
-- after validating a session, never from an untrusted request field.
CREATE OR REPLACE FUNCTION sonny_current_account() RETURNS uuid
LANGUAGE plpgsql STABLE AS $$
BEGIN
    RETURN NULLIF(current_setting('sonny.account_id', true), '')::uuid;
EXCEPTION WHEN invalid_text_representation THEN
    RETURN NULL;
END;
$$;

ALTER TABLE sonny_workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE sonny_memories ENABLE ROW LEVEL SECURITY;
ALTER TABLE sonny_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE sonny_turns ENABLE ROW LEVEL SECURITY;
ALTER TABLE sonny_workspaces FORCE ROW LEVEL SECURITY;
ALTER TABLE sonny_memories FORCE ROW LEVEL SECURITY;
ALTER TABLE sonny_messages FORCE ROW LEVEL SECURITY;
ALTER TABLE sonny_turns FORCE ROW LEVEL SECURITY;

CREATE POLICY sonny_workspace_isolation ON sonny_workspaces
    USING (account_id = sonny_current_account())
    WITH CHECK (account_id = sonny_current_account());
CREATE POLICY sonny_memory_isolation ON sonny_memories
    USING (account_id = sonny_current_account())
    WITH CHECK (account_id = sonny_current_account());
CREATE POLICY sonny_message_isolation ON sonny_messages
    USING (account_id = sonny_current_account())
    WITH CHECK (account_id = sonny_current_account());
CREATE POLICY sonny_turn_isolation ON sonny_turns
    USING (account_id = sonny_current_account())
    WITH CHECK (account_id = sonny_current_account());

COMMIT;
