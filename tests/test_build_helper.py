import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from build_helper import helper_path

class BuildHelperTests(unittest.TestCase):
    def test_fresh_checkout_builds_in_cache_and_reuses_binary(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ,{'XDG_CACHE_HOME':temp}):
            binary=helper_path()
            self.assertTrue(binary.is_file())
            self.assertTrue(str(binary).startswith(temp))
            self.assertTrue(os.access(binary,os.X_OK))
            original=binary.stat().st_mtime_ns
            self.assertEqual(subprocess.run([str(binary)],capture_output=True).returncode,2)
            self.assertEqual(helper_path(),binary)
            self.assertEqual(binary.stat().st_mtime_ns,original)
    def test_missing_compiler_has_actionable_message(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ,{'XDG_CACHE_HOME':temp}):
            with patch('build_helper.subprocess.run',side_effect=FileNotFoundError()):
                with self.assertRaisesRegex(OSError,'GCC is required'):helper_path()
            self.assertFalse(list(Path(temp).rglob('.build-*')))

if __name__=='__main__':unittest.main()
