import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import release  # noqa: E402


class ReleaseTest(unittest.TestCase):
    def test_publish_and_replace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ipa = root / "src.ipa"
            ipa.write_bytes(b"ipa-one")
            entry = release.publish(root, "1.4.1", ipa, "关于页和检查更新")
            self.assertEqual(entry["version"], "1.4.1")
            self.assertEqual(entry["file"], "Tieji-v1.4.1.ipa")
            self.assertTrue((root / "Tieji-v1.4.1.ipa").is_file())
            manifest = json.loads((root / "latest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["channels"]["ios"]["latest"], "1.4.1")
            self.assertIn("关于页和检查更新", manifest["channels"]["ios"]["releases"][0]["changelog"])
            sums = (root / "SHA256SUMS").read_text(encoding="utf-8")
            self.assertIn("Tieji-v1.4.1.ipa", sums)
            # replace same version
            ipa.write_bytes(b"ipa-two-bigger")
            release.publish(root, "1.4.1", ipa, "重建")
            manifest = json.loads((root / "latest.json").read_text(encoding="utf-8"))
            rels = manifest["channels"]["ios"]["releases"]
            self.assertEqual(len(rels), 1)
            self.assertEqual(rels[0]["size"], len(b"ipa-two-bigger"))
            self.assertEqual(manifest["channels"]["ios"]["previous"], None)


if __name__ == "__main__":
    unittest.main()
