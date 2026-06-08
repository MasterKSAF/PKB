-- Seed registry.rs_enums with initial values for classifier systems, document statuses, eras, etc.
BEGIN;

INSERT INTO registry.rs_enums (enum_key, enum_value, description)
VALUES
('classifier_system','MKS', NULL),
('classifier_system','OKSTU', NULL),
('classifier_system','UDC', NULL),
('classifier_system','EXTERNAL', NULL),

('classifier_status','active', NULL),
('classifier_status','deprecated', NULL),
('classifier_status','archived', NULL),

('source_type','GOST', NULL),
('source_type','GOST_R', NULL),
('source_type','OST', NULL),
('source_type','RD', NULL),
('source_type','TU', NULL),
('source_type','ISO', NULL),
('source_type','DNV', NULL),
('source_type','ASTM', NULL),
('source_type','OTHER', NULL),

('document_status','draft', NULL),
('document_status','uploaded', NULL),
('document_status','validating', NULL),
('document_status','processing', NULL),
('document_status','review_required', NULL),
('document_status','ready_for_promotion', NULL),
('document_status','approved', NULL),
('document_status','failed', NULL),
('document_status','archived', NULL),

('era','USSR', NULL),
('era','CIS', NULL),
('era','RF', NULL),
('era','CURRENT', NULL),

('validity_status','active', NULL),
('validity_status','superseded', NULL),
('validity_status','cancelled', NULL),
('validity_status','historical', NULL),
('validity_status','draft', NULL),

('jurisdiction','RU', NULL),
('jurisdiction','EU', NULL),
('jurisdiction','US', NULL),
('jurisdiction','NO', NULL),
('jurisdiction','INTL', NULL),

('term_type','acronym', NULL),
('term_type','foreign_term', NULL),
('term_type','standard_code', NULL),
('term_type','avatar', NULL),
('term_type','symbol', NULL),

('classification_status_code','CONFIRMED', NULL),
('classification_status_code','PENDING_REVIEW', NULL),
('classification_status_code','NOT_FOUND', NULL),
('classification_status_code','NOT_USED', NULL),
('classification_status_code','UNASSIGNED', NULL),

('pending_status','new', NULL),
('pending_status','mapped', NULL),
('pending_status','rejected', NULL),

('validation_status','pending', NULL),
('validation_status','valid', NULL),
('validation_status','invalid', NULL),

('chunk_type','text', NULL),
('chunk_type','table', NULL),
('chunk_type','image', NULL),
('chunk_type','formula', NULL)
ON CONFLICT DO NOTHING;

COMMIT;
