"""Security regressions; Docker calls are mocked, Git flow tests are separate."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from sonny_one.apl import runner
from sonny_one.apl.compare import compare
from sonny_one.apl.loop import run_queue

DIFF = '''diff --git a/sonny_one/apl_targets/x.py b/sonny_one/apl_targets/x.py
--- a/sonny_one/apl_targets/x.py
+++ b/sonny_one/apl_targets/x.py
@@ -1 +1 @@
-old
+new
'''


class HardeningTests(unittest.TestCase):
    def test_timeout_removes_only_named_container(self):
        ok = subprocess.CompletedProcess([], 0, '', '')
        with patch.object(runner, 'execute', side_effect=[subprocess.TimeoutExpired('docker', 1), ok]) as execute:
            result = runner.docker_test('image', Path('/src'), Path('/tests'), 1)
        run = execute.call_args_list[0].args[0]
        name = next(arg.split('=', 1)[1] for arg in run if arg.startswith('--name='))
        self.assertEqual(execute.call_args_list[1].args[0], ['docker', 'rm', '--force', name])
        self.assertTrue(result['cleanup_confirmed'])
        self.assertEqual(result['exit_code'], -1)
        self.assertIn('--entrypoint=python', run)

    def test_infrastructure_failure_is_not_repair(self):
        for code in (-1, 2, 3, 4, 5, 125, 126, 127):
            baseline = dict(base_revision='a', deterministic={'exit_code': code}, heldout={'exit_code': 0})
            candidate = dict(base_revision='a', deterministic={'exit_code': 0}, heldout={'exit_code': 0})
            result = compare(baseline, candidate)
            self.assertEqual(result['repairs'], [])
            self.assertFalse(result['suites']['deterministic']['comparison_valid'])

    def test_invalid_timeout_rejected_before_execution(self):
        for timeout in (0, 601, True, 1.5):
            with self.assertRaises(ValueError):
                runner.evaluate('/missing', 'a'*40, '/missing', '/missing', '/missing', 'image', '/missing', timeout)

    def test_special_file_rejected_without_read(self):
        import os
        with tempfile.TemporaryDirectory() as tmp:
            os.mkfifo(Path(tmp) / 'pipe')
            with self.assertRaises(ValueError):
                runner.suite_fingerprint(Path(tmp))

    def test_nested_suites_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'source').mkdir()
            (root/'trusted'/'heldout').mkdir(parents=True)
            (root/'patch').write_text(DIFF)
            with self.assertRaises(ValueError):
                runner.evaluate(root/'source', 'a'*40, root/'patch', root/'trusted', root/'trusted'/'heldout', 'runner@sha256:'+'a'*64, root/'ledger')

    def test_queue_budget_and_duplicates_fail_before_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'patch'
            path.write_text(DIFF)
            proposal = {'patch': str(path), 'predicted_pass': 0.7}
            with patch('sonny_one.apl.loop.evaluate') as evaluate:
                for proposals, budget in (([proposal]*2, 1), ([proposal]*2, 3), ([proposal], True)):
                    with self.assertRaises(ValueError):
                        run_queue(proposals, max_candidates=budget)
                evaluate.assert_not_called()

    def test_queue_records_prediction_and_never_promotes(self):
        from sonny_one.apl.policy import sha256_bytes, verify_lineage
        with tempfile.TemporaryDirectory() as tmp:
            path, ledger = Path(tmp)/'patch', Path(tmp)/'ledger'
            path.write_text(DIFF)
            report = {'candidate_id': sha256_bytes(DIFF.encode()), 'promotion': 'FORBIDDEN'}
            with patch('sonny_one.apl.loop.evaluate', return_value=report) as evaluate:
                result = run_queue([{'patch': str(path), 'predicted_pass': .7}], ledger=ledger, revision='a'*40)
            self.assertEqual(result['attempted'], 1)
            self.assertEqual(result['promotion'], 'FORBIDDEN')
            self.assertTrue(verify_lineage(ledger))
            self.assertIn('proposal_prediction', ledger.read_text())
            evaluate.assert_called_once()

    def test_queue_evaluates_frozen_validated_patch_bytes(self):
        from sonny_one.apl.policy import sha256_bytes
        with tempfile.TemporaryDirectory() as tmp:
            path, ledger = Path(tmp)/'patch', Path(tmp)/'ledger'
            path.write_text(DIFF)
            digest = sha256_bytes(DIFF.encode())
            captured = []
            def fake_evaluate(*, patch_file, **kwargs):
                captured.append(Path(patch_file).read_text())
                path.write_text('malicious later inbox contents')
                return {'candidate_id': sha256_bytes(captured[-1].encode()),
                        'promotion': 'FORBIDDEN'}
            with patch('sonny_one.apl.loop.evaluate', side_effect=fake_evaluate):
                result = run_queue([{'patch': str(path), 'predicted_pass': .7}],
                                   ledger=ledger, revision='a'*40)
            self.assertEqual(result['attempted'], 1)
            self.assertEqual(captured, [DIFF])
            self.assertEqual(digest, result['reports'][0]['candidate_id'])

    def test_queue_stops_on_missing_suite_outcomes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first, second = root/'a.diff', root/'b.diff'
            first.write_text(DIFF)
            second.write_text(DIFF.replace('+new', '+newer'))
            from sonny_one.apl.policy import sha256_bytes
            incomplete = {'candidate_id': sha256_bytes(DIFF.encode()),
                          'promotion': 'FORBIDDEN'}
            proposals = [{'patch': str(first), 'predicted_pass': .5},
                         {'patch': str(second), 'predicted_pass': .5}]
            with patch('sonny_one.apl.loop.evaluate', return_value=incomplete) as evaluate:
                result = run_queue(proposals, max_candidates=2, ledger=root/'ledger', revision='a'*40)
            self.assertEqual(result['attempted'], 1)
            evaluate.assert_called_once()

    def test_bootstrap_reproducible_and_not_proof(self):
        from sonny_one.apl.metrics import paired_uncertainty
        args = ({'a': 0, 'b': 1, 'c': 0}, {'a': 1, 'b': 0, 'c': 1})
        first = paired_uncertainty(*args, resamples=1000)
        self.assertEqual(first, paired_uncertainty(*args, resamples=1000))
        lo, hi = first['bootstrap_95_percentile_interval']
        self.assertLessEqual(lo, 0)
        self.assertGreaterEqual(hi, 0)
        self.assertFalse(first['improvement_proven'])

    def test_changed_fixtures_reject_real_git_flow(self):
        from test_apl_flow import git
        from sonny_one.apl.policy import verify_lineage
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root/'source'
            target = source/'sonny_one/apl_targets/x.py'
            target.parent.mkdir(parents=True)
            target.write_text('old\n')
            git(source, 'init', '-q')
            git(source, 'config', 'user.email', 'test@example.invalid')
            git(source, 'config', 'user.name', 'Test')
            git(source, 'add', '.')
            git(source, 'commit', '-qm', 'baseline')
            revision = git(source, 'rev-parse', 'HEAD')
            proposal = root/'patch'
            proposal.write_text(DIFF)
            trusted, heldout = root/'trusted', root/'heldout'
            trusted.mkdir()
            heldout.mkdir()
            def mutate(*args):
                (heldout/'test_changed.py').write_text('assert True')
                return {'exit_code': 0}
            with patch.object(runner, 'docker_test', side_effect=mutate):
                result = runner.evaluate(source, revision, proposal, trusted, heldout,
                    'runner@sha256:'+'a'*64, root/'ledger')
            self.assertEqual(result['status'], 'REJECTED')
            self.assertIn('fixtures changed', result['error'])
            self.assertTrue(verify_lineage(root/'ledger'))

    def test_output_capture_is_bounded_for_both_streams(self):
        import sys
        result = runner.bounded_execute([sys.executable, '-c',
            "import sys; sys.stdout.write('x'*200000); sys.stderr.write('y'*200000)"], timeout=5)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, 'x'*4000)
        self.assertEqual(result.stderr, 'y'*4000)

    def test_real_process_timeout(self):
        import sys
        import time
        started = time.monotonic()
        with self.assertRaises(subprocess.TimeoutExpired):
            runner.bounded_execute([sys.executable, '-c', 'import time; time.sleep(30)'], timeout=.1)
        self.assertLess(time.monotonic() - started, 3)

    def test_concurrent_lineage_writers(self):
        from concurrent.futures import ThreadPoolExecutor
        from sonny_one.apl.policy import append_lineage, verify_lineage
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp)/'ledger'
            with ThreadPoolExecutor(max_workers=8) as pool:
                hashes = list(pool.map(lambda i: append_lineage(ledger, {'event': i}), range(40)))
            self.assertEqual(len(set(hashes)), 40)
            self.assertEqual(len(ledger.read_text().splitlines()), 40)
            self.assertTrue(verify_lineage(ledger))

    def test_malformed_ledger_fails_closed(self):
        from sonny_one.apl.policy import append_lineage, verify_lineage
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp)/'ledger'
            for data in ('{', '{}', '[]', 'null'):
                ledger.write_text(data)
                self.assertFalse(verify_lineage(ledger))
                with self.assertRaises(ValueError):
                    append_lineage(ledger, {'event': 'new'})
