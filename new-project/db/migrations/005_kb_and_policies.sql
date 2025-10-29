-- Migration: 005_kb_and_policies
-- Knowledge base documents and policy definitions

BEGIN;

CREATE TABLE kb_docs (
    id VARCHAR(36) PRIMARY KEY,  -- UUID v4
    title VARCHAR(255) NOT NULL,
    anchor VARCHAR(100) NOT NULL,  -- Section anchor for deep linking
    content_text TEXT NOT NULL,    -- Markdown or plain text content
    -- Indexes
    CONSTRAINT kb_docs_unique_anchor UNIQUE (anchor)
);

CREATE INDEX idx_kb_docs_title ON kb_docs(title);
CREATE INDEX idx_kb_docs_anchor ON kb_docs(anchor);
-- Full text search index for content
CREATE INDEX idx_kb_docs_content_text_search ON kb_docs USING GIN (to_tsvector('english', content_text));

CREATE TABLE policies (
    id VARCHAR(36) PRIMARY KEY,  -- UUID v4
    code VARCHAR(100) NOT NULL,  -- Unique policy code
    title VARCHAR(255) NOT NULL,
    content_text TEXT NOT NULL,  -- Policy rules/content
    -- Constraints
    CONSTRAINT policies_unique_code UNIQUE (code)
);

CREATE INDEX idx_policies_code ON policies(code);
-- Full text search for policy content
CREATE INDEX idx_policies_content_text_search ON policies USING GIN (to_tsvector('english', content_text));

COMMIT;
