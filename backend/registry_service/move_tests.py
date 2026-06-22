import os
import sys

missing_file = 'tests/test_missing_endpoints.py'

if not os.path.exists(missing_file):
    print("test_missing_endpoints.py not found.")
    sys.exit(1)

with open(missing_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

functions = {}
current_fn = None
for line in lines:
    if line.startswith('def test_'):
        current_fn = line.split('def ')[1].split('(')[0]
        functions[current_fn] = [line]
    elif current_fn is not None:
        functions[current_fn].append(line)

classifiers_tests = [
    'test_classifier_code_filtering',
    'test_classifier_tree_metadata',
    'test_classifier_get_children',
    'test_create_classifier_parent_not_found',
    'test_update_patch_classifier_nullify',
    'test_csv_imports',
    'test_create_classifier_cross_system_parent'
]
terminology_tests = [
    'test_update_patch_terminology_nullify'
]
documents_tests = [
    'test_pipeline_document_terminology_linking',
    'test_document_mks_okstu_name_resolution',
    'test_document_total_versions_count'
]

def append_to_file(filename, test_names):
    with open(filename, 'a', encoding='utf-8') as f:
        for name in test_names:
            if name in functions:
                f.write('\n\n')
                f.writelines(functions[name])

append_to_file('tests/test_classifiers.py', classifiers_tests)
append_to_file('tests/test_terminology.py', terminology_tests)
append_to_file('tests/test_documents.py', documents_tests)

os.remove(missing_file)
print("Successfully moved tests and deleted test_missing_endpoints.py")
