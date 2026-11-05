import re
import unittest

from source_provenance import UPSTREAM_COMMIT, UPSTREAM_REPOSITORY
from vendor_bibata import UPSTREAM_REF


class SourceProvenanceTests(unittest.TestCase):
    def test_upstream_source_is_pinned_to_a_full_commit(self):
        self.assertEqual(UPSTREAM_REPOSITORY, "https://github.com/rtgiskard/bibata_cursor")
        self.assertRegex(UPSTREAM_COMMIT, re.compile(r"^[0-9a-f]{40}$"))
        self.assertEqual(UPSTREAM_REF, UPSTREAM_COMMIT)


if __name__ == "__main__":
    unittest.main()
