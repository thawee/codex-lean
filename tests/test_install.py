"""Run with python3 -m unittest discover -s tests -v. Uses temporary homes only."""

import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("installer", ROOT / "scripts/install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory(prefix="codex-lean-test-")
        self.addCleanup(self.workspace.cleanup)
        self.home = Path(self.workspace.name) / "codex home"
        self.template = tomllib.loads((ROOT / "codex/config.toml").read_text())

    def run_installer(self):
        return subprocess.run(
            [str(ROOT / "install.sh")], env={**os.environ, "CODEX_HOME": str(self.home)},
            text=True, capture_output=True, check=False,
        )

    def test_fresh_and_repeat_install(self):
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(tomllib.loads((self.home / "config.toml").read_text()), self.template)
        for name in ["AGENTS.md", *(f"agents/{role}.toml" for role in ("explorer", "worker", "researcher", "reviewer"))]:
            self.assertEqual((self.home / name).read_bytes(), (ROOT / "codex" / name).read_bytes())
        before = {str(path.relative_to(self.home)): path.read_bytes() for path in self.home.rglob("*") if path.is_file()}
        for _ in range(2):
            result = self.run_installer()
            self.assertEqual(result.returncode, 0, result.stderr)
        backups = list(self.home.glob("backup-*"))
        self.assertEqual(len(backups), 2)
        for backup in backups:
            for name, content in before.items():
                self.assertEqual((backup / name).read_bytes(), content)
                self.assertEqual((self.home / name).read_bytes(), content)

    def test_existing_settings_and_backup(self):
        self.home.mkdir()
        text = '''# Personal settings
model = "previous"
approval_policy = "never"
notify = ["my-command", "🎵"]
metadata = { when = 2026-10-03T12:00:00Z, date = 2026-10-03, time = 12:34:56, score = nan, limit = inf }
[[examples]]
name = "one"
nested = { value = "line\\nnext", flags = [true, 12, 1.25] }
[mcp_servers.personal]
url = "https://example.test/mcp"
[projects."/example/project"]
trust_level = "trusted"
[agents]
interrupt_message = false
[agents.explorer]
description = "old"
custom = "keep"
[agents.custom]
description = "personal role"
config_file = "agents/custom.toml"
'''
        (self.home / "config.toml").write_text(text)
        (self.home / "AGENTS.md").write_text("Personal instructions\n")
        (self.home / "auth.json").write_text("untouched sentinel\n")
        (self.home / "agents").mkdir()
        (self.home / "agents/custom.toml").write_text('model = "personal"\n')
        expected = tomllib.loads(text)
        installer.merge(expected, self.template)
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(installer.equivalent(tomllib.loads((self.home / "config.toml").read_text()), expected))
        backup, = self.home.glob("backup-*")
        self.assertEqual((backup / "config.toml").read_text(), text)
        self.assertEqual((backup / "AGENTS.md").read_text(), "Personal instructions\n")
        self.assertEqual((self.home / "auth.json").read_text(), "untouched sentinel\n")
        self.assertEqual((self.home / "agents/custom.toml").read_text(), 'model = "personal"\n')

    def test_invalid_config_and_conflicting_table_leave_files_unchanged(self):
        self.home.mkdir()
        for text in ['model = [', 'agents = "not a table"\n']:
            with self.subTest(text=text):
                (self.home / "config.toml").write_text(text)
                (self.home / "AGENTS.md").write_text("keep")
                result = self.run_installer()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Installation failed:", result.stderr)
                self.assertEqual((self.home / "config.toml").read_text(), text)
                self.assertEqual((self.home / "AGENTS.md").read_text(), "keep")
                self.assertEqual(list(self.home.glob("backup-*")), [])

    def test_symlink_does_not_modify_external_file(self):
        self.home.mkdir()
        external = Path(self.workspace.name) / "personal.md"
        external.write_text("keep")
        (self.home / "AGENTS.md").symlink_to(external)
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("symlink", result.stderr)
        self.assertEqual(external.read_text(), "keep")
        self.assertFalse((self.home / "config.toml").exists())


if __name__ == "__main__":
    unittest.main()
