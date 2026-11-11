"""Regression checks for deterministic exterior prompt rules."""
import ast
from pathlib import Path
import unittest


SCRIPT = Path(__file__).with_name("comfyui-polish-exterior.py")


def assigned_string(name: str) -> str:
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
                return ast.literal_eval(node.value)
    raise AssertionError(f"{name} assignment not found")


class ExteriorWallLightRuleTest(unittest.TestCase):
    def test_fixture_centreline_is_opening_head_datum(self):
        rule = assigned_string("WALL_LIGHT_RULE")
        self.assertIn("centreline of the fixture body exactly equals the top/head elevation", rule)
        self.assertIn("beside its associated exterior door or window on solid wall", rule)

    def test_rule_forbids_wrong_mounting_heights(self):
        rule = assigned_string("WALL_LIGHT_RULE")
        self.assertIn("never mount a fixture above the frame head", rule)
        self.assertIn("or at handle-height or mid-window height", rule)

    def test_missing_opening_head_omits_instead_of_guessing(self):
        rule = assigned_string("WALL_LIGHT_RULE")
        self.assertIn("omit that decorative wall light instead of guessing its height", rule)


if __name__ == "__main__":
    unittest.main()
