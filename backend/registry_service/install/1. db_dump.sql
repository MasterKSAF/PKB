--
-- PostgreSQL database dump
--

\restrict 5JPuILMMgVnnFpwdr6X727RiRE7m89eA7FUPs7UKB7sTxhKG9ma93cYmxciqySh

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
    classifier_system character varying(50) NOT NULL,
    code text NOT NULL,
    full_name text NOT NULL,
    description text,
    status character varying(50) DEFAULT 'active'::character varying,
    parent_code text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    effective_date date,
    replaced_by text
);


ALTER TABLE registry.classifiers OWNER TO postgres;

--
-- Name: TABLE classifiers; Type: COMMENT; Schema: registry; Owner: postgres
--

COMMENT ON TABLE registry.classifiers IS 'Classifier entries (system, code, names, status) used by the registry service.';


--
-- Name: document_history_id_seq; Type: SEQUENCE; Schema: registry; Owner: postgres
--

CREATE SEQUENCE registry.document_history_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE registry.document_history_id_seq OWNER TO postgres;

--
-- Name: document_history; Type: TABLE; Schema: registry; Owner: postgres
--

CREATE TABLE registry.document_history (
    id bigint DEFAULT nextval('registry.document_history_id_seq'::regclass) NOT NULL,
    document_id bigint NOT NULL,
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
-- Name: document_references_id_seq; Type: SEQUENCE; Schema: registry; Owner: postgres
--

CREATE SEQUENCE registry.document_references_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE registry.document_references_id_seq OWNER TO postgres;

--
-- Name: document_references; Type: TABLE; Schema: registry; Owner: postgres
--

CREATE TABLE registry.document_references (
    id bigint DEFAULT nextval('registry.document_references_id_seq'::regclass) NOT NULL,
    source_document_id bigint NOT NULL,
    target_doc_code text NOT NULL,
    reference_type character varying(50),
    context text,
    current_status character varying(50),
    replaced_by text,
    replacement_date date,
    is_resolved boolean DEFAULT false,
    resolved_document_id bigint,
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
    document_id bigint NOT NULL,
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
-- Name: document_versions_id_seq; Type: SEQUENCE; Schema: registry; Owner: postgres
--

CREATE SEQUENCE registry.document_versions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE registry.document_versions_id_seq OWNER TO postgres;

--
-- Name: document_versions; Type: TABLE; Schema: registry; Owner: postgres
--

CREATE TABLE registry.document_versions (
    id bigint DEFAULT nextval('registry.document_versions_id_seq'::regclass) NOT NULL,
    document_id bigint NOT NULL,
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
-- Name: documents_id_seq; Type: SEQUENCE; Schema: registry; Owner: postgres
--

CREATE SEQUENCE registry.documents_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE registry.documents_id_seq OWNER TO postgres;

--
-- Name: documents; Type: TABLE; Schema: registry; Owner: postgres
--

CREATE TABLE registry.documents (
    id bigint DEFAULT nextval('registry.documents_id_seq'::regclass) NOT NULL,
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
    successor_doc_id bigint,
    predecessor_doc_id bigint,
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
-- Name: terminology_id_seq; Type: SEQUENCE; Schema: registry; Owner: postgres
--

CREATE SEQUENCE registry.terminology_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE registry.terminology_id_seq OWNER TO postgres;

--
-- Name: terminology; Type: TABLE; Schema: registry; Owner: postgres
--

CREATE TABLE registry.terminology (
    id bigint DEFAULT nextval('registry.terminology_id_seq'::regclass) NOT NULL,
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

INSERT INTO registry.classifiers VALUES ('MKS', 'MKS_ROOT', '🌐 МЕЖГОСУДАРСТВЕННЫЙ КЛАССИФИКАТОР (МКС)', NULL, 'active', NULL, NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('OKSTU', 'OKSTU_ROOT', '🏛 ОБЩЕСОЮЗНЫЙ КЛАССИФИКАТОР (ОКСТУ)', NULL, 'active', NULL, NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('UDC', 'UDC_ROOT', '📚 УНИВЕРСАЛЬНАЯ ДЕСЯТИЧНАЯ КЛАССИФИКАЦИЯ', NULL, 'active', NULL, NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('EXTERNAL', 'EXT_ROOT', '🌍 ВНЕШНИЕ СИСТЕМЫ (DNV, ASTM, ОСТ, ТУ)', NULL, 'active', NULL, NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01', 'ОБЩИЕ ПОЛОЖЕНИЯ. ТЕРМИНОЛОГИЯ. СТАНДАРТИЗАЦИЯ. ДОКУМЕНТАЦИЯ', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03', 'УСЛУГИ. ОРГАНИЗАЦИЯ ФИРМ И УПРАВЛЕНИЕ ИМИ. АДМИНИСТРАЦИЯ. ТРАНСПОРТ. СОЦИОЛОГИЯ', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '07', 'ЕСТЕСТВЕННЫЕ И ПРИКЛАДНЫЕ НАУКИ', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11', 'ТЕХНОЛОГИЯ ЗДРАВООХРАНЕНИЯ', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13', 'ОКРУЖАЮЩАЯ СРЕДА. ЗАЩИТА ЧЕЛОВЕКА ОТ ВОЗДЕЙСТВИЯ ОКРУЖАЮЩЕЙ СРЕДЫ. БЕЗОПАСНОСТЬ', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17', 'МЕТРОЛОГИЯ И ИЗМЕРЕНИЯ. ФИЗИЧЕСКИЕ ЯВЛЕНИЯ', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '19', 'ИСПЫТАНИЯ', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21', 'МЕХАНИЧЕСКИЕ СИСТЕМЫ И УСТРОЙСТВА ОБЩЕГО НАЗНАЧЕНИЯ', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23', 'ГИДРАВЛИЧЕСКИЕ И ПНЕВМАТИЧЕСКИЕ СИСТЕМЫ И КОМПОНЕНТЫ ОБЩЕГО НАЗНАЧЕНИЯ', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25', 'МАШИНОСТРОЕНИЕ', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '27', 'ЭНЕРГЕТИКА И ТЕПЛОТЕХНИКА', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29', 'ЭЛЕКТРОТЕХНИКА', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31', 'ЭЛЕКТРОНИКА', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33', 'ТЕЛЕКОММУНИКАЦИИ. АУДИО- И ВИДЕОТЕХНИКА', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35', 'ИНФОРМАЦИОННЫЕ ТЕХНОЛОГИИ', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '37', 'ТЕХНОЛОГИЯ ПОЛУЧЕНИЯ ИЗОБРАЖЕНИЙ', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '39', 'ТОЧНАЯ МЕХАНИКА. ЮВЕЛИРНОЕ ДЕЛО', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43', 'ДОРОЖНО-ТРАНСПОРТНАЯ ТЕХНИКА', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '45', 'ЖЕЛЕЗНОДОРОЖНАЯ ТЕХНИКА', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '47', 'СУДОСТРОЕНИЕ И МОРСКИЕ СООРУЖЕНИЯ', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49', 'АВИАЦИОННАЯ И КОСМИЧЕСКАЯ ТЕХНИКА', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '53', 'ПОДЪЕМНО-ТРАНСПОРТНОЕ ОБОРУДОВАНИЕ', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '55', 'УПАКОВКА И РАЗМЕЩЕНИЕ ГРУЗОВ', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59', 'ТЕКСТИЛЬНОЕ И КОЖЕВЕННОЕ ПРОИЗВОДСТВО', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '61', 'ШВЕЙНАЯ ПРОМЫШЛЕННОСТЬ', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65', 'СЕЛЬСКОЕ ХОЗЯЙСТВО', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67', 'ПРОИЗВОДСТВО ПИЩЕВЫХ ПРОДУКТОВ', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71', 'ХИМИЧЕСКАЯ ПРОМЫШЛЕННОСТЬ', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '73', 'ГОРНОЕ ДЕЛО И ПОЛЕЗНЫЕ ИСКОПАЕМЫЕ', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '75', 'ДОБЫЧА И ПЕРЕРАБОТКА НЕФТИ, ГАЗА И СМЕЖНЫЕ ПРОИЗВОДСТВА', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77', 'МЕТАЛЛУРГИЯ', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '79', 'ТЕХНОЛОГИЯ ПЕРЕРАБОТКИ ДРЕВЕСИНЫ', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '81', 'СТЕКОЛЬНАЯ И КЕРАМИЧЕСКАЯ ПРОМЫШЛЕННОСТЬ', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83', 'РЕЗИНОВАЯ И ПЛАСТМАССОВАЯ ПРОМЫШЛЕННОСТЬ', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '85', 'ТЕХНОЛОГИЯ ПРОИЗВОДСТВА БУМАГИ', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '87', 'ЛАКОКРАСОЧНАЯ ПРОМЫШЛЕННОСТЬ', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91', 'СТРОИТЕЛЬНЫЕ МАТЕРИАЛЫ И СТРОИТЕЛЬСТВО', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '93', 'ГРАЖДАНСКОЕ СТРОИТЕЛЬСТВО', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '95', 'ВОЕННОЕ ДЕЛО. ВОЕННО-ИНЖЕНЕРНОЕ ДЕЛО. ВООРУЖЕНИЕ', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97', 'БЫТОВАЯ ТЕХНИКА И ТОРГОВОЕ ОБОРУДОВАНИЕ. ОТДЫХ. СПОРТ', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '99', '(РЕЗЕРВ)', NULL, 'active', 'MKS_ROOT', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.020', 'Терминология (принципы и координация)', NULL, 'active', '01', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040', 'Словари', NULL, 'active', '01', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.060', 'Величины и единицы измерения', NULL, 'active', '01', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.070', 'Цветовое кодирование', NULL, 'active', '01', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.075', 'Знаковые обозначения', NULL, 'active', '01', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.080', 'Графические обозначения', NULL, 'active', '01', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.100', 'Технические чертежи', NULL, 'active', '01', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.110', 'Техническая документация на продукцию', NULL, 'active', '01', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.120', 'Стандартизация. Общие правила', NULL, 'active', '01', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.140', 'Информатика. Издательское дело', NULL, 'active', '01', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.020', 'Социология. Демография', NULL, 'active', '03', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.040', 'Труд. Занятость', NULL, 'active', '03', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '37.100', 'Технология полиграфии', NULL, 'active', '37', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.060', 'Финансы. Банковское дело. Денежные системы. Страхование', NULL, 'active', '03', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.080', 'Услуги', NULL, 'active', '03', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.100', 'Организация фирм и управление ими. Системы менеджмента', NULL, 'active', '03', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.120', 'Качество', NULL, 'active', '03', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.140', 'Патенты. Интеллектуальная собственность', NULL, 'active', '03', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.160', 'Законодательство. Администрация', NULL, 'active', '03', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.180', 'Образование', NULL, 'active', '03', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.200', 'Досуг. Туризм', NULL, 'active', '03', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.220', 'Транспорт', NULL, 'active', '03', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.240', 'Почтовые услуги', NULL, 'active', '03', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '07.020', 'Математика', NULL, 'active', '07', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '07.030', 'Физика. Химия', NULL, 'active', '07', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '07.040', 'Астрономия. Геодезия. География', NULL, 'active', '07', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '07.060', 'Геология. Метеорология. Гидрология', NULL, 'active', '07', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '07.080', 'Биология. Ботаника. Зоология', NULL, 'active', '07', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '07.100', 'Микробиология', NULL, 'active', '07', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '07.120', 'Нанотехнологии', NULL, 'active', '07', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '07.140', 'Судебная наука', NULL, 'active', '07', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.020', 'Медицинские науки и учреждения здравоохранения в целом', NULL, 'active', '11', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.040', 'Медицинское оборудование', NULL, 'active', '11', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.060', 'Стоматология', NULL, 'active', '11', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.080', 'Стерилизация и дезинфекция', NULL, 'active', '11', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.100', 'Лабораторные препараты', NULL, 'active', '11', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.120', 'Фармацевтика', NULL, 'active', '11', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.140', 'Больничное оборудование', NULL, 'active', '11', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.160', 'Первая помощь', NULL, 'active', '11', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.180', 'Средства помощи для инвалидов и других лиц с ограничениями жизнедеятельности', NULL, 'active', '11', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.200', 'Регулирование рождаемости. Механические контрацептивы', NULL, 'active', '11', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.220', 'Ветеринария', NULL, 'active', '11', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.020', 'Охрана окружающей среды', NULL, 'active', '13', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.030', 'Отходы', NULL, 'active', '13', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.040', 'Качество воздуха', NULL, 'active', '13', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.060', 'Качество воды', NULL, 'active', '13', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.080', 'Качество грунта. Почвоведение', NULL, 'active', '13', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.100', 'Безопасность профессиональной деятельности. Промышленная гигиена', NULL, 'active', '13', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.110', 'Безопасность механизмов', NULL, 'active', '13', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.120', 'Безопасность в быту', NULL, 'active', '13', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.140', 'Воздействие шума на человека', NULL, 'active', '13', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.160', 'Воздействие вибрации и удара на человека', NULL, 'active', '13', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.180', 'Эргономика', NULL, 'active', '13', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.200', 'Борьба с несчастными случаями и катастрофами', NULL, 'active', '13', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.220', 'Защита от пожара', NULL, 'active', '13', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.230', 'Взрывозащита', NULL, 'active', '13', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.240', 'Защита от избыточного давления', NULL, 'active', '13', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.260', 'Защита от электрического удара. Работа с проводкой, находящейся под током', NULL, 'active', '13', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.280', 'Защита от радиационного излучения', NULL, 'active', '13', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.300', 'Защита от опасных грузов', NULL, 'active', '13', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.310', 'Защита от преступлений', NULL, 'active', '13', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.320', 'Системы аварийной сигнализации и оповещения', NULL, 'active', '13', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.340', 'Защитные средства', NULL, 'active', '13', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.020', 'Метрология и измерения в целом', NULL, 'active', '17', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.040', 'Линейные и угловые измерения', NULL, 'active', '17', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.060', 'Измерение объема, массы, плотности, вязкости', NULL, 'active', '17', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.080', 'Измерения времени, скорости, ускорения, угловой скорости', NULL, 'active', '17', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.100', 'Измерение силы, веса и давления', NULL, 'active', '17', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.120', 'Измерения параметров потока жидкости', NULL, 'active', '17', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.140', 'Акустика и акустические измерения', NULL, 'active', '17', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.160', 'Вибрации, измерения удара и вибрации', NULL, 'active', '17', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.180', 'Оптика и оптические измерения', NULL, 'active', '17', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.200', 'Термодинамика и измерения температуры', NULL, 'active', '17', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.220', 'Электричество. Магнетизм. Электрические и магнитные измерения', NULL, 'active', '17', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.240', 'Измерение излучений', NULL, 'active', '17', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '19.020', 'Условия и методика испытаний в целом', NULL, 'active', '19', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '19.040', 'Климатические испытания', NULL, 'active', '19', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '19.060', 'Механические испытания', NULL, 'active', '19', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '19.080', 'Электрические и электронные испытания', NULL, 'active', '19', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '19.100', 'Неразрушающие испытания', NULL, 'active', '19', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '19.120', 'Ситовый анализ. Просеивание', NULL, 'active', '19', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.020', 'Характеристики и конструкция механизмов, приборов и оборудования', NULL, 'active', '21', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.040', 'Винтовые резьбы', NULL, 'active', '21', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.060', 'Крепежные изделия', NULL, 'active', '21', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.080', 'Шарниры, проушины и другие шарнирные соединения', NULL, 'active', '21', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.100', 'Подшипники', NULL, 'active', '21', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.120', 'Валы и муфты', NULL, 'active', '21', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.140', 'Уплотнения, сальники', NULL, 'active', '21', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.160', 'Пружины', NULL, 'active', '21', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.180', 'Кожухи, корпуса и другие детали машин', NULL, 'active', '21', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.200', 'Зубчатые передачи', NULL, 'active', '21', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.220', 'Гибкие приводы и передачи', NULL, 'active', '21', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.240', 'Вращательно-поступательные механизмы и их детали', NULL, 'active', '21', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.260', 'Смазочные системы', NULL, 'active', '21', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.020', 'Резервуары для хранения жидкостей', NULL, 'active', '23', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.040', 'Трубопроводы и их компоненты', NULL, 'active', '23', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.060', 'Арматура трубопроводная', NULL, 'active', '23', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.080', 'Насосы', NULL, 'active', '23', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.100', 'Объемные гидроприводы и пневмоприводы', NULL, 'active', '23', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.120', 'Вентиляторы. Фены. Кондиционеры', NULL, 'active', '23', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.140', 'Компрессоры и пневматические машины', NULL, 'active', '23', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.160', 'Вакуумная технология', NULL, 'active', '23', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.020', 'Производственные формовочные процессы', NULL, 'active', '25', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.030', 'Аддитивные технологии', NULL, 'active', '25', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.040', 'Промышленные автоматизированные системы', NULL, 'active', '25', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.060', 'Станочные системы', NULL, 'active', '25', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.080', 'Металлорежущие станки', NULL, 'active', '25', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.100', 'Режущие инструменты', NULL, 'active', '25', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.120', 'Оборудование для бесстружечной обработки', NULL, 'active', '25', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.140', 'Ручные инструменты', NULL, 'active', '25', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.160', 'Сварка, пайка твердым и мягким припоем', NULL, 'active', '25', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.180', 'Промышленные печи', NULL, 'active', '25', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.200', 'Термическая обработка', NULL, 'active', '25', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.220', 'Обработка и покрытие поверхности', NULL, 'active', '25', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '27.010', 'Энергетика и теплотехника в целом', NULL, 'active', '27', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '27.015', 'Энергоэффективность. Энергосбережение в целом', NULL, 'active', '27', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '27.020', 'Двигатели внутреннего сгорания', NULL, 'active', '27', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '27.040', 'Газовые и паровые турбины. Паровые двигатели', NULL, 'active', '27', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '27.060', 'Горелки. Котлы', NULL, 'active', '27', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '27.070', 'Топливные элементы', NULL, 'active', '27', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '27.075', 'Водородные технологии', NULL, 'active', '27', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '27.080', 'Тепловые насосы', NULL, 'active', '27', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '27.100', 'Электростанции в целом', NULL, 'active', '27', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '27.120', 'Атомная энергетика', NULL, 'active', '27', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '27.140', 'Гидроэнергетика', NULL, 'active', '27', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '27.160', 'Гелиоэнергетика', NULL, 'active', '27', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '27.180', 'Системы ветровых энергетических турбин', NULL, 'active', '27', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '27.190', 'Биологические и альтернативные источники энергии', NULL, 'active', '27', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '27.200', 'Холодильная технология', NULL, 'active', '27', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '27.220', 'Регенерация тепла. Теплоизоляция', NULL, 'active', '27', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.020', 'Электротехника в целом', NULL, 'active', '29', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.030', 'Магнитные материалы', NULL, 'active', '29', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.035', 'Изоляционные материалы', NULL, 'active', '29', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.040', 'Изоляционные жидкости и газы (текучие среды)', NULL, 'active', '29', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.045', 'Полупроводниковые материалы', NULL, 'active', '29', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.050', 'Сверхпроводимость и проводниковые материалы', NULL, 'active', '29', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.060', 'Электрические провода и кабели', NULL, 'active', '29', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.080', 'Изоляция', NULL, 'active', '29', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.100', 'Компоненты электрооборудования', NULL, 'active', '29', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.120', 'Электрическая арматура', NULL, 'active', '29', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.130', 'Коммутационная аппаратура и аппаратура управления', NULL, 'active', '29', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.140', 'Лампы и сопутствующие изделия', NULL, 'active', '29', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.160', 'Машины вращающиеся', NULL, 'active', '29', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.180', 'Трансформаторы. Реакторы', NULL, 'active', '29', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.200', 'Выпрямители. Преобразователи. Стабилизированные источники питания', NULL, 'active', '29', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.220', 'Гальванические элементы и батареи', NULL, 'active', '29', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.240', 'Сети электропередачи и распределительные сети', NULL, 'active', '29', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.260', 'Электрическое оборудование для работы в особых условиях', NULL, 'active', '29', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.280', 'Электрическое тяговое оборудование', NULL, 'active', '29', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.020', 'Электронные компоненты в целом', NULL, 'active', '31', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.040', 'Резисторы', NULL, 'active', '31', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.060', 'Конденсаторы', NULL, 'active', '31', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.080', 'Полупроводниковые приборы', NULL, 'active', '31', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.100', 'Электронные лампы', NULL, 'active', '31', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.120', 'Электронные дисплеи', NULL, 'active', '31', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.140', 'Пьезоэлектрические приборы', NULL, 'active', '31', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.160', 'Электрические фильтры', NULL, 'active', '31', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.180', 'Печатные схемы и платы', NULL, 'active', '31', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.190', 'Электронные компоненты в сборе', NULL, 'active', '31', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.200', 'Интегральные схемы. Микроэлектроника', NULL, 'active', '31', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.220', 'Электромеханические компоненты электронного оборудования и телекоммуникационного оборудования', NULL, 'active', '31', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.240', 'Механические конструкции электронного оборудования', NULL, 'active', '31', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.260', 'Оптоэлектроника. Лазерное оборудование', NULL, 'active', '31', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.020', 'Телекоммуникации в целом', NULL, 'active', '33', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.030', 'Телекоммуникационные услуги. Применение', NULL, 'active', '33', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.040', 'Телекоммуникационные системы', NULL, 'active', '33', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.050', 'Телекоммуникационная оконечная аппаратура', NULL, 'active', '33', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.060', 'Радиосвязь', NULL, 'active', '33', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.070', 'Подвижные службы', NULL, 'active', '33', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.080', 'Цифровая сеть связи с интеграцией служб (ISDN)', NULL, 'active', '33', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.100', 'Электромагнитная совместимость (EMC)', NULL, 'active', '33', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.120', 'Компоненты и вспомогательные приспособления телекоммуникационного оборудования', NULL, 'active', '33', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.140', 'Специальное измерительное оборудование для систем телекоммуникаций', NULL, 'active', '33', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.160', 'Аудио-, видео- и аудиовизуальная техника', NULL, 'active', '33', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.170', 'Теле- и радиовещание', NULL, 'active', '33', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.180', 'Волоконно-оптическая связь', NULL, 'active', '33', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.200', 'Телемеханика. Телеметрия', NULL, 'active', '33', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.020', 'Информационные технологии (ИТ) в целом', NULL, 'active', '35', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.030', 'Безопасность ИТ', NULL, 'active', '35', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.040', 'Кодирование информации', NULL, 'active', '35', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.060', 'Языки, используемые в информационных технологиях', NULL, 'active', '35', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.080', 'Программное обеспечение', NULL, 'active', '35', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.100', 'Взаимосвязь открытых систем', NULL, 'active', '35', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.110', 'Организация сети', NULL, 'active', '35', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.140', 'Компьютерная графика', NULL, 'active', '35', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.160', 'Микропроцессорные системы', NULL, 'active', '35', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.180', 'Информационно-технологические терминалы и другие периферийные устройства', NULL, 'active', '35', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.200', 'Интерфейсы и межсоединительные устройства', NULL, 'active', '35', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.210', '"Облачная" обработка данных', NULL, 'active', '35', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.220', 'Запоминающие устройства', NULL, 'active', '35', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.240', 'Применение информационных технологий', NULL, 'active', '35', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.260', 'Машины конторские', NULL, 'active', '35', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '37.020', 'Оптическое оборудование', NULL, 'active', '37', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '37.040', 'Фотография', NULL, 'active', '37', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '37.060', 'Кинематография', NULL, 'active', '37', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '37.080', 'Способы формирования изображения документов', NULL, 'active', '37', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '39.020', 'Точная механика', NULL, 'active', '39', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '39.040', 'Часовое дело', NULL, 'active', '39', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '39.060', 'Ювелирное дело', NULL, 'active', '39', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.020', 'Дорожно-транспортные средства в целом', NULL, 'active', '43', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.040', 'Системы дорожно-транспортных средств', NULL, 'active', '43', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.060', 'Двигатели внутреннего сгорания для дорожно-транспортных средств', NULL, 'active', '43', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.080', 'Грузовые транспортные средства', NULL, 'active', '43', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.100', 'Легковые автомобили. Караваны и легкие прицепы', NULL, 'active', '43', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.120', 'Электрические дорожно-транспортные средства', NULL, 'active', '43', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.140', 'Мотоциклы и мопеды', NULL, 'active', '43', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.150', 'Велосипеды', NULL, 'active', '43', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.160', 'Транспорт специального назначения', NULL, 'active', '43', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.180', 'Диагностическое и испытательное оборудование и оборудование для технического обслуживания', NULL, 'active', '43', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '45.020', 'Железнодорожная техника в целом', NULL, 'active', '45', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '45.040', 'Материалы и компоненты для железнодорожной техники', NULL, 'active', '45', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '45.060', 'Подвижной состав железных дорог', NULL, 'active', '45', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '45.080', 'Рельсы и компоненты железных дорог', NULL, 'active', '45', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '45.100', 'Оборудование для канатных дорог', NULL, 'active', '45', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '45.120', 'Оборудование для сооружения и технического обслуживания железных/канатных дорог', NULL, 'active', '45', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '45.140', 'Оборудование метро, трамваев и легкорельсового транспорта', NULL, 'active', '45', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '47.020', 'Судостроение и морские сооружения в целом', NULL, 'active', '47', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '47.040', 'Морские суда', NULL, 'active', '47', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '47.060', 'Суда внутренней навигации', NULL, 'active', '47', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '47.080', 'Малые суда', NULL, 'active', '47', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.020', 'Авиационные и космические аппараты в целом', NULL, 'active', '49', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.025', 'Материалы для авиационно-космических конструкций', NULL, 'active', '49', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.030', 'Крепежные изделия для авиационно-космических конструкций', NULL, 'active', '49', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.035', 'Компоненты для авиационно-космических конструкций', NULL, 'active', '49', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.040', 'Покрытия и связанные с ними процессы в авиационно-космической промышленности', NULL, 'active', '49', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.045', 'Конструкции и элементы конструкций', NULL, 'active', '49', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.050', 'Авиационно-космические двигатели и силовые установки', NULL, 'active', '49', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.060', 'Авиационно-космическое электрооборудование и системы', NULL, 'active', '49', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.080', 'Авиационно-космические гидравлические и пневматические системы и их компоненты', NULL, 'active', '49', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.090', 'Бортовое оборудование и приборы', NULL, 'active', '49', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.095', 'Оборудование для пассажиров и кабин', NULL, 'active', '49', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.100', 'Оборудование наземного обслуживания и ремонта', NULL, 'active', '49', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.120', 'Грузовое оборудование', NULL, 'active', '49', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.140', 'Космические системы и операции', NULL, 'active', '49', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '53.020', 'Подъемное оборудование', NULL, 'active', '53', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '53.040', 'Подъемно-транспортное оборудование непрерывного действия', NULL, 'active', '53', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '53.060', 'Грузовые тележки', NULL, 'active', '53', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '53.080', 'Оборудование для хранения', NULL, 'active', '53', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '53.100', 'Землеройные машины', NULL, 'active', '53', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '53.120', 'Оборудование для ручных работ', NULL, 'active', '53', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '55.020', 'Упаковка и размещение грузов в целом', NULL, 'active', '55', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '55.040', 'Упаковочные материалы и приспособления', NULL, 'active', '55', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '55.060', 'Катушки. Бобины', NULL, 'active', '55', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '55.080', 'Мешки, сумки', NULL, 'active', '55', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '55.100', 'Бутыли. Горшки. Банки', NULL, 'active', '55', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '55.120', 'Консервные банки. Баллоны. Тубы', NULL, 'active', '55', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '55.130', 'Аэрозольная тара', NULL, 'active', '55', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '55.140', 'Бочки. Барабаны. Канистры', NULL, 'active', '55', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '55.160', 'Ящики. Коробки. Решетчатая тара', NULL, 'active', '55', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '55.180', 'Размещение грузов для перевозок', NULL, 'active', '55', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '55.200', 'Упаковочное оборудование', NULL, 'active', '55', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '55.220', 'Хранение. Складирование', NULL, 'active', '55', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '55.230', 'Размещение и торговые автоматы', NULL, 'active', '55', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.020', 'Процессы в текстильной промышленности', NULL, 'active', '59', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.040', 'Вспомогательные материалы для отделки текстиля', NULL, 'active', '59', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.060', 'Текстильные волокна', NULL, 'active', '59', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.080', 'Изделия текстильной промышленности', NULL, 'active', '59', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.100', 'Материалы для усиления композитов', NULL, 'active', '59', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.120', 'Текстильные машины', NULL, 'active', '59', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.140', 'Технология производства кожи', NULL, 'active', '59', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '61.020', 'Одежда', NULL, 'active', '61', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '61.040', 'Головные уборы. Аксессуары. Застежки для одежды', NULL, 'active', '61', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '61.060', 'Обувь', NULL, 'active', '61', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '61.080', 'Швейные машины и другое оборудование для швейной промышленности', NULL, 'active', '61', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.020', 'Земледелие и лесоводство', NULL, 'active', '65', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.040', 'Сельскохозяйственные постройки, сооружения и установки', NULL, 'active', '65', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.060', 'Сельскохозяйственные машины, инвентарь и оборудование', NULL, 'active', '65', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.080', 'Удобрения', NULL, 'active', '65', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.100', 'Пестициды и другие агрохимикаты', NULL, 'active', '65', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.120', 'Корма для животных', NULL, 'active', '65', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.140', 'Пчеловодство', NULL, 'active', '65', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.145', 'Охота', NULL, 'active', '65', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.150', 'Рыболовство и рыбоводство', NULL, 'active', '65', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.160', 'Табак, табачные изделия и соответствующее оборудование', NULL, 'active', '65', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.020', 'Процессы в пищевой промышленности', NULL, 'active', '67', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.040', 'Пищевые продукты в целом', NULL, 'active', '67', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.050', 'Общие методы проверки и анализа пищевых продуктов', NULL, 'active', '67', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.060', 'Зерновые, бобовые и продукты их переработки', NULL, 'active', '67', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.080', 'Фрукты. Овощи', NULL, 'active', '67', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.100', 'Молоко и молочные продукты', NULL, 'active', '67', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.120', 'Мясо, мясные продукты и другие продукты животного происхождения', NULL, 'active', '67', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.140', 'Чай. Кофе. Какао', NULL, 'active', '67', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.160', 'Напитки', NULL, 'active', '67', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.180', 'Сахар. Продукты из сахара. Крахмал', NULL, 'active', '67', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.190', 'Шоколад', NULL, 'active', '67', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.200', 'Пищевые масла и жиры. Семена масличных культур', NULL, 'active', '67', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.220', 'Пряности и приправы. Пищевые добавки', NULL, 'active', '67', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.230', 'Расфасованные пищевые продукты и пищевые продукты, подвергнутые кулинарной обработке', NULL, 'active', '67', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.240', 'Органолептический анализ', NULL, 'active', '67', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.250', 'Материалы и предметы в контакте с пищевыми продуктами', NULL, 'active', '67', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.260', 'Установки и оборудование для пищевой промышленности', NULL, 'active', '67', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.020', 'Производство в химической промышленности', NULL, 'active', '71', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.040', 'Аналитическая химия', NULL, 'active', '71', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.060', 'Неорганические химические вещества', NULL, 'active', '71', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.080', 'Органические химические вещества', NULL, 'active', '71', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.100', 'Продукты химической промышленности', NULL, 'active', '71', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.120', 'Оборудование для химической промышленности', NULL, 'active', '71', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '73.020', 'Горное дело и открытые горные работы', NULL, 'active', '73', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '73.040', 'Угли', NULL, 'active', '73', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '73.060', 'Рудные минералы и их концентраты', NULL, 'active', '73', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '73.080', 'Нерудные минералы', NULL, 'active', '73', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '73.100', 'Горное оборудование', NULL, 'active', '73', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '73.120', 'Оборудование для обработки минералов', NULL, 'active', '73', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '75.020', 'Добыча и переработка нефти и природного газа', NULL, 'active', '75', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '75.040', 'Нефть', NULL, 'active', '75', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '75.060', 'Газ горючий природный', NULL, 'active', '75', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '75.080', 'Нефтяные продукты в целом', NULL, 'active', '75', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '75.100', 'Смазки, индустриальные масла и связанные с ними продукты', NULL, 'active', '75', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '75.120', 'Гидравлические жидкости', NULL, 'active', '75', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '75.140', 'Парафины, битумные материалы и другие нефтепродукты', NULL, 'active', '75', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '75.160', 'Топливо', NULL, 'active', '75', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.060.20', 'Оксиды', NULL, 'active', '71.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '75.180', 'Оборудование для нефтяной и газовой промышленности', NULL, 'active', '75', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '75.200', 'Оборудование для переработки нефти, нефтяных продуктов и природного газа', NULL, 'active', '75', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.020', 'Производство металлов', NULL, 'active', '77', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.040', 'Испытания металлов', NULL, 'active', '77', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.060', 'Коррозия металлов', NULL, 'active', '77', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.080', 'Черные металлы', NULL, 'active', '77', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.100', 'Ферросплавы', NULL, 'active', '77', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.120', 'Цветные металлы', NULL, 'active', '77', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.140', 'Продукция из чугуна и стали', NULL, 'active', '77', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.150', 'Продукция из цветных металлов', NULL, 'active', '77', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.160', 'Порошковая металлургия', NULL, 'active', '77', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.180', 'Оборудование для металлургической промышленности', NULL, 'active', '77', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '79.020', 'Процессы обработки древесины', NULL, 'active', '79', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '79.040', 'Древесина, пиловочные бревна, пиломатериалы', NULL, 'active', '79', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '79.060', 'Древесные плиты', NULL, 'active', '79', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '79.080', 'Полуфабрикаты из древесины', NULL, 'active', '79', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '79.100', 'Пробка и изделия из пробки', NULL, 'active', '79', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '79.120', 'Деревообрабатывающее оборудование', NULL, 'active', '79', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '81.020', 'Процессы в стекольной и керамической промышленности', NULL, 'active', '81', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '81.040', 'Стекло', NULL, 'active', '81', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '81.060', 'Керамика', NULL, 'active', '81', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '81.080', 'Огнеупоры', NULL, 'active', '81', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '81.100', 'Оборудование для стекольной и керамической промышленности', NULL, 'active', '81', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83.020', 'Процессы производства резины и пластмасс', NULL, 'active', '83', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83.040', 'Сырье для производства резины и пластмасс', NULL, 'active', '83', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83.060', 'Резина', NULL, 'active', '83', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83.080', 'Пластмассы', NULL, 'active', '83', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83.100', 'Поропласты', NULL, 'active', '83', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83.120', 'Армированные пластмассы', NULL, 'active', '83', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83.140', 'Резиновые и пластмассовые изделия', NULL, 'active', '83', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83.160', 'Шины', NULL, 'active', '83', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83.180', 'Клеи', NULL, 'active', '83', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83.200', 'Оборудование для производства резины и пластмасс', NULL, 'active', '83', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '85.020', 'Процессы производства бумаги', NULL, 'active', '85', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '85.040', 'Целлюлоза', NULL, 'active', '85', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '85.060', 'Бумага и картон', NULL, 'active', '85', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '85.080', 'Бумажные изделия', NULL, 'active', '85', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '85.100', 'Оборудование для производства бумаги', NULL, 'active', '85', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '87.020', 'Процессы производства лакокрасочных покрытий', NULL, 'active', '87', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '87.040', 'Краски и лаки', NULL, 'active', '87', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '87.060', 'Ингредиенты красок', NULL, 'active', '87', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '87.080', 'Типографские краски. Печатные краски', NULL, 'active', '87', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '87.100', 'Оборудование для производства лакокрасочных покрытий', NULL, 'active', '87', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.010', 'Строительная промышленность', NULL, 'active', '91', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.020', 'Территориальное планирование. Планировка городов', NULL, 'active', '91', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.040', 'Строительство', NULL, 'active', '91', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.060', 'Строительные элементы', NULL, 'active', '91', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.080', 'Конструкции зданий', NULL, 'active', '91', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.090', 'Наружные конструкции', NULL, 'active', '91', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.100', 'Строительные материалы', NULL, 'active', '91', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.120', 'Защита зданий снаружи и внутри', NULL, 'active', '91', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.140', 'Установки в зданиях', NULL, 'active', '91', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.160', 'Освещение', NULL, 'active', '91', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.180', 'Внутренняя отделка', NULL, 'active', '91', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.190', 'Арматура для зданий', NULL, 'active', '91', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.200', 'Технология строительства', NULL, 'active', '91', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.220', 'Строительное оборудование', NULL, 'active', '91', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '93.010', 'Гражданское строительство в целом', NULL, 'active', '93', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '93.020', 'Земляные работы. Выемка грунта. Сооружение фундаментов. Подземные работы', NULL, 'active', '93', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '93.025', 'Наружные системы подачи воды', NULL, 'active', '93', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '93.030', 'Наружные канализационные системы', NULL, 'active', '93', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '93.040', 'Сооружение мостов', NULL, 'active', '93', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '93.060', 'Сооружение тоннелей', NULL, 'active', '93', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.060.30', 'Кислоты', NULL, 'active', '71.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '93.080', 'Строительство дорог', NULL, 'active', '93', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '93.100', 'Сооружение железных дорог', NULL, 'active', '93', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '93.110', 'Сооружение канатных транспортных систем', NULL, 'active', '93', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '93.120', 'Сооружение аэропортов', NULL, 'active', '93', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '93.140', 'Сооружение водных путей, портов и дамб', NULL, 'active', '93', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '93.160', 'Сооружение гидротехнических объектов', NULL, 'active', '93', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '95.020', 'Военные вопросы в целом', NULL, 'active', '95', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '95.040', 'Военно-инженерное дело', NULL, 'active', '95', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '95.060', 'Вооружение', NULL, 'active', '95', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.020', 'Домашнее хозяйство в целом', NULL, 'active', '97', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.030', 'Бытовые электрические приборы в целом', NULL, 'active', '97', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.040', 'Кухонное оборудование', NULL, 'active', '97', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.060', 'Прачечное оборудование', NULL, 'active', '97', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.080', 'Чистящие устройства', NULL, 'active', '97', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.100', 'Бытовые, торговые и промышленные нагревательные приборы', NULL, 'active', '97', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.120', 'Автоматические регуляторы бытового назначения', NULL, 'active', '97', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.130', 'Аксессуары для магазинов', NULL, 'active', '97', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.140', 'Мебель', NULL, 'active', '97', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.145', 'Лестницы-стремянки', NULL, 'active', '97', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.150', 'Нетекстильные покрытия для полов', NULL, 'active', '97', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.160', 'Бытовые швейные изделия. Белье', NULL, 'active', '97', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.170', 'Бытовые приборы для ухода за телом', NULL, 'active', '97', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.180', 'Различная бытовая техника и торговое оборудование', NULL, 'active', '97', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.190', 'Техника для детей', NULL, 'active', '97', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.195', 'Предметы искусства и ремесел. Культурные ценности и наследие', NULL, 'active', '97', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.200', 'Оборудование для отдыха', NULL, 'active', '97', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.220', 'Спортивный инвентарь и сооружения', NULL, 'active', '97', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.01', 'Общие положения. Терминология. Стандартизация. Документация (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.03', 'Услуги. Организация фирм, управление ими и качество. Администрация. Транспорт. Социология (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.07', 'Естественные и прикладные науки (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.11', 'Здравоохранение (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.13', 'Охрана окружающей среды, защита человека от воздействия окружающей среды. Безопасность (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.17', 'Метрология и измерения. Физические явления (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.19', 'Испытания (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.21', 'Механические системы и компоненты общего назначения (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.23', 'Гидравлические и пневматические системы и компоненты общего назначения (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.25', 'Машиностроение (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.27', 'Энергетика и теплотехника (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.29', 'Электротехника (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.31', 'Электроника (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.33', 'Телекоммуникации. Аудио- и видеотехника (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.35', 'Информационные технологии (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.37', 'Технология получения изображений (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.39', 'Точная механика. Ювелирное дело (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.43', 'Дорожно-транспортная техника (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.45', 'Железнодорожная техника (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.47', 'Судостроение и морские сооружения (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.49', 'Авиационная и космическая техника (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.53', 'Подъемно-транспортное оборудование (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.55', 'Упаковка и размещение грузов (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.59', 'Технология текстильного и кожевенного производства (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.61', 'Швейная промышленность (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.65', 'Сельское хозяйство (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.67', 'Технология пищевых продуктов (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.71', 'Химическая технология (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.73', 'Горное дело и полезные ископаемые (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.75', 'Добыча и переработка нефти, газа и смежные производства (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.77', 'Металлургия (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.79', 'Технология переработки древесины (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.81', 'Стекольная и керамическая промышленность (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.83', 'Резиновая и пластмассовая промышленность (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.85', 'Технология производства бумаги (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.87', 'Лакокрасочная промышленность (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.91', 'Строительные материалы и строительство (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.93', 'Гражданское строительство (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.95', 'Военное дело. Военно-инженерное дело. Вооружение (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.040.97', 'Бытовая техника и торговое оборудование. Отдых. Спорт (Словари)', NULL, 'active', '01.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.080.01', 'Графические обозначения в целом', NULL, 'active', '01.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.080.10', 'Обозначения общедоступной информации. Знаки. Пластинки. Этикетки', NULL, 'active', '01.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.080.20', 'Графические обозначения для специального оборудования', NULL, 'active', '01.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.080.30', 'Графические обозначения для машиностроительных и строительных чертежей, диаграмм, планов, карт и соответствующей технической документации на продукцию', NULL, 'active', '01.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.080.40', 'Графические обозначения для технических чертежей, диаграмм, схем и соответствующей технической документации в области электротехники и электроники', NULL, 'active', '01.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.080.50', 'Графические обозначения для технических чертежей и соответствующей технической документации в области информационных технологий и телекоммуникаций', NULL, 'active', '01.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.080.99', 'Графические обозначения прочие', NULL, 'active', '01.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.100.01', 'Технические чертежи в целом', NULL, 'active', '01.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.100.20', 'Машиностроительные чертежи', NULL, 'active', '01.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.100.25', 'Технические чертежи в области электротехники и электроники', NULL, 'active', '01.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.100.27', 'Технические чертежи в области телекоммуникаций и информационных технологий', NULL, 'active', '01.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.100.30', 'Строительные чертежи', NULL, 'active', '01.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.100.40', 'Чертежное оборудование', NULL, 'active', '01.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.100.99', 'Технические чертежи, прочие аспекты', NULL, 'active', '01.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.140.10', 'Письмо и транслитерация', NULL, 'active', '01.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.140.20', 'Информатика', NULL, 'active', '01.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.140.30', 'Документы в управлении, торговле и промышленности', NULL, 'active', '01.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '01.140.40', 'Издательское дело', NULL, 'active', '01.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.080.01', 'Услуги в целом', NULL, 'active', '03.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.080.10', 'Техническое обслуживание и ремонт. Управление объектами', NULL, 'active', '03.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.080.20', 'Обслуживание компаний', NULL, 'active', '03.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.080.30', 'Обслуживание потребителей', NULL, 'active', '03.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.080.99', 'Услуги прочие', NULL, 'active', '03.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.100.01', 'Организация фирм и управление в целом', NULL, 'active', '03.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.100.02', 'Организация управления и этика', NULL, 'active', '03.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.100.10', 'Закупки. Заготовки. Логистика', NULL, 'active', '03.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.100.20', 'Торговля. Коммерческие функции. Маркетинг', NULL, 'active', '03.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.100.30', 'Управление трудовыми ресурсами', NULL, 'active', '03.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.100.40', 'Научные исследования и разработки', NULL, 'active', '03.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.100.50', 'Производство. Управление производством', NULL, 'active', '03.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.100.60', 'Бухгалтерский учет', NULL, 'active', '03.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.100.70', 'Системы менеджмента', NULL, 'active', '03.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.100.99', 'Организация фирм и управление ими, прочие аспекты', NULL, 'active', '03.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.120.01', 'Качество в целом', NULL, 'active', '03.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.120.10', 'Управление качеством и обеспечение качества', NULL, 'active', '03.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.120.20', 'Сертификация продукции и фирм. Оценка соответствия', NULL, 'active', '03.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.120.30', 'Применение статистических методов', NULL, 'active', '03.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.120.99', 'Качество, прочие аспекты', NULL, 'active', '03.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.200.01', 'Отдых и туризм, общие стандарты', NULL, 'active', '03.200', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.200.10', 'Экстремальный туризм', NULL, 'active', '03.200', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.200.99', 'Прочие стандарты, касающиеся отдыха и туризма', NULL, 'active', '03.200', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.220.01', 'Транспорт в целом', NULL, 'active', '03.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.220.20', 'Дорожный транспорт', NULL, 'active', '03.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.220.30', 'Рельсовый транспорт', NULL, 'active', '03.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.220.40', 'Водный транспорт', NULL, 'active', '03.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.220.50', 'Воздушный транспорт', NULL, 'active', '03.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '03.220.99', 'Виды транспорта прочие', NULL, 'active', '03.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '07.100.01', 'Микробиология в целом', NULL, 'active', '07.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '07.100.10', 'Медицинская микробиология', NULL, 'active', '07.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '07.100.20', 'Микробиология воды', NULL, 'active', '07.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '07.100.30', 'Пищевая микробиология', NULL, 'active', '07.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '07.100.40', 'Микробиология в косметике', NULL, 'active', '07.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '07.100.99', 'Микробиология, прочие аспекты', NULL, 'active', '07.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.020.01', 'Менеджмент качества и менеджмент окружающей среды в сфере охраны здоровья населения', NULL, 'active', '11.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.020.10', 'Общие услуги охраны здоровья населения', NULL, 'active', '11.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.020.20', 'Медицинская наука', NULL, 'active', '11.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.020.99', 'Стандарты, связанные с охраной здоровья населения, прочие', NULL, 'active', '11.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.040.01', 'Медицинское оборудование в целом', NULL, 'active', '11.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.040.10', 'Наркозные, дыхательные и реанимационные аппараты', NULL, 'active', '11.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.040.20', 'Аппараты для переливания крови, вливаний и инъекций', NULL, 'active', '11.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.040.25', 'Шприцы, иглы и катетеры', NULL, 'active', '11.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.040.30', 'Хирургические инструменты и материалы', NULL, 'active', '11.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.040.40', 'Имплантаты для хирургии, протезирования и ортоптики', NULL, 'active', '11.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.040.50', 'Радиографическое оборудование', NULL, 'active', '11.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.040.55', 'Диагностическое оборудование', NULL, 'active', '11.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.040.60', 'Терапевтическое оборудование', NULL, 'active', '11.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.040.70', 'Офтальмологическое оборудование', NULL, 'active', '11.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.040.99', 'Медицинское оборудование прочее', NULL, 'active', '11.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.060.01', 'Стоматология в целом', NULL, 'active', '11.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.060.10', 'Стоматологические материалы', NULL, 'active', '11.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.060.15', 'Стоматологические имплантаты', NULL, 'active', '11.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.060.20', 'Стоматологическое оборудование', NULL, 'active', '11.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.060.25', 'Стоматологические инструменты', NULL, 'active', '11.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.080.01', 'Стерилизация и дезинфекция в целом', NULL, 'active', '11.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.080.10', 'Оборудование для стерилизации', NULL, 'active', '11.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.080.20', 'Дезинфицирующие и антисептические средства', NULL, 'active', '11.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.080.30', 'Стерильная упаковка', NULL, 'active', '11.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.080.99', 'Стерилизация и дезинфекция, прочие аспекты', NULL, 'active', '11.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.100.01', 'Лабораторные препараты в целом', NULL, 'active', '11.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.100.10', 'Диагностические системы инвитро (in vitro)', NULL, 'active', '11.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.100.20', 'Биологическая оценка медицинских средств', NULL, 'active', '11.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.100.30', 'Анализ крови и мочи', NULL, 'active', '11.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.100.99', 'Лабораторные препараты, прочие аспекты', NULL, 'active', '11.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.120.01', 'Фармацевтика в целом', NULL, 'active', '11.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.120.10', 'Медикаменты', NULL, 'active', '11.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.120.20', 'Перевязочные материалы и компрессы', NULL, 'active', '11.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.120.99', 'Фармацевтика, прочие аспекты', NULL, 'active', '11.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.180.01', 'Средства помощи для инвалидов и других лиц с ограничениями жизнедеятельности', NULL, 'active', '11.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.180.10', 'Средства помощи и приспособления для обеспечения доступности объектов и инфраструктуры', NULL, 'active', '11.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.180.15', 'Средства для глухих и плохослышащих людей', NULL, 'active', '11.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.180.20', 'Средства сбора мочи и стомы', NULL, 'active', '11.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.060.40', 'Основания', NULL, 'active', '71.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.180.30', 'Средства помощи для слепых и слабовидящих людей', NULL, 'active', '11.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.180.40', 'Средства помощи для питья и приема пищи', NULL, 'active', '11.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '11.180.99', 'Средства помощи для лиц с физическими недостатками и увечьями прочие', NULL, 'active', '11.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.020.01', 'Окружающая среда и охрана окружающей среды в целом', NULL, 'active', '13.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.020.10', 'Менеджмент окружающей среды (экологический менеджмент)', NULL, 'active', '13.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.020.20', 'Экономика окружающей среды. Устойчивое развитие', NULL, 'active', '13.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.020.30', 'Оценка воздействия на окружающую среду', NULL, 'active', '13.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.020.40', 'Загрязнение, борьба с загрязнением и консервация', NULL, 'active', '13.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.020.50', 'Экологическая маркировка', NULL, 'active', '13.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.020.55', 'Биопродукция', NULL, 'active', '13.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.020.60', 'Жизненный цикл продукции', NULL, 'active', '13.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.020.70', 'Проекты в области охраны окружающей среды', NULL, 'active', '13.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.020.99', 'Охрана окружающей среды, прочие аспекты', NULL, 'active', '13.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.030.01', 'Отходы в целом', NULL, 'active', '13.030', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.030.10', 'Твердые отходы', NULL, 'active', '13.030', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.030.20', 'Жидкие отходы. Осадки', NULL, 'active', '13.030', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.030.30', 'Специальные отходы', NULL, 'active', '13.030', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.030.40', 'Установки и оборудование для удаления и обработки отходов', NULL, 'active', '13.030', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.030.50', 'Рециклинг', NULL, 'active', '13.030', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.030.99', 'Отходы, прочие аспекты', NULL, 'active', '13.030', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.040.01', 'Качество воздуха в целом', NULL, 'active', '13.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.040.20', 'Окружающая атмосфера', NULL, 'active', '13.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.040.30', 'Атмосфера рабочей зоны', NULL, 'active', '13.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.040.35', 'Чистые помещения и связанные с ними контролируемые условия окружающей среды', NULL, 'active', '13.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.040.40', 'Выбросы стационарных источников', NULL, 'active', '13.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.040.50', 'Выбросы системы выпуска двигателей транспортных средств', NULL, 'active', '13.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.040.99', 'Качество воздуха, прочие аспекты', NULL, 'active', '13.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.060.01', 'Качество воды в целом', NULL, 'active', '13.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.060.10', 'Вода естественных источников', NULL, 'active', '13.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.060.20', 'Питьевая вода', NULL, 'active', '13.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.060.25', 'Промышленная вода', NULL, 'active', '13.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.060.30', 'Сточные воды', NULL, 'active', '13.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.060.45', 'Исследование воды в целом', NULL, 'active', '13.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.060.50', 'Исследование воды для определения содержания химических веществ', NULL, 'active', '13.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.060.60', 'Исследование физических свойств воды', NULL, 'active', '13.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.060.70', 'Исследование биологических свойств воды', NULL, 'active', '13.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.060.99', 'Качество воды, прочие аспекты', NULL, 'active', '13.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.080.01', 'Качество грунта и почвоведение в целом', NULL, 'active', '13.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.080.05', 'Исследование почвы в целом', NULL, 'active', '13.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.080.10', 'Химические характеристики грунтов', NULL, 'active', '13.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.080.20', 'Физические свойства грунтов', NULL, 'active', '13.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.080.30', 'Биологические свойства грунтов', NULL, 'active', '13.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.080.40', 'Гидрологические свойства грунтов', NULL, 'active', '13.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.080.99', 'Качество грунта, прочие аспекты', NULL, 'active', '13.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.220.01', 'Защита от пожара в целом', NULL, 'active', '13.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.220.10', 'Пожаротушение', NULL, 'active', '13.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.220.20', 'Противопожарные средства', NULL, 'active', '13.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.220.40', 'Воспламеняемость, поведение материалов и продуктов при горении', NULL, 'active', '13.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.220.50', 'Огнестойкость строительных материалов и элементов', NULL, 'active', '13.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.220.99', 'Защита от пожаров, прочие аспекты', NULL, 'active', '13.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.340.01', 'Защитные средства в целом', NULL, 'active', '13.340', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.340.10', 'Защитная одежда', NULL, 'active', '13.340', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.340.20', 'Защитные средства для головы', NULL, 'active', '13.340', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.340.30', 'Устройства для защиты органов дыхания', NULL, 'active', '13.340', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.340.40', 'Защитные средства для рук', NULL, 'active', '13.340', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.340.50', 'Защитные средства для ног', NULL, 'active', '13.340', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.340.60', 'Защита от падения и скольжения', NULL, 'active', '13.340', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.340.70', 'Спасательные жилеты, приспособления и вспомогательные средства для удерживания на воде', NULL, 'active', '13.340', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '13.340.99', 'Защитные средства прочие', NULL, 'active', '13.340', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.040.01', 'Линейные и угловые измерения в целом', NULL, 'active', '17.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.040.10', 'Допуски и посадки', NULL, 'active', '17.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.040.20', 'Свойства поверхностей', NULL, 'active', '17.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.040.30', 'Измерительные приборы', NULL, 'active', '17.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.040.40', 'Геометрические характеристики продукции', NULL, 'active', '17.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.040.99', 'Другие стандарты, связанные с линейными и угловыми измерениями', NULL, 'active', '17.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.120.01', 'Измерения параметров потока жидкости в целом', NULL, 'active', '17.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.120.10', 'Поток в закрытых каналах', NULL, 'active', '17.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.120.20', 'Поток в открытых каналах', NULL, 'active', '17.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.140.01', 'Акустические измерения и борьба с шумами в целом', NULL, 'active', '17.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.140.20', 'Шум от машин и оборудования', NULL, 'active', '17.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.140.30', 'Шум от транспорта', NULL, 'active', '17.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.140.50', 'Электроакустика', NULL, 'active', '17.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.140.99', 'Другие стандарты, связанные с акустикой', NULL, 'active', '17.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.180.01', 'Оптика и оптические измерения в целом', NULL, 'active', '17.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.180.20', 'Цветовые и световые измерения', NULL, 'active', '17.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.180.30', 'Оптические измерительные приборы', NULL, 'active', '17.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.180.99', 'Другие стандарты, связанные с оптикой и оптическими измерениями', NULL, 'active', '17.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.200.01', 'Термодинамика в целом', NULL, 'active', '17.200', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.200.10', 'Тепло. Калориметрия', NULL, 'active', '17.200', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.200.20', 'Приборы для измерений температуры', NULL, 'active', '17.200', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.200.99', 'Термодинамика, прочие аспекты', NULL, 'active', '17.200', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.220.01', 'Электричество. Магнетизм. Общие аспекты', NULL, 'active', '17.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.220.20', 'Измерения электрических и магнитных величин', NULL, 'active', '17.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '17.220.99', 'Электричество и магнетизм, прочие аспекты', NULL, 'active', '17.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.040.01', 'Винтовые резьбы в целом', NULL, 'active', '21.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.040.10', 'Метрические резьбы', NULL, 'active', '21.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.040.20', 'Дюймовые резьбы', NULL, 'active', '21.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.040.30', 'Специальные резьбы', NULL, 'active', '21.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.060.01', 'Крепежные изделия в целом', NULL, 'active', '21.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.060.10', 'Болты, винты, шпильки', NULL, 'active', '21.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.060.20', 'Гайки', NULL, 'active', '21.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.060.30', 'Шайбы, контрящие элементы', NULL, 'active', '21.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.060.40', 'Заклепки', NULL, 'active', '21.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.060.50', 'Штифты, гвозди', NULL, 'active', '21.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.060.60', 'Кольца, втулки, манжеты, муфты', NULL, 'active', '21.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.060.70', 'Зажимы и скобы', NULL, 'active', '21.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.060.99', 'Крепежные изделия прочие', NULL, 'active', '21.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.100.01', 'Подшипники в целом', NULL, 'active', '21.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.100.10', 'Подшипники скольжения', NULL, 'active', '21.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.100.20', 'Подшипники качения', NULL, 'active', '21.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.120.01', 'Валы и муфты в целом', NULL, 'active', '21.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.120.10', 'Валы', NULL, 'active', '21.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.120.20', 'Муфты', NULL, 'active', '21.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.120.30', 'Шпонки, шпоночные канавки, шлицы', NULL, 'active', '21.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.120.40', 'Балансировка и балансировочные станки', NULL, 'active', '21.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.120.99', 'Валы и муфты, прочие аспекты', NULL, 'active', '21.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.220.01', 'Гибкие приводы и передачи в целом', NULL, 'active', '21.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.220.10', 'Ременные приводы и их компоненты', NULL, 'active', '21.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.220.20', 'Кабельные или канатные приводы и их компоненты', NULL, 'active', '21.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.220.30', 'Цепные приводы и их компоненты', NULL, 'active', '21.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '21.220.99', 'Гибкие приводы и передачи прочие', NULL, 'active', '21.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.020.01', 'Резервуары для хранения текучих сред в целом', NULL, 'active', '23.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.020.10', 'Стационарные контейнеры и баки', NULL, 'active', '23.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.020.20', 'Сосуды и контейнеры, установленные на транспортных средствах', NULL, 'active', '23.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.020.30', 'Сосуды под давлением', NULL, 'active', '23.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.020.35', 'Газовые баллоны', NULL, 'active', '23.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.020.40', 'Криогенные сосуды', NULL, 'active', '23.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.020.99', 'Резервуары для хранения текучих сред прочие', NULL, 'active', '23.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.040.01', 'Трубопроводы и их компоненты в целом', NULL, 'active', '23.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.040.03', 'Трубопроводы и детали трубопроводов для наземных водопроводов', NULL, 'active', '23.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.040.05', 'Трубопроводы и детали трубопроводов для наземных систем канализации', NULL, 'active', '23.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.040.07', 'Трубопроводы и детали трубопроводов для центрального теплоснабжения', NULL, 'active', '23.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.040.10', 'Чугунные и стальные трубы', NULL, 'active', '23.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.040.15', 'Трубы из цветных металлов', NULL, 'active', '23.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.040.20', 'Пластмассовые трубы', NULL, 'active', '23.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.040.40', 'Металлические фитинги', NULL, 'active', '23.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.040.45', 'Пластмассовые фитинги', NULL, 'active', '23.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.040.50', 'Трубы и фитинги из других материалов', NULL, 'active', '23.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.040.60', 'Фланцы, муфты и соединения', NULL, 'active', '23.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.040.70', 'Рукава и рукава в сборе', NULL, 'active', '23.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.040.80', 'Уплотнения для труб и рукавов в сборе', NULL, 'active', '23.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.040.99', 'Компоненты трубопроводов прочие', NULL, 'active', '23.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.060.01', 'Арматура трубопроводная в целом', NULL, 'active', '23.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.060.10', 'Клапаны запорные', NULL, 'active', '23.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.060.20', 'Краны шаровые и конусные', NULL, 'active', '23.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.060.30', 'Задвижки', NULL, 'active', '23.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.060.40', 'Арматура регулирующая', NULL, 'active', '23.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.060.50', 'Арматура обратная и предохранительная', NULL, 'active', '23.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.060.99', 'Арматура прочая', NULL, 'active', '23.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.100.01', 'Объемные гидроприводы и пневмоприводы в целом', NULL, 'active', '23.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.100.10', 'Насосы и моторы', NULL, 'active', '23.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.100.20', 'Цилиндры', NULL, 'active', '23.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.100.40', 'Трубы и муфты', NULL, 'active', '23.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.100.50', 'Элементы системы управления', NULL, 'active', '23.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.100.60', 'Фильтры, уплотнения и загрязнение жидкостей', NULL, 'active', '23.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '23.100.99', 'Компоненты объемных гидроприводов и пневмоприводов прочие', NULL, 'active', '23.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.040.01', 'Промышленные автоматизированные системы в целом', NULL, 'active', '25.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.040.10', 'Обрабатывающие центры', NULL, 'active', '25.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.040.20', 'Станки с числовым программным управлением', NULL, 'active', '25.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.040.30', 'Промышленные роботы. Манипуляторы', NULL, 'active', '25.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.040.40', 'Измерение и контроль производственного процесса', NULL, 'active', '25.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.040.99', 'Промышленные автоматизированные системы прочие', NULL, 'active', '25.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.060.01', 'Станочные системы в целом', NULL, 'active', '25.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.060.10', 'Модули и другие устройства', NULL, 'active', '25.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.060.20', 'Делительные головки и зажимные приспособления для обрабатываемых деталей и инструментов', NULL, 'active', '25.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.060.99', 'Станочные системы прочие', NULL, 'active', '25.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.080.01', 'Металлорежущие станки в целом', NULL, 'active', '25.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.080.10', 'Токарные станки', NULL, 'active', '25.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.080.20', 'Расточные и фрезерные станки', NULL, 'active', '25.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.080.25', 'Строгальные станки', NULL, 'active', '25.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.080.30', 'Протяжные станки', NULL, 'active', '25.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.080.40', 'Сверлильные станки', NULL, 'active', '25.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.080.50', 'Шлифовальные и полировальные станки', NULL, 'active', '25.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.080.60', 'Пильные станки', NULL, 'active', '25.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.080.99', 'Металлорежущие станки прочие', NULL, 'active', '25.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.100.01', 'Режущие инструменты в целом', NULL, 'active', '25.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.100.10', 'Токарные резцы', NULL, 'active', '25.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.100.20', 'Фрезы', NULL, 'active', '25.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.100.25', 'Режущие инструменты для строгальных и протяжных станков', NULL, 'active', '25.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.100.30', 'Сверла, зенковки, развертки', NULL, 'active', '25.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.100.40', 'Пилы', NULL, 'active', '25.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.100.50', 'Метчики, резьбонарезные плашки', NULL, 'active', '25.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.100.60', 'Напильники', NULL, 'active', '25.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.100.70', 'Абразивы', NULL, 'active', '25.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.100.99', 'Режущие инструменты прочие', NULL, 'active', '25.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.120.01', 'Оборудование для бесстружечной обработки в целом', NULL, 'active', '25.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.120.10', 'Ковочное оборудование. Прессы. Ножницы', NULL, 'active', '25.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.120.20', 'Оборудование для прокатки, экструдирования и протягивания', NULL, 'active', '25.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.120.30', 'Оборудование для литья', NULL, 'active', '25.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.120.40', 'Машины для электрохимической обработки', NULL, 'active', '25.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.120.99', 'Оборудование для бесстружечной обработки прочее', NULL, 'active', '25.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.140.01', 'Ручные инструменты в целом', NULL, 'active', '25.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.140.10', 'Пневматические инструменты', NULL, 'active', '25.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.140.20', 'Электрические инструменты', NULL, 'active', '25.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.140.30', 'Инструменты, управляемые вручную', NULL, 'active', '25.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.140.99', 'Ручные инструменты прочие', NULL, 'active', '25.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.160.01', 'Сварка, пайка твердым и мягким припоем в целом', NULL, 'active', '25.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.160.10', 'Процессы сварки', NULL, 'active', '25.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.160.20', 'Сварочные расходуемые материалы', NULL, 'active', '25.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.160.30', 'Сварочное оборудование', NULL, 'active', '25.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.160.40', 'Сварочные швы и сварка', NULL, 'active', '25.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.160.50', 'Пайка твердым и мягким припоем', NULL, 'active', '25.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.180.01', 'Промышленные печи в целом', NULL, 'active', '25.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.180.10', 'Электрические печи', NULL, 'active', '25.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.180.20', 'Топливные печи', NULL, 'active', '25.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.220.01', 'Обработка и покрытие поверхности в целом', NULL, 'active', '25.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.220.10', 'Подготовка поверхности', NULL, 'active', '25.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.220.20', 'Обработка поверхности', NULL, 'active', '25.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.220.40', 'Металлические покрытия', NULL, 'active', '25.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.220.50', 'Эмали', NULL, 'active', '25.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.220.60', 'Органические покрытия', NULL, 'active', '25.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '25.220.99', 'Виды обработки и покрытий прочие', NULL, 'active', '25.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '27.060.01', 'Горелки и котлы в целом', NULL, 'active', '27.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '27.060.10', 'Горелки на жидком и твердом топливе', NULL, 'active', '27.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '27.060.20', 'Газовые горелки', NULL, 'active', '27.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '27.060.30', 'Котлы и теплообменники', NULL, 'active', '27.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '27.120.01', 'Атомная энергетика в целом', NULL, 'active', '27.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '27.120.10', 'Реакторная техника', NULL, 'active', '27.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '27.120.20', 'Атомные электростанции. Безопасность', NULL, 'active', '27.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '27.120.30', 'Делящиеся ядерные вещества и технология получения ядерного топлива', NULL, 'active', '27.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '27.120.99', 'Атомная энергетика, прочие аспекты', NULL, 'active', '27.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.035.01', 'Изоляционные материалы в целом', NULL, 'active', '29.035', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.035.10', 'Бумажные и картонные изоляционные материалы', NULL, 'active', '29.035', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.035.20', 'Пластмассовые и резиновые изоляционные материалы', NULL, 'active', '29.035', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.035.30', 'Стеклянные и керамические изоляционные материалы', NULL, 'active', '29.035', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.035.50', 'Материалы на основе слюды', NULL, 'active', '29.035', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.035.60', 'Лакоткани', NULL, 'active', '29.035', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.035.99', 'Изоляционные материалы прочие', NULL, 'active', '29.035', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.040.01', 'Изоляционные жидкости и газы (текучие среды) в целом', NULL, 'active', '29.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.040.10', 'Изоляционные масла', NULL, 'active', '29.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.040.20', 'Изоляционные газы', NULL, 'active', '29.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.040.99', 'Изоляционные жидкости и газы (текучие среды) прочие', NULL, 'active', '29.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.060.01', 'Электрические провода и кабели в целом', NULL, 'active', '29.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.060.10', 'Провода', NULL, 'active', '29.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.060.20', 'Кабели', NULL, 'active', '29.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.080.01', 'Электрическая изоляция в целом', NULL, 'active', '29.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.080.10', 'Изоляторы', NULL, 'active', '29.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.080.20', 'Вводы', NULL, 'active', '29.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.080.30', 'Изоляционные системы', NULL, 'active', '29.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.080.99', 'Изоляция, прочие аспекты', NULL, 'active', '29.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.100.01', 'Компоненты электрооборудования в целом', NULL, 'active', '29.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.060.50', 'Соли', NULL, 'active', '71.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.100.10', 'Магнитные компоненты', NULL, 'active', '29.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.100.20', 'Электрические и электромеханические компоненты', NULL, 'active', '29.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.100.99', 'Компоненты электрооборудования прочие', NULL, 'active', '29.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.120.01', 'Электрическая арматура в целом', NULL, 'active', '29.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.120.10', 'Кабелепроводы', NULL, 'active', '29.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.120.20', 'Соединительные устройства', NULL, 'active', '29.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.120.30', 'Вилки, розетки, соединители', NULL, 'active', '29.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.120.40', 'Переключатели', NULL, 'active', '29.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.120.50', 'Плавкие предохранители и другие защитные устройства при перегрузках', NULL, 'active', '29.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.120.70', 'Реле', NULL, 'active', '29.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.120.99', 'Электрическая арматура прочая', NULL, 'active', '29.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.130.01', 'Коммутационная аппаратура и аппаратура управления в целом', NULL, 'active', '29.130', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.130.10', 'Высоковольтное оборудование, коммутационная аппаратура и аппаратура управления', NULL, 'active', '29.130', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.130.20', 'Низковольтная коммутационная аппаратура и аппаратура управления', NULL, 'active', '29.130', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.130.99', 'Коммутационная аппаратура и аппаратура управления прочая', NULL, 'active', '29.130', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.140.01', 'Лампы в целом', NULL, 'active', '29.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.140.10', 'Цоколи и патроны для ламп', NULL, 'active', '29.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.140.20', 'Лампы накаливания', NULL, 'active', '29.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.140.30', 'Флуоресцентные лампы. Разрядные лампы', NULL, 'active', '29.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.140.40', 'Светильники', NULL, 'active', '29.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.140.50', 'Системы осветительных электроустановок', NULL, 'active', '29.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.140.99', 'Лампы, прочие аспекты', NULL, 'active', '29.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.160.01', 'Машины вращающиеся в целом', NULL, 'active', '29.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.160.10', 'Компоненты машины вращающиеся', NULL, 'active', '29.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.160.20', 'Генераторы', NULL, 'active', '29.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.160.30', 'Двигатели', NULL, 'active', '29.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.160.40', 'Генераторные агрегаты', NULL, 'active', '29.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.160.99', 'Машины вращающиеся, прочие аспекты', NULL, 'active', '29.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.220.01', 'Гальванические элементы и батареи в целом', NULL, 'active', '29.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.220.10', 'Первичные элементы и батареи', NULL, 'active', '29.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.220.20', 'Кислотные аккумуляторы и аккумуляторные батареи', NULL, 'active', '29.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.220.30', 'Щелочные аккумуляторы и аккумуляторные батареи', NULL, 'active', '29.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.220.99', 'Элементы и батареи прочие', NULL, 'active', '29.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.240.01', 'Сети электропередачи и распределительные сети в целом', NULL, 'active', '29.240', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.240.10', 'Подстанции. Защитные разрядники', NULL, 'active', '29.240', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.240.20', 'Линии электропередачи и распределительные линии', NULL, 'active', '29.240', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.240.30', 'Аппаратура управления для электрических силовых систем', NULL, 'active', '29.240', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.240.99', 'Оборудование, связанное с сетями электропередачи и распределительными сетями', NULL, 'active', '29.240', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.260.01', 'Электрическое оборудование для работы в особых условиях в целом', NULL, 'active', '29.260', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.260.10', 'Электрические установки для эксплуатации на открытом воздухе', NULL, 'active', '29.260', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.260.20', 'Электрическое оборудование для взрывоопасной атмосферы', NULL, 'active', '29.260', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '29.260.99', 'Электрическое оборудование для работы в особых условиях прочее', NULL, 'active', '29.260', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.040.01', 'Резисторы в целом', NULL, 'active', '31.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.040.10', 'Постоянные резисторы', NULL, 'active', '31.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.040.20', 'Потенциометры, переменные резисторы', NULL, 'active', '31.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.040.30', 'Термисторы', NULL, 'active', '31.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.040.99', 'Резисторы прочие', NULL, 'active', '31.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.060.01', 'Конденсаторы в целом', NULL, 'active', '31.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.060.10', 'Конденсаторы постоянной емкости', NULL, 'active', '31.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.060.20', 'Керамические и слюдяные конденсаторы', NULL, 'active', '31.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.060.30', 'Бумажные и пластмассовые конденсаторы', NULL, 'active', '31.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.060.40', 'Танталовые электролитические конденсаторы', NULL, 'active', '31.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.060.50', 'Алюминиевые электролитические конденсаторы', NULL, 'active', '31.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.060.60', 'Конденсаторы переменной емкости', NULL, 'active', '31.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.060.70', 'Силовые конденсаторы', NULL, 'active', '31.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.060.99', 'Конденсаторы прочие', NULL, 'active', '31.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.080.01', 'Полупроводниковые приборы в целом', NULL, 'active', '31.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.080.10', 'Диоды', NULL, 'active', '31.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.080.20', 'Тиристоры', NULL, 'active', '31.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.080.30', 'Транзисторы', NULL, 'active', '31.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.080.99', 'Полупроводниковые приборы прочие', NULL, 'active', '31.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.220.01', 'Электромеханические компоненты в целом', NULL, 'active', '31.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.220.10', 'Штепсельные разъемы. Соединители', NULL, 'active', '31.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.220.20', 'Переключатели', NULL, 'active', '31.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '31.220.99', 'Электромеханические компоненты прочие', NULL, 'active', '31.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.040.01', 'Телекоммуникационные системы в целом', NULL, 'active', '33.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.040.20', 'Системы передачи', NULL, 'active', '33.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.040.30', 'Системы коммутации и сигнализации', NULL, 'active', '33.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.040.35', 'Телефонные сети', NULL, 'active', '33.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.040.40', 'Сети передачи данных', NULL, 'active', '33.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.040.50', 'Линии, соединения и цепи', NULL, 'active', '33.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.040.60', 'Силовые линии телекоммуникаций', NULL, 'active', '33.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.040.99', 'Оборудование для телекоммуникационных систем прочее', NULL, 'active', '33.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.050.01', 'Телекоммуникационная оконечная аппаратура в целом', NULL, 'active', '33.050', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.050.10', 'Телефонная аппаратура', NULL, 'active', '33.050', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.050.20', 'Пейджинговая аппаратура', NULL, 'active', '33.050', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.050.30', 'Аппаратура для телексов, телетекстов, телефаксов', NULL, 'active', '33.050', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.050.99', 'Телекоммуникационная оконечная аппаратура прочая', NULL, 'active', '33.050', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.060.01', 'Радиосвязь в целом', NULL, 'active', '33.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.060.20', 'Приемная и передающая аппаратура', NULL, 'active', '33.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.060.30', 'Радиорелейные и стационарные спутниковые системы связи', NULL, 'active', '33.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.060.40', 'Кабельные распределительные системы', NULL, 'active', '33.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.060.99', 'Оборудование для радиосвязи прочее', NULL, 'active', '33.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.070.01', 'Подвижные службы в целом', NULL, 'active', '33.070', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.070.10', 'Наземная линейная радиосвязь (TETRA)', NULL, 'active', '33.070', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.070.20', 'Пейджинговые системы', NULL, 'active', '33.070', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.070.30', 'Цифровые усиленные беспроводные телекоммуникации (DECT)', NULL, 'active', '33.070', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.070.40', 'Спутники связи', NULL, 'active', '33.070', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.070.50', 'Глобальная система радиосвязи с подвижными объектами (GSM)', NULL, 'active', '33.070', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.070.99', 'Подвижные системы прочие', NULL, 'active', '33.070', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.100.01', 'Электромагнитная совместимость в целом', NULL, 'active', '33.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.100.10', 'Излучение', NULL, 'active', '33.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.100.20', 'Защищенность', NULL, 'active', '33.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.100.99', 'Электромагнитная совместимость, прочие аспекты', NULL, 'active', '33.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.120.01', 'Компоненты и вспомогательные приспособления в целом', NULL, 'active', '33.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.120.10', 'Коаксиальные кабели. Волноводы', NULL, 'active', '33.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.120.20', 'Провода и симметричные кабели', NULL, 'active', '33.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.120.30', 'Радиочастотные соединители', NULL, 'active', '33.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.120.40', 'Антенны', NULL, 'active', '33.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.120.99', 'Компоненты и вспомогательные приспособления прочие', NULL, 'active', '33.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.160.01', 'Аудио-, видео- и аудиовизуальная техника в целом', NULL, 'active', '33.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.160.10', 'Усилители', NULL, 'active', '33.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.160.20', 'Радиоприемники', NULL, 'active', '33.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.160.25', 'Телевизионные приемники', NULL, 'active', '33.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.160.30', 'Аудиосистемы', NULL, 'active', '33.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.160.40', 'Видеосистемы', NULL, 'active', '33.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.160.50', 'Вспомогательные устройства', NULL, 'active', '33.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.160.60', 'Системы мультимедиа и оборудование телеконференцсвязи', NULL, 'active', '33.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.160.99', 'Аудио-, видео- и аудиовизуальное оборудование прочее', NULL, 'active', '33.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.180.01', 'Волоконно-оптические системы в целом', NULL, 'active', '33.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.180.10', 'Волокна и кабели', NULL, 'active', '33.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '37.100.20', 'Материалы для графической техники', NULL, 'active', '37.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.180.20', 'Волоконно-оптические межсоединительные устройства', NULL, 'active', '33.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.180.30', 'Оптические усилители', NULL, 'active', '33.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '33.180.99', 'Волоконно-оптическое оборудование прочее', NULL, 'active', '33.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.040.01', 'Кодирование информации в целом', NULL, 'active', '35.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.040.10', 'Кодирование наборов знаков', NULL, 'active', '35.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.040.30', 'Кодирование графической и фотографической информации', NULL, 'active', '35.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.040.40', 'Кодирование аудио-, видео-, мультимедийной и гипермедийной информации', NULL, 'active', '35.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.040.50', 'Технологии автоматической идентификации и сбора данных', NULL, 'active', '35.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.040.99', 'Стандарты по кодированию информации прочие', NULL, 'active', '35.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.100.01', 'Взаимосвязь открытых систем в целом', NULL, 'active', '35.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.100.05', 'Многоуровневые прикладные системы', NULL, 'active', '35.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.100.10', 'Физический уровень', NULL, 'active', '35.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.100.20', 'Уровень звена данных', NULL, 'active', '35.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.100.30', 'Сетевой уровень', NULL, 'active', '35.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.100.40', 'Транспортный уровень', NULL, 'active', '35.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.100.50', 'Сеансовый уровень', NULL, 'active', '35.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.100.60', 'Уровень представления', NULL, 'active', '35.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.100.70', 'Прикладной уровень', NULL, 'active', '35.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.220.01', 'Запоминающие устройства в целом', NULL, 'active', '35.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.220.10', 'Бумажные карты и ленты', NULL, 'active', '35.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.220.20', 'Магнитные запоминающие устройства в целом', NULL, 'active', '35.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.220.21', 'Магнитные диски', NULL, 'active', '35.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.220.22', 'Магнитные ленты', NULL, 'active', '35.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.220.23', 'Кассеты и картриджи для магнитных лент', NULL, 'active', '35.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.220.30', 'Оптические запоминающие устройства', NULL, 'active', '35.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.220.99', 'Запоминающие устройства прочие', NULL, 'active', '35.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.240.01', 'Применение информационных технологий в целом', NULL, 'active', '35.240', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.240.10', 'Автоматизированное проектирование', NULL, 'active', '35.240', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.240.15', 'Карты идентификационные. Карты с микросхемами. Биометрия', NULL, 'active', '35.240', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.240.20', 'Применение приложений ИТ в работе учреждений', NULL, 'active', '35.240', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.240.30', 'Применение приложений ИТ в области информации, документации и в издательском деле', NULL, 'active', '35.240', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.240.40', 'Применение приложений ИТ в банковском деле', NULL, 'active', '35.240', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.240.50', 'Применение приложений ИТ в промышленности', NULL, 'active', '35.240', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.240.60', 'Приложения ИТ на транспорте', NULL, 'active', '35.240', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.240.63', 'Приложения ИТ в торговле', NULL, 'active', '35.240', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.240.67', 'Приложения ИТ в строительстве зданий и сооружений', NULL, 'active', '35.240', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.240.68', 'Приложения ИТ в сельском хозяйстве', NULL, 'active', '35.240', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.240.69', 'Приложения ИТ в почтовых услугах', NULL, 'active', '35.240', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.240.70', 'Применение приложений ИТ в науке', NULL, 'active', '35.240', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.240.80', 'Применение приложений ИТ в здравоохранении', NULL, 'active', '35.240', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.240.90', 'Приложения ИТ в образовании', NULL, 'active', '35.240', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.240.95', 'Приложения Интернет', NULL, 'active', '35.240', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '35.240.99', 'Применение приложений ИТ в других областях', NULL, 'active', '35.240', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '37.040.01', 'Фотография в целом', NULL, 'active', '37.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '37.040.10', 'Фотографическое оборудование. Проекторы', NULL, 'active', '37.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '37.040.20', 'Фотографическая бумага, пленки и платы. Картриджи', NULL, 'active', '37.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '37.040.25', 'Пленки для радиографии', NULL, 'active', '37.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '37.040.30', 'Фотохимикаты', NULL, 'active', '37.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '37.040.99', 'Фотография, прочие аспекты', NULL, 'active', '37.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '37.060.01', 'Кинематография в целом', NULL, 'active', '37.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '37.060.10', 'Кинематографическое оборудование', NULL, 'active', '37.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '37.060.20', 'Кинематографические пленки. Картриджи', NULL, 'active', '37.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '37.060.99', 'Кинематография, прочие аспекты', NULL, 'active', '37.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '37.100.01', 'Технология полиграфии в целом', NULL, 'active', '37.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '37.100.10', 'Оборудование для репродуцирования', NULL, 'active', '37.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '37.100.99', 'Технология полиграфии, прочие аспекты', NULL, 'active', '37.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '39.040.01', 'Часовое дело в целом', NULL, 'active', '39.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '39.040.10', 'Наручные и карманные часы', NULL, 'active', '39.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '39.040.20', 'Часы', NULL, 'active', '39.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '39.040.99', 'Приборы для измерения времени прочие', NULL, 'active', '39.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.040.01', 'Системы дорожно-транспортных средств в целом', NULL, 'active', '43.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.040.10', 'Электрическое и электронное оборудование', NULL, 'active', '43.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.040.15', 'Информационное оборудование. Встроенные компьютерные системы', NULL, 'active', '43.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.040.20', 'Осветительные, сигнальные устройства и устройства оповещения', NULL, 'active', '43.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.040.30', 'Индикаторы и контрольные приборы', NULL, 'active', '43.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.040.40', 'Тормозные системы', NULL, 'active', '43.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.040.50', 'Трансмиссии, подвески', NULL, 'active', '43.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.040.60', 'Кузова и их компоненты', NULL, 'active', '43.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.040.65', 'Системы нанесения защитного слоя и сушки', NULL, 'active', '43.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.040.70', 'Сцепные устройства', NULL, 'active', '43.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.040.80', 'Защита от столкновений и ограничительные системы', NULL, 'active', '43.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.040.99', 'Системы дорожно-транспортных средств прочие', NULL, 'active', '43.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.060.01', 'Двигатели внутреннего сгорания для дорожно-транспортных средств в целом', NULL, 'active', '43.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.060.10', 'Блок цилиндров и его компоненты', NULL, 'active', '43.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.060.20', 'Системы наддува и системы труб для воздуха и выхлопных газов', NULL, 'active', '43.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.060.30', 'Системы охлаждения. Смазочные системы', NULL, 'active', '43.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.060.40', 'Топливные системы', NULL, 'active', '43.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.060.50', 'Электрооборудование и электронное оборудование. Системы контроля', NULL, 'active', '43.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.060.99', 'Компоненты и системы двигателей внутреннего сгорания прочие', NULL, 'active', '43.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.080.01', 'Грузовые транспортные средства в целом', NULL, 'active', '43.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.080.10', 'Грузовики и прицепы', NULL, 'active', '43.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.080.20', 'Автобусы', NULL, 'active', '43.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '43.080.99', 'Грузовые транспортные средства прочие', NULL, 'active', '43.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '45.060.01', 'Подвижной состав железных дорог в целом', NULL, 'active', '45.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '45.060.10', 'Тяговый состав', NULL, 'active', '45.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '45.060.20', 'Прицепной состав', NULL, 'active', '45.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '47.020.01', 'Судостроение и морские сооружения, общие аспекты', NULL, 'active', '47.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '47.020.05', 'Материалы и компоненты для судостроения', NULL, 'active', '47.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '47.020.10', 'Корпуса и их конструктивные элементы', NULL, 'active', '47.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '47.020.20', 'Судовые двигатели и движительные системы', NULL, 'active', '47.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '47.020.30', 'Системы трубопроводов', NULL, 'active', '47.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '47.020.40', 'Подъемное и погрузочно-разгрузочное оборудование', NULL, 'active', '47.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '47.020.50', 'Палубное оборудование и установки', NULL, 'active', '47.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '47.020.60', 'Электрооборудование судов и морских сооружений', NULL, 'active', '47.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '47.020.70', 'Навигационное оборудование и приборы управления', NULL, 'active', '47.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '47.020.80', 'Помещения для пассажиров', NULL, 'active', '47.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '47.020.85', 'Помещения для груза', NULL, 'active', '47.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '47.020.90', 'Судовые системы вентиляции, кондиционирования воздуха и обогрева', NULL, 'active', '47.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '47.020.99', 'Судостроение и морские сооружения, прочие аспекты', NULL, 'active', '47.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.025.01', 'Материалы для авиационно-космических конструкций в целом', NULL, 'active', '49.025', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.025.05', 'Сплавы на железной основе в целом', NULL, 'active', '49.025', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.025.10', 'Стали', NULL, 'active', '49.025', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.025.15', 'Сплавы цветных металлов в целом', NULL, 'active', '49.025', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.025.20', 'Алюминий', NULL, 'active', '49.025', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.025.30', 'Титан', NULL, 'active', '49.025', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.025.40', 'Резина и пластмассы', NULL, 'active', '49.025', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.025.50', 'Клеи', NULL, 'active', '49.025', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.025.60', 'Текстиль', NULL, 'active', '49.025', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.025.99', 'Материалы прочие', NULL, 'active', '49.025', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.030.01', 'Крепежные изделия в целом', NULL, 'active', '49.030', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.030.10', 'Винтовые резьбы', NULL, 'active', '49.030', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.030.20', 'Болты, винты, шпильки', NULL, 'active', '49.030', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.030.30', 'Гайки', NULL, 'active', '49.030', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.030.40', 'Штифты, гвозди', NULL, 'active', '49.030', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.030.50', 'Шайбы и другие фиксирующие элементы', NULL, 'active', '49.030', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.030.60', 'Заклепки', NULL, 'active', '49.030', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '49.030.99', 'Крепежные изделия прочие', NULL, 'active', '49.030', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '53.020.01', 'Подъемные приспособления в целом', NULL, 'active', '53.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '53.020.20', 'Краны', NULL, 'active', '53.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '53.020.30', 'Вспомогательные приспособления для подъемного оборудования', NULL, 'active', '53.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '53.020.99', 'Подъемное оборудование прочее', NULL, 'active', '53.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '53.040.01', 'Подъемно-транспортное оборудование непрерывного действия в целом', NULL, 'active', '53.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '53.040.10', 'Конвейеры', NULL, 'active', '53.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '53.040.20', 'Компоненты для конвейеров', NULL, 'active', '53.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '53.040.30', 'Пневмотранспорт и его компоненты', NULL, 'active', '53.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '53.040.99', 'Подъемно-транспортное оборудование непрерывного действия прочее', NULL, 'active', '53.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '55.180.01', 'Размещение грузов для перевозок в целом', NULL, 'active', '55.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '55.180.10', 'Контейнеры общего назначения', NULL, 'active', '55.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '55.180.20', 'Поддоны общего назначения', NULL, 'active', '55.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '55.180.30', 'Контейнеры, поддоны и сетки для воздушных перевозок', NULL, 'active', '55.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '55.180.40', 'Укомплектованная заполненная транспортная тара', NULL, 'active', '55.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '55.180.99', 'Размещение грузов для перевозок, прочие аспекты', NULL, 'active', '55.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.060.01', 'Текстильные волокна в целом', NULL, 'active', '59.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.060.10', 'Натуральные волокна', NULL, 'active', '59.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.060.20', 'Искусственные волокна', NULL, 'active', '59.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.060.30', 'Минеральные и металлические волокна', NULL, 'active', '59.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.060.99', 'Текстильные волокна прочие', NULL, 'active', '59.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.080.01', 'Текстиль в целом', NULL, 'active', '59.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.080.20', 'Пряжа', NULL, 'active', '59.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.080.30', 'Текстильные изделия', NULL, 'active', '59.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.080.40', 'Ткани с покрытием', NULL, 'active', '59.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.080.50', 'Веревки', NULL, 'active', '59.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.080.70', 'Геотекстиль', NULL, 'active', '59.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.080.80', 'Интеллектуальные текстильные материалы', NULL, 'active', '59.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.080.99', 'Изделия текстильной промышленности прочие', NULL, 'active', '59.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.100.01', 'Материалы для усиления композитов в целом', NULL, 'active', '59.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.100.10', 'Текстильные стекловолокнистые материалы', NULL, 'active', '59.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.100.20', 'Материалы из углеродного волокна', NULL, 'active', '59.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.100.30', 'Материалы из арамидного волокна', NULL, 'active', '59.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.100.99', 'Материалы для усиления композитов прочие', NULL, 'active', '59.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.120.01', 'Текстильные машины в целом', NULL, 'active', '59.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.120.10', 'Прядильные, крутильные и текстурирующие машины', NULL, 'active', '59.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.120.20', 'Мотальные машины и оборудование', NULL, 'active', '59.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.120.30', 'Ткацкие станки и машины', NULL, 'active', '59.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.120.40', 'Трикотажные машины', NULL, 'active', '59.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.120.50', 'Красильное и отделочное оборудование', NULL, 'active', '59.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.120.99', 'Текстильные машины прочие', NULL, 'active', '59.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.140.01', 'Технология производства кожи в целом', NULL, 'active', '59.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.140.10', 'Процессы и вспомогательные материалы', NULL, 'active', '59.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.140.20', 'Невыделанные шкуры, полуфабрикаты, голье', NULL, 'active', '59.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.140.30', 'Кожи и меха', NULL, 'active', '59.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.140.35', 'Кожгалантерейные изделия', NULL, 'active', '59.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.140.40', 'Машины и оборудование для производства кожи мехов', NULL, 'active', '59.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '59.140.99', 'Технология производства кожи, прочие аспекты', NULL, 'active', '59.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.020.01', 'Земледелие и лесоводство в целом', NULL, 'active', '65.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.020.20', 'Растениеводство', NULL, 'active', '65.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.020.30', 'Животноводство и селекция животных', NULL, 'active', '65.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.020.40', 'Озеленение и лесоводство', NULL, 'active', '65.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.020.99', 'Земледелие и лесоводство, прочие аспекты', NULL, 'active', '65.020', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.040.01', 'Сельскохозяйственные постройки и установки в целом', NULL, 'active', '65.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.040.10', 'Постройки, установки и оборудование для домашнего скота', NULL, 'active', '65.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.040.20', 'Постройки и установки для переработки и хранения сельскохозяйственной продукции', NULL, 'active', '65.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.040.30', 'Теплицы и другие сооружения', NULL, 'active', '65.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.040.99', 'Сельскохозяйственные постройки и установки, прочие аспекты', NULL, 'active', '65.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.060.01', 'Сельскохозяйственные машины и оборудование в целом', NULL, 'active', '65.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.060.10', 'Сельскохозяйственные тракторы и прицепы', NULL, 'active', '65.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.060.20', 'Орудия для обработки почвы', NULL, 'active', '65.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.060.25', 'Оборудование для хранения, приготовления и внесения удобрений', NULL, 'active', '65.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.060.30', 'Оборудование для сева и посадок', NULL, 'active', '65.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.060.35', 'Ирригационное и дренажное оборудование', NULL, 'active', '65.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.060.40', 'Оборудование для ухода за растениями', NULL, 'active', '65.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.060.50', 'Оборудование для уборки урожая', NULL, 'active', '65.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.060.60', 'Оборудование для виноградарства и виноделия', NULL, 'active', '65.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.060.70', 'Садово-парковый инвентарь', NULL, 'active', '65.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.060.80', 'Оборудование для лесного хозяйства', NULL, 'active', '65.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.060.99', 'Сельскохозяйственные машины и оборудование прочие', NULL, 'active', '65.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.100.01', 'Пестициды и другие агрохимикаты в целом', NULL, 'active', '65.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.100.10', 'Инсектициды', NULL, 'active', '65.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.100.20', 'Гербициды', NULL, 'active', '65.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.100.30', 'Фунгициды', NULL, 'active', '65.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '65.100.99', 'Пестициды и агрохимикаты прочие', NULL, 'active', '65.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.080.01', 'Фрукты, овощи и продукты их переработки в целом', NULL, 'active', '67.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.080.10', 'Фрукты и продукты их переработки', NULL, 'active', '67.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.080.20', 'Овощи и продукты их переработки', NULL, 'active', '67.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.100.01', 'Молоко и молочные продукты в целом', NULL, 'active', '67.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.100.10', 'Молоко и продукты из переработанного молока', NULL, 'active', '67.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.100.20', 'Масло', NULL, 'active', '67.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.100.30', 'Сыр', NULL, 'active', '67.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.100.40', 'Мороженое и замороженные кондитерские изделия', NULL, 'active', '67.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.100.99', 'Молочные продукты прочие', NULL, 'active', '67.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.120.01', 'Продукты животного происхождения в целом', NULL, 'active', '67.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.120.10', 'Мясо и мясные продукты', NULL, 'active', '67.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.120.20', 'Птица и яйца', NULL, 'active', '67.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.120.30', 'Рыба и рыбные продукты', NULL, 'active', '67.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.120.99', 'Продукты животного происхождения прочие', NULL, 'active', '67.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.140.10', 'Чай', NULL, 'active', '67.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.140.20', 'Кофе и заменители кофе', NULL, 'active', '67.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.140.30', 'Какао', NULL, 'active', '67.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.160.01', 'Напитки в целом', NULL, 'active', '67.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.160.10', 'Алкогольные напитки', NULL, 'active', '67.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.160.20', 'Безалкогольные напитки', NULL, 'active', '67.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.180.10', 'Сахар и продукты из сахара', NULL, 'active', '67.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.180.20', 'Крахмал и продукты из него', NULL, 'active', '67.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.200.10', 'Животные и растительные масла и жиры', NULL, 'active', '67.200', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.200.20', 'Семена масличных культур', NULL, 'active', '67.200', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.220.10', 'Пряности и приправы', NULL, 'active', '67.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '67.220.20', 'Пищевые добавки', NULL, 'active', '67.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.040.01', 'Аналитическая химия в целом', NULL, 'active', '71.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.040.10', 'Химические лаборатории. Лабораторное оборудование', NULL, 'active', '71.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.040.20', 'Лабораторная посуда и сопутствующая аппаратура', NULL, 'active', '71.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.040.30', 'Химические реактивы', NULL, 'active', '71.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.040.40', 'Химический анализ', NULL, 'active', '71.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.040.50', 'Физико-химические методы анализа', NULL, 'active', '71.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.040.99', 'Аналитическая химия, прочие аспекты', NULL, 'active', '71.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.060.01', 'Неорганические химические вещества в целом', NULL, 'active', '71.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.060.10', 'Химические элементы', NULL, 'active', '71.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.060.99', 'Неорганические химические вещества прочие', NULL, 'active', '71.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.080.01', 'Органические химические вещества в целом', NULL, 'active', '71.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.080.10', 'Алифатические углеводороды', NULL, 'active', '71.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.080.15', 'Ароматические углеводороды', NULL, 'active', '71.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.080.20', 'Галогензамещенные углеводороды', NULL, 'active', '71.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.080.30', 'Органические азотные соединения', NULL, 'active', '71.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.080.40', 'Органические кислоты', NULL, 'active', '71.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.080.50', 'Ангидриды', NULL, 'active', '71.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.080.60', 'Спирты. Эфиры', NULL, 'active', '71.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.080.70', 'Сложные эфиры', NULL, 'active', '71.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.080.80', 'Альдегиды и кетоны', NULL, 'active', '71.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.080.90', 'Фенолы', NULL, 'active', '71.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.080.99', 'Органические химические вещества прочие', NULL, 'active', '71.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.100.01', 'Продукты химической промышленности в целом', NULL, 'active', '71.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.100.10', 'Материалы для производства алюминия', NULL, 'active', '71.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.100.20', 'Газы промышленного применения', NULL, 'active', '71.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.100.30', 'Взрывчатые вещества. Пиротехника и фейерверки', NULL, 'active', '71.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.100.35', 'Химикаты для промышленной и бытовой дезинфекции', NULL, 'active', '71.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.100.40', 'Поверхностно-активные вещества', NULL, 'active', '71.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.100.45', 'Холодильные агенты и антифризы', NULL, 'active', '71.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.100.50', 'Химикаты для защиты древесины', NULL, 'active', '71.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.100.55', 'Силиконы', NULL, 'active', '71.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.100.60', 'Эфирные масла', NULL, 'active', '71.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.100.70', 'Косметика, туалетные принадлежности', NULL, 'active', '71.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.100.80', 'Химикаты для очистки воды', NULL, 'active', '71.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.100.99', 'Продукты химической промышленности прочие', NULL, 'active', '71.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.120.01', 'Оборудование для химической промышленности в целом', NULL, 'active', '71.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.120.10', 'Реакторы и их компоненты', NULL, 'active', '71.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.120.20', 'Аппараты колонного типа', NULL, 'active', '71.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.120.30', 'Теплообменники', NULL, 'active', '71.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '71.120.99', 'Оборудование для химической промышленности прочее', NULL, 'active', '71.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '73.060.01', 'Рудные минералы в целом', NULL, 'active', '73.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '73.060.10', 'Железные руды', NULL, 'active', '73.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '73.060.20', 'Марганцевые руды', NULL, 'active', '73.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '73.060.30', 'Хромовые руды', NULL, 'active', '73.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '73.060.40', 'Алюминиевые руды', NULL, 'active', '73.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '73.060.99', 'Рудные минералы прочие', NULL, 'active', '73.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '73.100.01', 'Горное оборудование в целом', NULL, 'active', '73.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '73.100.10', 'Оборудование для проходки и крепления горных выработок, установки тюбинговой крепи', NULL, 'active', '73.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '73.100.20', 'Оборудование для вентиляции, кондиционирования воздуха и освещения', NULL, 'active', '73.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '73.100.30', 'Оборудование для бурения и выемки грунта', NULL, 'active', '73.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '73.100.40', 'Оборудование для откатки и подъема', NULL, 'active', '73.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '73.100.99', 'Горное оборудование прочее', NULL, 'active', '73.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '75.160.01', 'Топливо в целом', NULL, 'active', '75.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '75.160.10', 'Твердое топливо', NULL, 'active', '75.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '75.160.20', 'Жидкое топливо', NULL, 'active', '75.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '75.160.30', 'Газообразное топливо', NULL, 'active', '75.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '75.160.40', 'Биотопливо', NULL, 'active', '75.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '75.180.01', 'Оборудование для нефтяной и газовой промышленности в целом', NULL, 'active', '75.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '75.180.10', 'Оборудование для разведки, бурения и добычи', NULL, 'active', '75.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '75.180.20', 'Технологическое оборудование', NULL, 'active', '75.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '75.180.30', 'Объемные измерения и средства для этих измерений', NULL, 'active', '75.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '75.180.99', 'Оборудование для нефтяной и газовой промышленности прочее', NULL, 'active', '75.180', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.040.01', 'Испытания металлов в целом', NULL, 'active', '77.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.040.10', 'Механические испытания металлов', NULL, 'active', '77.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.040.20', 'Неразрушающие испытания металлов', NULL, 'active', '77.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.040.30', 'Химический анализ металлов', NULL, 'active', '77.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.040.99', 'Методы испытания металлов прочие', NULL, 'active', '77.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.080.01', 'Черные металлы в целом', NULL, 'active', '77.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.080.10', 'Чугуны', NULL, 'active', '77.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.080.20', 'Стали', NULL, 'active', '77.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.120.01', 'Цветные металлы в целом', NULL, 'active', '77.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.120.10', 'Алюминий и алюминиевые сплавы', NULL, 'active', '77.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.120.20', 'Магний и магниевые сплавы', NULL, 'active', '77.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.120.30', 'Медь и медные сплавы', NULL, 'active', '77.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.120.40', 'Никель, хром и их сплавы', NULL, 'active', '77.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.120.50', 'Титан и титановые сплавы', NULL, 'active', '77.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.120.60', 'Свинец, цинк, олово и их сплавы', NULL, 'active', '77.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.120.70', 'Кадмий, кобальт и их сплавы', NULL, 'active', '77.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.120.99', 'Цветные металлы и их сплавы прочие', NULL, 'active', '77.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.140.01', 'Продукция из чугуна и стали в целом', NULL, 'active', '77.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.140.10', 'Термообрабатываемые стали', NULL, 'active', '77.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.140.15', 'Стали для армирования бетона', NULL, 'active', '77.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.140.20', 'Нержавеющие стали', NULL, 'active', '77.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.140.25', 'Пружинные стали', NULL, 'active', '77.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.140.30', 'Стали для работы под давлением', NULL, 'active', '77.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.140.35', 'Инструментальные стали', NULL, 'active', '77.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.140.40', 'Стали со специальными магнитными свойствами', NULL, 'active', '77.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.140.45', 'Нелегированные стали', NULL, 'active', '77.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.140.50', 'Стальной листовой прокат и полуфабрикаты', NULL, 'active', '77.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.140.60', 'Стальные прутки и катанка', NULL, 'active', '77.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.140.65', 'Стальная проволока, проволочные канаты и звеньевые цепи', NULL, 'active', '77.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.140.70', 'Стальные профили', NULL, 'active', '77.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.140.75', 'Стальные трубы и трубки специального назначения', NULL, 'active', '77.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.140.80', 'Чугунные и стальные отливки', NULL, 'active', '77.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.140.85', 'Чугунные и стальные поковки', NULL, 'active', '77.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.140.99', 'Продукция из чугуна и стали прочая', NULL, 'active', '77.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.150.01', 'Продукция из цветных металлов в целом', NULL, 'active', '77.150', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.150.10', 'Продукция из алюминия', NULL, 'active', '77.150', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.150.20', 'Продукция из магния', NULL, 'active', '77.150', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.150.30', 'Продукция из меди', NULL, 'active', '77.150', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.150.40', 'Продукция из никеля и хрома', NULL, 'active', '77.150', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.150.50', 'Продукция из титана', NULL, 'active', '77.150', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.150.60', 'Продукция из свинца, цинка и олова', NULL, 'active', '77.150', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.150.70', 'Продукция из кадмия и кобальта', NULL, 'active', '77.150', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '77.150.99', 'Продукция из цветных металлов прочая', NULL, 'active', '77.150', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '79.060.01', 'Древесные плиты в целом', NULL, 'active', '79.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '79.060.10', 'Фанера', NULL, 'active', '79.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '79.060.20', 'Древесно-волокнистые и древесно-стружечные плиты', NULL, 'active', '79.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '79.060.99', 'Древесные плиты прочие', NULL, 'active', '79.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '79.120.01', 'Деревообрабатывающее оборудование в целом', NULL, 'active', '79.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '79.120.10', 'Деревообрабатывающие станки', NULL, 'active', '79.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '79.120.20', 'Деревообрабатывающие инструменты', NULL, 'active', '79.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '79.120.99', 'Деревообрабатывающее оборудование прочее', NULL, 'active', '79.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '81.040.01', 'Стекло в целом', NULL, 'active', '81.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '81.040.10', 'Сырье и необработанное стекло', NULL, 'active', '81.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '81.040.20', 'Стекло для строительства зданий', NULL, 'active', '81.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '81.040.30', 'Изделия из стекла', NULL, 'active', '81.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '81.060.01', 'Керамика в целом', NULL, 'active', '81.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '81.060.10', 'Сырье', NULL, 'active', '81.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '81.060.20', 'Изделия из керамики', NULL, 'active', '81.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '81.060.30', 'Высококачественная керамика', NULL, 'active', '81.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '81.060.99', 'Керамика, прочие аспекты', NULL, 'active', '81.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83.040.01', 'Сырье для производства резины и пластмасс в целом', NULL, 'active', '83.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83.040.10', 'Латекс и сырой каучук', NULL, 'active', '83.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83.040.20', 'Ингредиенты резиновой смеси', NULL, 'active', '83.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83.040.30', 'Вспомогательные материалы и добавки для пластмасс', NULL, 'active', '83.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83.080.01', 'Пластмассы в целом', NULL, 'active', '83.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83.080.10', 'Термореактивные материалы', NULL, 'active', '83.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83.080.20', 'Термопластические материалы', NULL, 'active', '83.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83.140.01', 'Резиновые и пластмассовые изделия в целом', NULL, 'active', '83.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83.140.10', 'Пленки и листы', NULL, 'active', '83.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83.140.20', 'Слоистые листы', NULL, 'active', '83.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83.140.30', 'Пластмассовые трубы, фитинги не для жидкостей', NULL, 'active', '83.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83.140.40', 'Рукава', NULL, 'active', '83.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83.140.50', 'Уплотнения', NULL, 'active', '83.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83.140.99', 'Резиновые и пластмассовые изделия прочие', NULL, 'active', '83.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83.160.01', 'Шины в целом', NULL, 'active', '83.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83.160.10', 'Шины для дорожно-транспортных средств', NULL, 'active', '83.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83.160.20', 'Авиационные шины', NULL, 'active', '83.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83.160.30', 'Шины для сельскохозяйственных машин', NULL, 'active', '83.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '83.160.99', 'Шины прочие', NULL, 'active', '83.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '85.080.01', 'Бумажные изделия в целом', NULL, 'active', '85.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '85.080.10', 'Офисная бумага', NULL, 'active', '85.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '85.080.20', 'Папиросная бумага', NULL, 'active', '85.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '85.080.30', 'Картон', NULL, 'active', '85.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '85.080.99', 'Бумажные изделия прочие', NULL, 'active', '85.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '87.060.01', 'Ингредиенты красок в целом', NULL, 'active', '87.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '87.060.10', 'Пигменты и разбавители', NULL, 'active', '87.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '87.060.20', 'Связующие вещества', NULL, 'active', '87.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '87.060.30', 'Растворители', NULL, 'active', '87.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '87.060.99', 'Ингредиенты красок прочие', NULL, 'active', '87.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.010.01', 'Строительная промышленность в целом', NULL, 'active', '91.010', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.010.10', 'Правовые аспекты', NULL, 'active', '91.010', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.010.20', 'Контрактные аспекты', NULL, 'active', '91.010', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.010.30', 'Технические аспекты', NULL, 'active', '91.010', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.010.99', 'Строительная промышленность, прочие аспекты', NULL, 'active', '91.010', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.040.01', 'Строительство в целом', NULL, 'active', '91.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.040.10', 'Общественные здания', NULL, 'active', '91.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.040.20', 'Торговые и промышленные здания', NULL, 'active', '91.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.040.30', 'Жилые здания', NULL, 'active', '91.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.040.99', 'Здания прочие', NULL, 'active', '91.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.060.01', 'Строительные элементы в целом', NULL, 'active', '91.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.060.10', 'Стены. Перегородки. Фасады', NULL, 'active', '91.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.060.20', 'Крыши', NULL, 'active', '91.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.060.30', 'Потолки. Полы. Лестницы', NULL, 'active', '91.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.060.40', 'Дымовые трубы, шахты, каналы', NULL, 'active', '91.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.060.50', 'Двери и окна', NULL, 'active', '91.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.060.99', 'Строительные элементы прочие', NULL, 'active', '91.060', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.080.01', 'Конструкции зданий в целом', NULL, 'active', '91.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.080.10', 'Металлические конструкции', NULL, 'active', '91.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.080.13', 'Стальные конструкции', NULL, 'active', '91.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.080.17', 'Алюминиевые конструкции', NULL, 'active', '91.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.080.20', 'Деревянные конструкции', NULL, 'active', '91.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.080.30', 'Каменная и кирпичная кладка', NULL, 'active', '91.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.080.40', 'Бетонные конструкции', NULL, 'active', '91.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.080.99', 'Конструкции зданий прочие', NULL, 'active', '91.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.100.01', 'Строительные материалы в целом', NULL, 'active', '91.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.100.10', 'Цемент. Гипс. Известь. Строительный раствор', NULL, 'active', '91.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.100.15', 'Минеральные материалы и изделия', NULL, 'active', '91.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.100.23', 'Керамическая плитка', NULL, 'active', '91.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.100.25', 'Керамические изделия для строительства', NULL, 'active', '91.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.100.30', 'Бетон и изделия из бетона', NULL, 'active', '91.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.100.40', 'Изделия из цемента, армированного волокном', NULL, 'active', '91.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.100.50', 'Связующие вещества. Уплотнительные материалы', NULL, 'active', '91.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.100.60', 'Тепло- и звукоизоляционные материалы', NULL, 'active', '91.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.100.99', 'Строительные материалы прочие', NULL, 'active', '91.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.120.01', 'Защита зданий снаружи и внутри в целом', NULL, 'active', '91.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.120.10', 'Теплоизоляция зданий', NULL, 'active', '91.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.120.20', 'Акустика в зданиях. Звукоизоляция', NULL, 'active', '91.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.120.25', 'Сейсмическая защита и защита от вибрации', NULL, 'active', '91.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.120.30', 'Водонепроницаемость', NULL, 'active', '91.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.120.40', 'Защита от молний', NULL, 'active', '91.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.120.99', 'Защита зданий снаружи и внутри, прочие аспекты', NULL, 'active', '91.120', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.140.01', 'Установки в зданиях в целом', NULL, 'active', '91.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.140.10', 'Системы центрального отопления', NULL, 'active', '91.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.140.30', 'Вентиляционные системы и системы кондиционирования воздуха', NULL, 'active', '91.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.140.40', 'Системы газоснабжения', NULL, 'active', '91.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.140.50', 'Системы электроснабжения', NULL, 'active', '91.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.140.60', 'Системы водоснабжения', NULL, 'active', '91.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.140.65', 'Водонагревательное оборудование', NULL, 'active', '91.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.140.70', 'Санитарно-техническое оборудование', NULL, 'active', '91.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.140.80', 'Дренажные системы', NULL, 'active', '91.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.140.90', 'Лифты. Эскалаторы', NULL, 'active', '91.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.140.99', 'Установки в зданиях прочие', NULL, 'active', '91.140', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.160.01', 'Освещение в целом', NULL, 'active', '91.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.160.10', 'Внутреннее освещение', NULL, 'active', '91.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '91.160.20', 'Наружное освещение зданий', NULL, 'active', '91.160', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '93.080.01', 'Строительство дорог в целом', NULL, 'active', '93.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '93.080.10', 'Сооружение дорог', NULL, 'active', '93.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '93.080.20', 'Дорожно-строительные материалы', NULL, 'active', '93.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '93.080.30', 'Дорожное оборудование и установки', NULL, 'active', '93.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '93.080.40', 'Уличное освещение и связанное с ним оборудование', NULL, 'active', '93.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '93.080.99', 'Строительство дорог, прочие аспекты', NULL, 'active', '93.080', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.040.01', 'Кухонное оборудование в целом', NULL, 'active', '97.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.040.10', 'Кухонная мебель', NULL, 'active', '97.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.040.20', 'Кухонные плиты, рабочие столы, печи и аналогичные аппараты', NULL, 'active', '97.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.040.30', 'Бытовые холодильные аппараты', NULL, 'active', '97.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.040.40', 'Посудомоечные машины', NULL, 'active', '97.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.040.50', 'Небольшие кухонные аппараты', NULL, 'active', '97.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.040.60', 'Посуда для приготовления пищи, ножевые изделия и столовые приборы', NULL, 'active', '97.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.040.99', 'Кухонное оборудование прочее', NULL, 'active', '97.040', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.100.01', 'Нагревательные приборы в целом', NULL, 'active', '97.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.100.10', 'Электрические нагреватели', NULL, 'active', '97.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.100.20', 'Газовые нагреватели', NULL, 'active', '97.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.100.30', 'Нагреватели на твердом топливе', NULL, 'active', '97.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.100.40', 'Нагреватели на жидком топливе', NULL, 'active', '97.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.100.99', 'Нагреватели на других источниках энергии', NULL, 'active', '97.100', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.130.01', 'Аксессуары для магазинов в целом', NULL, 'active', '97.130', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.130.10', 'Стеллажи', NULL, 'active', '97.130', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.130.20', 'Торговые холодильные аппараты', NULL, 'active', '97.130', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.130.30', 'Тележки для супермаркетов', NULL, 'active', '97.130', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.130.99', 'Аксессуары для магазинов прочие', NULL, 'active', '97.130', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.200.01', 'Оборудование для отдыха в целом', NULL, 'active', '97.200', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.200.10', 'Театральное, сценическое, студийное оборудование', NULL, 'active', '97.200', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.200.20', 'Музыкальные инструменты', NULL, 'active', '97.200', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.200.30', 'Туристическое снаряжение и площадки для кемпинга', NULL, 'active', '97.200', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.200.40', 'Игровые площадки', NULL, 'active', '97.200', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.200.50', 'Игрушки', NULL, 'active', '97.200', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.200.99', 'Оборудование для отдыха прочее', NULL, 'active', '97.200', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.220.01', 'Спортивный инвентарь и сооружения в целом', NULL, 'active', '97.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.220.10', 'Спортивные сооружения', NULL, 'active', '97.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.220.20', 'Инвентарь для зимних видов спорта', NULL, 'active', '97.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.220.30', 'Инвентарь для спортивных залов', NULL, 'active', '97.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.220.40', 'Инвентарь для спорта на открытом воздухе и для водных видов спорта', NULL, 'active', '97.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '97.220.99', 'Спортивный инвентарь и сооружения прочие', NULL, 'active', '97.220', NULL, NULL, NULL, NULL);
INSERT INTO registry.classifiers VALUES ('MKS', '27.010-01', 'Электроэнергетические системы', NULL, 'active', '27.010', NULL, NULL, NULL, NULL);


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
-- Name: document_history_id_seq; Type: SEQUENCE SET; Schema: registry; Owner: postgres
--

SELECT pg_catalog.setval('registry.document_history_id_seq', 1, false);


--
-- Name: document_references_id_seq; Type: SEQUENCE SET; Schema: registry; Owner: postgres
--

SELECT pg_catalog.setval('registry.document_references_id_seq', 1, false);


--
-- Name: document_sections_id_seq; Type: SEQUENCE SET; Schema: registry; Owner: postgres
--

SELECT pg_catalog.setval('registry.document_sections_id_seq', 1, false);


--
-- Name: document_versions_id_seq; Type: SEQUENCE SET; Schema: registry; Owner: postgres
--

SELECT pg_catalog.setval('registry.document_versions_id_seq', 1, false);


--
-- Name: documents_id_seq; Type: SEQUENCE SET; Schema: registry; Owner: postgres
--

SELECT pg_catalog.setval('registry.documents_id_seq', 1, false);


--
-- Name: rs_enums_id_seq; Type: SEQUENCE SET; Schema: registry; Owner: pkb_user
--

SELECT pg_catalog.setval('registry.rs_enums_id_seq', 59, true);


--
-- Name: terminology_id_seq; Type: SEQUENCE SET; Schema: registry; Owner: postgres
--

SELECT pg_catalog.setval('registry.terminology_id_seq', 1, false);


--
-- Name: classifiers classifiers_pkey; Type: CONSTRAINT; Schema: registry; Owner: postgres
--

ALTER TABLE ONLY registry.classifiers
    ADD CONSTRAINT classifiers_pkey PRIMARY KEY (classifier_system, code);


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
-- Name: SEQUENCE document_history_id_seq; Type: ACL; Schema: registry; Owner: postgres
--

GRANT ALL ON SEQUENCE registry.document_history_id_seq TO pkb_user;


--
-- Name: TABLE document_history; Type: ACL; Schema: registry; Owner: postgres
--

GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE registry.document_history TO pkb_user;


--
-- Name: SEQUENCE document_references_id_seq; Type: ACL; Schema: registry; Owner: postgres
--

GRANT ALL ON SEQUENCE registry.document_references_id_seq TO pkb_user;


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
-- Name: SEQUENCE document_versions_id_seq; Type: ACL; Schema: registry; Owner: postgres
--

GRANT ALL ON SEQUENCE registry.document_versions_id_seq TO pkb_user;


--
-- Name: TABLE document_versions; Type: ACL; Schema: registry; Owner: postgres
--

GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE registry.document_versions TO pkb_user;


--
-- Name: SEQUENCE documents_id_seq; Type: ACL; Schema: registry; Owner: postgres
--

GRANT ALL ON SEQUENCE registry.documents_id_seq TO pkb_user;


--
-- Name: TABLE documents; Type: ACL; Schema: registry; Owner: postgres
--

GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE registry.documents TO pkb_user;


--
-- Name: SEQUENCE terminology_id_seq; Type: ACL; Schema: registry; Owner: postgres
--

GRANT ALL ON SEQUENCE registry.terminology_id_seq TO pkb_user;


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

\unrestrict 5JPuILMMgVnnFpwdr6X727RiRE7m89eA7FUPs7UKB7sTxhKG9ma93cYmxciqySh

