"""Unit tests for JSON schema contracts, canonical examples, and hosted endpoint drift."""
import glob
import json
from pathlib import Path
import unittest
import urllib.request
import urllib.error
import jsonschema

def find_repo_root():
    curr = Path(__file__).resolve().parent
    for _ in range(6):
        if (curr / "schemas" / "performance_plan.schema.json").exists():
            return curr
        curr = curr.parent
    return Path(__file__).resolve().parents[3]

REPO_ROOT = find_repo_root()
LOCAL_SCHEMA_PATH = REPO_ROOT / "schemas" / "performance_plan.schema.json"
LOCAL_EXAMPLES_DIR = REPO_ROOT / "schemas" / "examples"

HOSTED_SCHEMA_URL = "https://frontiermindworks.com/schemas/v1/performance_plan.schema.json"
HOSTED_EXAMPLES_BASE = "https://frontiermindworks.com/schemas/v1/examples"


class PerformancePlanSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(LOCAL_SCHEMA_PATH, "r", encoding="utf-8") as f:
            cls.local_schema = json.load(f)
        cls.validator_cls = jsonschema.validators.validator_for(cls.local_schema)
        cls.validator_cls.check_schema(cls.local_schema)
        cls.local_validator = cls.validator_cls(cls.local_schema)

    def test_local_schema_is_valid_draft_2020_12(self):
        self.assertEqual(self.local_schema.get("$schema"), "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(self.local_schema.get("$id"), "https://frontiermindworks.com/schemas/v1/performance_plan.schema.json")
        self.assertEqual(self.local_schema.get("version"), "0.3.1")

    def test_all_local_example_plans_conform_to_schema(self):
        example_files = sorted(glob.glob(str(LOCAL_EXAMPLES_DIR / "*.json")))
        self.assertGreaterEqual(len(example_files), 3, "Expected at least 3 canonical example plans.")
        for example_path in example_files:
            with self.subTest(example=Path(example_path).name):
                with open(example_path, "r", encoding="utf-8") as f:
                    instance = json.load(f)
                self.local_validator.validate(instance=instance)

    def test_hosted_schema_and_examples_deploy_drift(self):
        try:
            req = urllib.request.Request(
                HOSTED_SCHEMA_URL,
                headers={"User-Agent": "MHPD-CI-Validator/0.3.1"}
            )
            with urllib.request.urlopen(req, timeout=8) as response:
                hosted_schema = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as exc:
            self.skipTest(f"Live website unreachable or timed out ({exc}). Skipping deploy drift check.")

        # 1. Assert hosted schema matches local schema version and dialect
        self.assertEqual(hosted_schema.get("version"), self.local_schema.get("version"))
        self.assertEqual(hosted_schema.get("$id"), self.local_schema.get("$id"))
        self.assertEqual(hosted_schema.get("$schema"), self.local_schema.get("$schema"))

        hosted_validator_cls = jsonschema.validators.validator_for(hosted_schema)
        hosted_validator_cls.check_schema(hosted_schema)
        hosted_validator = hosted_validator_cls(hosted_schema)

        # 2. Fetch and validate each hosted example against the hosted schema
        example_names = [
            "01_single_beat_minimal.json",
            "02_multi_beat_sequence.json",
            "03_channel_locks_and_subtext.json"
        ]
        for name in example_names:
            with self.subTest(hosted_example=name):
                ex_url = f"{HOSTED_EXAMPLES_BASE}/{name}"
                ex_req = urllib.request.Request(ex_url, headers={"User-Agent": "MHPD-CI-Validator/0.3.1"})
                with urllib.request.urlopen(ex_req, timeout=8) as ex_res:
                    hosted_instance = json.loads(ex_res.read().decode("utf-8"))
                hosted_validator.validate(instance=hosted_instance)


if __name__ == "__main__":
    unittest.main()
