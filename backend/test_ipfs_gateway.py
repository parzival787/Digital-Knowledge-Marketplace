import os
import unittest
from unittest.mock import patch
from services.ipfs_gateway import ipfs_gateways


class GatewayTests(unittest.TestCase):
    def test_preferred_gateway_and_fallbacks(self):
        with patch.dict(os.environ, {"PINATA_GATEWAY": "cyan-eldest-krill-834.mypinata.cloud"}):
            gateways = ipfs_gateways()
            self.assertEqual(gateways[0], "https://cyan-eldest-krill-834.mypinata.cloud/ipfs/")
            self.assertEqual(len(gateways), 3)
        with patch.dict(os.environ, {"PINATA_GATEWAY": ""}):
            self.assertEqual(len(ipfs_gateways()), 2)

    def test_rejects_non_gateway_destinations(self):
        for hostname in ("localhost", "https://example.com", "x.mypinata.cloud/other", "x.mypinata.cloud.evil.com"):
            with self.subTest(hostname=hostname), patch.dict(os.environ, {"PINATA_GATEWAY": hostname}):
                with self.assertRaises(ValueError):
                    ipfs_gateways()
