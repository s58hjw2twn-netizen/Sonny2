{
  "build": "0.1.0",
  "sonny_core": "1.0",
  "database_schema": "1.1",
  "project_state_schema": "1",
  "memory_schema": "1",
  "host_model": "stub-local",
  "test_suite": "1.2",
  "timestamp": "2026-10-06T15:10:28.493970+00:00",
  "disposition": "GATE_1_FUNCTIONAL_PASS",
  "evidence_scope": "local functional contract tests plus direct-identifier authorization/isolation tests; not independent security review, deployed-environment validation, or real host-model validation",
  "results": [
    {"test_id": "G1-01", "result": "PASS", "build": "0.1.0", "test_suite": "1.2"},
    {"test_id": "G1-02", "result": "PASS", "build": "0.1.0", "test_suite": "1.2"},
    {"test_id": "G1-03", "result": "PASS", "build": "0.1.0", "test_suite": "1.2"},
    {"test_id": "G1-04", "result": "PASS", "build": "0.1.0", "test_suite": "1.2"},
    {"test_id": "G1-05", "result": "PASS", "build": "0.1.0", "test_suite": "1.2"},
    {"test_id": "G1-06", "result": "PASS", "build": "0.1.0", "test_suite": "1.2"},
    {"test_id": "G1-07", "result": "PASS", "build": "0.1.0", "test_suite": "1.2"},
    {"test_id": "G1-08", "result": "PASS", "build": "0.1.0", "test_suite": "1.2"},
    {"test_id": "G1-09", "result": "PASS", "build": "0.1.0", "test_suite": "1.2"},
    {"test_id": "G1-10", "result": "PASS", "build": "0.1.0", "test_suite": "1.2"},
    {"test_id": "G1-11", "result": "PASS", "build": "0.1.0", "test_suite": "1.2"},
    {"test_id": "G1-12", "result": "PASS", "build": "0.1.0", "test_suite": "1.2"}
  ],
  "pytest": "..............                                                           [100%]\n14 passed in 1.37s\n",
  "collected_tests": "tests/test_gate1.py::test_G1_01_create_isolated_account\ntests/test_gate1.py::test_G1_02_create_project_persists\ntests/test_gate1.py::test_G1_03_chat_uses_project_context\ntests/test_gate1.py::test_G1_04_approved_memory_persists_with_provenance\ntests/test_gate1.py::test_G1_05_correction_used_and_auditable\ntests/test_gate1.py::test_G1_06_deleted_memory_stops_influencing\ntests/test_gate1.py::test_G1_07_next_action_proposed\ntests/test_gate1.py::test_G1_08_action_feedback_recorded\ntests/test_gate1.py::test_G1_09_state_reconstructs_after_store_restart\ntests/test_gate1.py::test_G1_10_cross_user_isolation\ntests/test_gate1.py::test_G1_11_false_memory_sentinel\ntests/test_gate1.py::test_G1_12_unknown_distinguished_from_known\ntests/test_gate1.py::test_G1_10_adversarial_direct_identifier_paths\ntests/test_gate1.py::test_G1_10_cross_project_object_id_binding\n\n14 tests collected in 0.38s\n"
}
