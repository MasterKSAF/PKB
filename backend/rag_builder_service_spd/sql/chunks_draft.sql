-- Черновик структуры nsi.chunks
-- Не утверждено
-- Требует согласования с Knowledge Base

CREATE TABLE nsi.chunks (
    id bigint generated always as identity,

    document_id bigint not null,
    document_version_id bigint not null,

    section_id bigint not null,

    clause text,
    page integer,

    bbox jsonb,

    chunk_index integer not null,
    chunk_type text not null,

    content text not null,

    metadata jsonb,

    embedding vector(1536)
);