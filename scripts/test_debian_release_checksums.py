import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packaging" / "debian"))
import release_checksums


def release_payload():
    return {
        "tag_name": "v1.5.0",
        "assets": [
            {
                "name": "bibata-material-dark-v1.5.0.tar.gz",
                "digest": "sha256:" + "a" * 64,
            },
            {
                "name": "bibata-material-light-v1.5.0.tar.gz",
                "digest": "sha256:" + "b" * 64,
            },
            {
                "name": "bibata-material-dark-v1.5.0-win.zip",
                "digest": "sha256:" + "c" * 64,
            },
        ],
    }


class ReleaseChecksumTests(unittest.TestCase):
    def opener_for(self, payload):
        encoded = json.dumps(payload).encode("utf-8")

        def opener(request, timeout):
            self.assertIn("/releases/tags/v1.5.0", request.full_url)
            self.assertEqual(timeout, 30)
            return io.BytesIO(encoded)

        return opener

    def test_reads_only_the_two_required_linux_asset_digests(self):
        checksums = release_checksums.release_archive_checksums(
            "v1.5.0", opener=self.opener_for(release_payload())
        )
        self.assertEqual(
            checksums,
            {
                "bibata-material-dark-v1.5.0.tar.gz": "a" * 64,
                "bibata-material-light-v1.5.0.tar.gz": "b" * 64,
            },
        )

    def test_uses_github_token_for_release_metadata_requests(self):
        encoded = json.dumps(release_payload()).encode("utf-8")

        def opener(request, timeout):
            self.assertEqual(
                request.get_header("Authorization"), "Bearer test-token"
            )
            return io.BytesIO(encoded)

        with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
            checksums = release_checksums.release_archive_checksums(
                "v1.5.0", opener=opener
            )
        self.assertEqual(len(checksums), 2)

    def test_writes_sha256sum_compatible_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "checksums.txt"
            release_checksums.write_checksum_manifest(
                "v1.5.0", output, opener=self.opener_for(release_payload())
            )
            self.assertEqual(
                output.read_text(encoding="utf-8").splitlines(),
                [
                    f'{"a" * 64}  bibata-material-dark-v1.5.0.tar.gz',
                    f'{"b" * 64}  bibata-material-light-v1.5.0.tar.gz',
                ],
            )

    def test_rejects_missing_linux_asset(self):
        payload = release_payload()
        payload["assets"] = payload["assets"][:1]
        with self.assertRaisesRegex(ValueError, "light"):
            release_checksums.release_archive_checksums(
                "v1.5.0", opener=self.opener_for(payload)
            )

    def test_rejects_missing_or_malformed_digest(self):
        payload = release_payload()
        payload["assets"][0]["digest"] = None
        with self.assertRaisesRegex(ValueError, "SHA-256 digest"):
            release_checksums.release_archive_checksums(
                "v1.5.0", opener=self.opener_for(payload)
            )

    def test_rejects_metadata_for_a_different_tag(self):
        payload = release_payload()
        payload["tag_name"] = "v1.4.0"
        with self.assertRaisesRegex(ValueError, "expected 'v1.5.0'"):
            release_checksums.release_archive_checksums(
                "v1.5.0", opener=self.opener_for(payload)
            )


if __name__ == "__main__":
    unittest.main()
