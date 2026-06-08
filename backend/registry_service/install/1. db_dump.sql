--
-- PostgreSQL database dump
--

\restrict Mj5CxO7JO03xn5ldvSUrcF5NoB6WH0re5gSdajewHXscWXdAxREVrIB9WEhPMkh

-- Dumped from database version 16.14
-- Dumped by pg_dump version 17.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: registry; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA registry;


ALTER SCHEMA registry OWNER TO postgres;

--
-- Name: SCHEMA registry; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA registry IS 'Registry of documents with metadata, sections, references, and processing history';


--
-- Name: ltree; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS ltree WITH SCHEMA public;


--
-- Name: EXTENSION ltree; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION ltree IS 'data type for hierarchical tree-like structures';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: classifiers; Type: TABLE; Schema: registry; Owner: postgres
--

CREATE TABLE registry.classifiers (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    classifier_system character varying(50) NOT NULL,
    code text NOT NULL,
    full_name text NOT NULL,
    description text,
    status character varying(50) DEFAULT 'active'::character varying,
    parent_code text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


ALTER TABLE registry.classifiers OWNER TO postgres;

--
-- Name: TABLE classifiers; Type: COMMENT; Schema: registry; Owner: postgres
--

COMMENT ON TABLE registry.classifiers IS 'Classifier entries (system, code, names, status) used by the registry service.';


--
-- Name: document_history; Type: TABLE; Schema: registry; Owner: postgres
--

CREATE TABLE registry.document_history (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    document_id uuid NOT NULL,
    event_type text,
    old_status character varying(50),
    new_status character varying(50),
    comment text,
    changed_by text,
    document_snapshot jsonb,
    event_at timestamp with time zone DEFAULT now()
);


ALTER TABLE registry.document_history OWNER TO postgres;

--
-- Name: TABLE document_history; Type: COMMENT; Schema: registry; Owner: postgres
--

COMMENT ON TABLE registry.document_history IS 'Audit log of document processing events';


--
-- Name: COLUMN document_history.document_snapshot; Type: COMMENT; Schema: registry; Owner: postgres
--

COMMENT ON COLUMN registry.document_history.document_snapshot IS 'Enriched JSON snapshot at event time';


--
-- Name: document_references; Type: TABLE; Schema: registry; Owner: postgres
--

CREATE TABLE registry.document_references (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    source_document_id uuid NOT NULL,
    target_doc_code text NOT NULL,
    reference_type character varying(50),
    context text,
    current_status character varying(50),
    replaced_by text,
    replacement_date date,
    is_resolved boolean DEFAULT false,
    resolved_document_id uuid,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE registry.document_references OWNER TO postgres;

--
-- Name: TABLE document_references; Type: COMMENT; Schema: registry; Owner: postgres
--

COMMENT ON TABLE registry.document_references IS 'Cross-references between documents';


--
-- Name: COLUMN document_references.current_status; Type: COMMENT; Schema: registry; Owner: postgres
--

COMMENT ON COLUMN registry.document_references.current_status IS 'Status of target document: active, superseded';


--
-- Name: document_sections; Type: TABLE; Schema: registry; Owner: postgres
--

CREATE TABLE registry.document_sections (
    id bigint NOT NULL,
    document_id uuid NOT NULL,
    parent_id bigint,
    clause text,
    title text,
    level integer,
    path public.ltree,
    page integer,
    bbox jsonb,
    type character varying(50),
    content jsonb,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT document_sections_type_check CHECK (((type)::text = ANY ((ARRAY['text'::character varying, 'textBlock'::character varying, 'headerFooter'::character varying, 'table'::character varying, 'list'::character varying, 'image'::character varying, 'formula'::character varying])::text[])))
);


ALTER TABLE registry.document_sections OWNER TO postgres;

--
-- Name: TABLE document_sections; Type: COMMENT; Schema: registry; Owner: postgres
--

COMMENT ON TABLE registry.document_sections IS 'Hierarchical sections of documents with content metadata';


--
-- Name: COLUMN document_sections.path; Type: COMMENT; Schema: registry; Owner: postgres
--

COMMENT ON COLUMN registry.document_sections.path IS 'LTree path for hierarchical queries';


--
-- Name: COLUMN document_sections.content; Type: COMMENT; Schema: registry; Owner: postgres
--

COMMENT ON COLUMN registry.document_sections.content IS 'JSONB content: {text, amendments} for sections, {caption, columns, rows} for tables, etc.';


--
-- Name: document_sections_id_seq; Type: SEQUENCE; Schema: registry; Owner: postgres
--

CREATE SEQUENCE registry.document_sections_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE registry.document_sections_id_seq OWNER TO postgres;

--
-- Name: document_sections_id_seq; Type: SEQUENCE OWNED BY; Schema: registry; Owner: postgres
--

ALTER SEQUENCE registry.document_sections_id_seq OWNED BY registry.document_sections.id;


--
-- Name: document_versions; Type: TABLE; Schema: registry; Owner: postgres
--

CREATE TABLE registry.document_versions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    document_id uuid NOT NULL,
    version_number integer,
    file_hash_sha256 text,
    file_size_bytes bigint,
    format_code character varying(50),
    format_label text,
    file_key text,
    uploaded_by text,
    uploaded_at timestamp with time zone DEFAULT now()
);


ALTER TABLE registry.document_versions OWNER TO postgres;

--
-- Name: documents; Type: TABLE; Schema: registry; Owner: postgres
--

CREATE TABLE registry.documents (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    doc_code text NOT NULL,
    title text NOT NULL,
    normalized_title text,
    source_type character varying(50),
    "group" character varying(50),
    mks_oks_code text,
    okstu_code text,
    udc text,
    era character varying(50),
    validity_status character varying(50),
    jurisdiction character varying(50),
    issuing_body text,
    adoption_date date,
    effective_from date,
    replaces text,
    status_note text,
    file_hash_sha256 text,
    title_hash_sha256 text,
    file_size_bytes bigint,
    processing_status character varying(50),
    chunk_count integer DEFAULT 0,
    successor_doc_id uuid,
    predecessor_doc_id uuid,
    created_by text,
    updated_by text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    status character varying(30) DEFAULT 'draft'::character varying NOT NULL
);


ALTER TABLE registry.documents OWNER TO postgres;

--
-- Name: TABLE documents; Type: COMMENT; Schema: registry; Owner: postgres
--

COMMENT ON TABLE registry.documents IS 'Main registry of all documents';


--
-- Name: COLUMN documents.file_hash_sha256; Type: COMMENT; Schema: registry; Owner: postgres
--

COMMENT ON COLUMN registry.documents.file_hash_sha256 IS 'Hash of binary file for duplicate detection';


--
-- Name: COLUMN documents.title_hash_sha256; Type: COMMENT; Schema: registry; Owner: postgres
--

COMMENT ON COLUMN registry.documents.title_hash_sha256 IS 'Hash of doc_code + title + era for duplicate detection';


--
-- Name: COLUMN documents.processing_status; Type: COMMENT; Schema: registry; Owner: postgres
--

COMMENT ON COLUMN registry.documents.processing_status IS 'FSM status: uploaded, previewing, awaiting_decision, parsing, validation, ready_for_promotion, review_required, approved, registry, pending_index, indexing, indexed, duplicate, new_version, archived, failed';


--
-- Name: rs_enums; Type: TABLE; Schema: registry; Owner: pkb_user
--

CREATE TABLE registry.rs_enums (
    id bigint NOT NULL,
    enum_key character varying(128) NOT NULL,
    enum_value character varying(256) NOT NULL,
    description text,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE registry.rs_enums OWNER TO pkb_user;

--
-- Name: rs_enums_id_seq; Type: SEQUENCE; Schema: registry; Owner: pkb_user
--

CREATE SEQUENCE registry.rs_enums_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE registry.rs_enums_id_seq OWNER TO pkb_user;

--
-- Name: rs_enums_id_seq; Type: SEQUENCE OWNED BY; Schema: registry; Owner: pkb_user
--

ALTER SEQUENCE registry.rs_enums_id_seq OWNED BY registry.rs_enums.id;


--
-- Name: terminology; Type: TABLE; Schema: registry; Owner: postgres
--

CREATE TABLE registry.terminology (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    raw_term text NOT NULL,
    normalized_value text,
    standard_term text,
    term_type text DEFAULT 'term'::text,
    is_case_sensitive boolean DEFAULT false,
    definition text,
    synonyms jsonb DEFAULT '[]'::jsonb,
    related_docs jsonb DEFAULT '[]'::jsonb,
    scope jsonb DEFAULT '[]'::jsonb,
    is_blocked boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE registry.terminology OWNER TO postgres;

--
-- Name: TABLE terminology; Type: COMMENT; Schema: registry; Owner: postgres
--

COMMENT ON TABLE registry.terminology IS 'Terminology registry entries: terms, synonyms, definitions and related docs';


--
-- Name: COLUMN terminology.raw_term; Type: COMMENT; Schema: registry; Owner: postgres
--

COMMENT ON COLUMN registry.terminology.raw_term IS 'Original raw term text';


--
-- Name: COLUMN terminology.normalized_value; Type: COMMENT; Schema: registry; Owner: postgres
--

COMMENT ON COLUMN registry.terminology.normalized_value IS 'Normalized term value used for lookup';


--
-- Name: COLUMN terminology.standard_term; Type: COMMENT; Schema: registry; Owner: postgres
--

COMMENT ON COLUMN registry.terminology.standard_term IS 'Canonical standard term mapped from raw_term';


--
-- Name: document_sections id; Type: DEFAULT; Schema: registry; Owner: postgres
--

ALTER TABLE ONLY registry.document_sections ALTER COLUMN id SET DEFAULT nextval('registry.document_sections_id_seq'::regclass);


--
-- Name: rs_enums id; Type: DEFAULT; Schema: registry; Owner: pkb_user
--

ALTER TABLE ONLY registry.rs_enums ALTER COLUMN id SET DEFAULT nextval('registry.rs_enums_id_seq'::regclass);


--
-- Data for Name: classifiers; Type: TABLE DATA; Schema: registry; Owner: postgres
--



--
-- Data for Name: document_history; Type: TABLE DATA; Schema: registry; Owner: postgres
--



--
-- Data for Name: document_references; Type: TABLE DATA; Schema: registry; Owner: postgres
--



--
-- Data for Name: document_sections; Type: TABLE DATA; Schema: registry; Owner: postgres
--



--
-- Data for Name: document_versions; Type: TABLE DATA; Schema: registry; Owner: postgres
--



--
-- Data for Name: documents; Type: TABLE DATA; Schema: registry; Owner: postgres
--



--
-- Data for Name: rs_enums; Type: TABLE DATA; Schema: registry; Owner: pkb_user
--

INSERT INTO registry.rs_enums VALUES (1, 'chunk_type', 'formula', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (2, 'chunk_type', 'image', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (3, 'chunk_type', 'table', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (4, 'chunk_type', 'text', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (5, 'classification_status_code', 'CONFIRMED', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (6, 'classification_status_code', 'NOT_FOUND', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (7, 'classification_status_code', 'NOT_USED', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (8, 'classification_status_code', 'PENDING_REVIEW', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (9, 'classification_status_code', 'UNASSIGNED', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (10, 'classifier_status', 'active', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (11, 'classifier_status', 'archived', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (12, 'classifier_status', 'deprecated', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (13, 'classifier_system', 'EXTERNAL', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (14, 'classifier_system', 'MKS', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (15, 'classifier_system', 'OKSTU', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (16, 'classifier_system', 'UDC', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (17, 'document_status', 'approved', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (18, 'document_status', 'archived', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (19, 'document_status', 'draft', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (20, 'document_status', 'failed', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (21, 'document_status', 'processing', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (22, 'document_status', 'ready_for_promotion', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (23, 'document_status', 'review_required', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (24, 'document_status', 'uploaded', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (25, 'document_status', 'validating', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (26, 'era', 'CIS', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (27, 'era', 'CURRENT', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (28, 'era', 'RF', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (29, 'era', 'USSR', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (30, 'jurisdiction', 'EU', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (31, 'jurisdiction', 'INTL', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (32, 'jurisdiction', 'NO', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (33, 'jurisdiction', 'RU', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (34, 'jurisdiction', 'US', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (35, 'pending_status', 'mapped', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (36, 'pending_status', 'new', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (37, 'pending_status', 'rejected', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (38, 'source_type', 'ASTM', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (39, 'source_type', 'DNV', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (40, 'source_type', 'GOST', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (41, 'source_type', 'GOST_R', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (42, 'source_type', 'ISO', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (43, 'source_type', 'OST', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (44, 'source_type', 'OTHER', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (45, 'source_type', 'RD', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (46, 'source_type', 'TU', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (47, 'term_type', 'acronym', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (48, 'term_type', 'avatar', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (49, 'term_type', 'foreign_term', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (50, 'term_type', 'standard_code', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (51, 'term_type', 'symbol', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (52, 'validation_status', 'invalid', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (53, 'validation_status', 'pending', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (54, 'validation_status', 'valid', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (55, 'validity_status', 'active', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (56, 'validity_status', 'cancelled', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (57, 'validity_status', 'draft', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (58, 'validity_status', 'historical', NULL, NULL, '2026-06-01 04:53:36.210846+01');
INSERT INTO registry.rs_enums VALUES (59, 'validity_status', 'superseded', NULL, NULL, '2026-06-01 04:53:36.210846+01');


--
-- Data for Name: terminology; Type: TABLE DATA; Schema: registry; Owner: postgres
--



--
-- Name: document_sections_id_seq; Type: SEQUENCE SET; Schema: registry; Owner: postgres
--

SELECT pg_catalog.setval('registry.document_sections_id_seq', 1, false);


--
-- Name: rs_enums_id_seq; Type: SEQUENCE SET; Schema: registry; Owner: pkb_user
--

SELECT pg_catalog.setval('registry.rs_enums_id_seq', 59, true);


--
-- Name: classifiers classifiers_pkey; Type: CONSTRAINT; Schema: registry; Owner: postgres
--

ALTER TABLE ONLY registry.classifiers
    ADD CONSTRAINT classifiers_pkey PRIMARY KEY (id);


--
-- Name: document_history document_history_pkey; Type: CONSTRAINT; Schema: registry; Owner: postgres
--

ALTER TABLE ONLY registry.document_history
    ADD CONSTRAINT document_history_pkey PRIMARY KEY (id);


--
-- Name: document_references document_references_pkey; Type: CONSTRAINT; Schema: registry; Owner: postgres
--

ALTER TABLE ONLY registry.document_references
    ADD CONSTRAINT document_references_pkey PRIMARY KEY (id);


--
-- Name: document_sections document_sections_pkey; Type: CONSTRAINT; Schema: registry; Owner: postgres
--

ALTER TABLE ONLY registry.document_sections
    ADD CONSTRAINT document_sections_pkey PRIMARY KEY (id);


--
-- Name: document_versions document_versions_pkey; Type: CONSTRAINT; Schema: registry; Owner: postgres
--

ALTER TABLE ONLY registry.document_versions
    ADD CONSTRAINT document_versions_pkey PRIMARY KEY (id);


--
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: registry; Owner: postgres
--

ALTER TABLE ONLY registry.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);


--
-- Name: rs_enums rs_enums_pkey; Type: CONSTRAINT; Schema: registry; Owner: pkb_user
--

ALTER TABLE ONLY registry.rs_enums
    ADD CONSTRAINT rs_enums_pkey PRIMARY KEY (id);


--
-- Name: terminology terminology_pkey; Type: CONSTRAINT; Schema: registry; Owner: postgres
--

ALTER TABLE ONLY registry.terminology
    ADD CONSTRAINT terminology_pkey PRIMARY KEY (id);


--
-- Name: classifiers unique_classifier_system_code; Type: CONSTRAINT; Schema: registry; Owner: postgres
--

ALTER TABLE ONLY registry.classifiers
    ADD CONSTRAINT unique_classifier_system_code UNIQUE (classifier_system, code);


--
-- Name: documents unique_doc_code_era; Type: CONSTRAINT; Schema: registry; Owner: postgres
--

ALTER TABLE ONLY registry.documents
    ADD CONSTRAINT unique_doc_code_era UNIQUE (doc_code, era);


--
-- Name: document_versions unique_version_number; Type: CONSTRAINT; Schema: registry; Owner: postgres
--

ALTER TABLE ONLY registry.document_versions
    ADD CONSTRAINT unique_version_number UNIQUE (document_id, version_number);


--
-- Name: rs_enums uq_rs_enums_key_value; Type: CONSTRAINT; Schema: registry; Owner: pkb_user
--

ALTER TABLE ONLY registry.rs_enums
    ADD CONSTRAINT uq_rs_enums_key_value UNIQUE (enum_key, enum_value);


--
-- Name: idx_classifiers_parent_code; Type: INDEX; Schema: registry; Owner: postgres
--

CREATE INDEX idx_classifiers_parent_code ON registry.classifiers USING btree (parent_code);


--
-- Name: idx_classifiers_system; Type: INDEX; Schema: registry; Owner: postgres
--

CREATE INDEX idx_classifiers_system ON registry.classifiers USING btree (classifier_system);


--
-- Name: idx_documents_created_at; Type: INDEX; Schema: registry; Owner: postgres
--

CREATE INDEX idx_documents_created_at ON registry.documents USING btree (created_at);


--
-- Name: idx_documents_doc_code; Type: INDEX; Schema: registry; Owner: postgres
--

CREATE INDEX idx_documents_doc_code ON registry.documents USING btree (doc_code);


--
-- Name: idx_documents_era; Type: INDEX; Schema: registry; Owner: postgres
--

CREATE INDEX idx_documents_era ON registry.documents USING btree (era);


--
-- Name: idx_documents_file_hash; Type: INDEX; Schema: registry; Owner: postgres
--

CREATE INDEX idx_documents_file_hash ON registry.documents USING btree (file_hash_sha256, file_size_bytes);


--
-- Name: idx_documents_jurisdiction; Type: INDEX; Schema: registry; Owner: postgres
--

CREATE INDEX idx_documents_jurisdiction ON registry.documents USING btree (jurisdiction);


--
-- Name: idx_documents_processing_status; Type: INDEX; Schema: registry; Owner: postgres
--

CREATE INDEX idx_documents_processing_status ON registry.documents USING btree (processing_status);


--
-- Name: idx_documents_title_hash; Type: INDEX; Schema: registry; Owner: postgres
--

CREATE INDEX idx_documents_title_hash ON registry.documents USING btree (title_hash_sha256);


--
-- Name: idx_documents_updated_at; Type: INDEX; Schema: registry; Owner: postgres
--

CREATE INDEX idx_documents_updated_at ON registry.documents USING btree (updated_at);


--
-- Name: idx_documents_validity_status; Type: INDEX; Schema: registry; Owner: postgres
--

CREATE INDEX idx_documents_validity_status ON registry.documents USING btree (validity_status);


--
-- Name: idx_history_document_id; Type: INDEX; Schema: registry; Owner: postgres
--

CREATE INDEX idx_history_document_id ON registry.document_history USING btree (document_id);


--
-- Name: idx_history_event_at; Type: INDEX; Schema: registry; Owner: postgres
--

CREATE INDEX idx_history_event_at ON registry.document_history USING btree (event_at);


--
-- Name: idx_history_event_type; Type: INDEX; Schema: registry; Owner: postgres
--

CREATE INDEX idx_history_event_type ON registry.document_history USING btree (event_type);


--
-- Name: idx_references_is_resolved; Type: INDEX; Schema: registry; Owner: postgres
--

CREATE INDEX idx_references_is_resolved ON registry.document_references USING btree (is_resolved);


--
-- Name: idx_references_resolved_document_id; Type: INDEX; Schema: registry; Owner: postgres
--

CREATE INDEX idx_references_resolved_document_id ON registry.document_references USING btree (resolved_document_id);


--
-- Name: idx_references_source_document_id; Type: INDEX; Schema: registry; Owner: postgres
--

CREATE INDEX idx_references_source_document_id ON registry.document_references USING btree (source_document_id);


--
-- Name: idx_references_target_doc_code; Type: INDEX; Schema: registry; Owner: postgres
--

CREATE INDEX idx_references_target_doc_code ON registry.document_references USING btree (target_doc_code);


--
-- Name: idx_rs_enums_enum_key; Type: INDEX; Schema: registry; Owner: pkb_user
--

CREATE INDEX idx_rs_enums_enum_key ON registry.rs_enums USING btree (enum_key);


--
-- Name: idx_sections_document_id; Type: INDEX; Schema: registry; Owner: postgres
--

CREATE INDEX idx_sections_document_id ON registry.document_sections USING btree (document_id);


--
-- Name: idx_sections_page; Type: INDEX; Schema: registry; Owner: postgres
--

CREATE INDEX idx_sections_page ON registry.document_sections USING btree (page);


--
-- Name: idx_sections_parent_id; Type: INDEX; Schema: registry; Owner: postgres
--

CREATE INDEX idx_sections_parent_id ON registry.document_sections USING btree (parent_id);


--
-- Name: idx_sections_path; Type: INDEX; Schema: registry; Owner: postgres
--

CREATE INDEX idx_sections_path ON registry.document_sections USING gist (path);


--
-- Name: idx_terminology_is_blocked; Type: INDEX; Schema: registry; Owner: postgres
--

CREATE INDEX idx_terminology_is_blocked ON registry.terminology USING btree (is_blocked);


--
-- Name: idx_terminology_term_type; Type: INDEX; Schema: registry; Owner: postgres
--

CREATE INDEX idx_terminology_term_type ON registry.terminology USING btree (term_type);


--
-- Name: idx_versions_document_id; Type: INDEX; Schema: registry; Owner: postgres
--

CREATE INDEX idx_versions_document_id ON registry.document_versions USING btree (document_id);


--
-- Name: idx_versions_uploaded_at; Type: INDEX; Schema: registry; Owner: postgres
--

CREATE INDEX idx_versions_uploaded_at ON registry.document_versions USING btree (uploaded_at);


--
-- Name: document_history document_history_document_id_fkey; Type: FK CONSTRAINT; Schema: registry; Owner: postgres
--

ALTER TABLE ONLY registry.document_history
    ADD CONSTRAINT document_history_document_id_fkey FOREIGN KEY (document_id) REFERENCES registry.documents(id) ON DELETE CASCADE;


--
-- Name: document_references document_references_resolved_document_id_fkey; Type: FK CONSTRAINT; Schema: registry; Owner: postgres
--

ALTER TABLE ONLY registry.document_references
    ADD CONSTRAINT document_references_resolved_document_id_fkey FOREIGN KEY (resolved_document_id) REFERENCES registry.documents(id) ON DELETE SET NULL;


--
-- Name: document_references document_references_source_document_id_fkey; Type: FK CONSTRAINT; Schema: registry; Owner: postgres
--

ALTER TABLE ONLY registry.document_references
    ADD CONSTRAINT document_references_source_document_id_fkey FOREIGN KEY (source_document_id) REFERENCES registry.documents(id) ON DELETE CASCADE;


--
-- Name: document_sections document_sections_document_id_fkey; Type: FK CONSTRAINT; Schema: registry; Owner: postgres
--

ALTER TABLE ONLY registry.document_sections
    ADD CONSTRAINT document_sections_document_id_fkey FOREIGN KEY (document_id) REFERENCES registry.documents(id) ON DELETE CASCADE;


--
-- Name: document_sections document_sections_parent_id_fkey; Type: FK CONSTRAINT; Schema: registry; Owner: postgres
--

ALTER TABLE ONLY registry.document_sections
    ADD CONSTRAINT document_sections_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES registry.document_sections(id) ON DELETE CASCADE;


--
-- Name: document_versions document_versions_document_id_fkey; Type: FK CONSTRAINT; Schema: registry; Owner: postgres
--

ALTER TABLE ONLY registry.document_versions
    ADD CONSTRAINT document_versions_document_id_fkey FOREIGN KEY (document_id) REFERENCES registry.documents(id) ON DELETE CASCADE;


--
-- Name: documents documents_predecessor_doc_id_fkey; Type: FK CONSTRAINT; Schema: registry; Owner: postgres
--

ALTER TABLE ONLY registry.documents
    ADD CONSTRAINT documents_predecessor_doc_id_fkey FOREIGN KEY (predecessor_doc_id) REFERENCES registry.documents(id) ON DELETE SET NULL;


--
-- Name: documents documents_successor_doc_id_fkey; Type: FK CONSTRAINT; Schema: registry; Owner: postgres
--

ALTER TABLE ONLY registry.documents
    ADD CONSTRAINT documents_successor_doc_id_fkey FOREIGN KEY (successor_doc_id) REFERENCES registry.documents(id) ON DELETE SET NULL;


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: pg_database_owner
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- Name: SCHEMA registry; Type: ACL; Schema: -; Owner: postgres
--

GRANT ALL ON SCHEMA registry TO pkb_user;


--
-- Name: TABLE classifiers; Type: ACL; Schema: registry; Owner: postgres
--

GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE registry.classifiers TO pkb_user;


--
-- Name: TABLE document_history; Type: ACL; Schema: registry; Owner: postgres
--

GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE registry.document_history TO pkb_user;


--
-- Name: TABLE document_references; Type: ACL; Schema: registry; Owner: postgres
--

GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE registry.document_references TO pkb_user;


--
-- Name: TABLE document_sections; Type: ACL; Schema: registry; Owner: postgres
--

GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE registry.document_sections TO pkb_user;


--
-- Name: SEQUENCE document_sections_id_seq; Type: ACL; Schema: registry; Owner: postgres
--

GRANT ALL ON SEQUENCE registry.document_sections_id_seq TO pkb_user;


--
-- Name: TABLE document_versions; Type: ACL; Schema: registry; Owner: postgres
--

GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE registry.document_versions TO pkb_user;


--
-- Name: TABLE documents; Type: ACL; Schema: registry; Owner: postgres
--

GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE registry.documents TO pkb_user;


--
-- Name: TABLE terminology; Type: ACL; Schema: registry; Owner: postgres
--

GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE registry.terminology TO pkb_user;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: registry; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA registry GRANT ALL ON SEQUENCES TO pkb_user;


--
-- Name: DEFAULT PRIVILEGES FOR FUNCTIONS; Type: DEFAULT ACL; Schema: registry; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA registry GRANT ALL ON FUNCTIONS TO pkb_user;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: registry; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA registry GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLES TO pkb_user;


--
-- PostgreSQL database dump complete
--

\unrestrict Mj5CxO7JO03xn5ldvSUrcF5NoB6WH0re5gSdajewHXscWXdAxREVrIB9WEhPMkh

