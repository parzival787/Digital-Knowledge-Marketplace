"""Verified HTTPS gateways for protected files and public metadata."""
import os
import re


def ipfs_gateways():
    hostname = os.environ.get("PINATA_GATEWAY", "").strip()
    preferred = ()
    if hostname:
        if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.mypinata\.cloud", hostname):
            raise ValueError("PINATA_GATEWAY must be a dedicated mypinata.cloud hostname")
        preferred = (f"https://{hostname}/ipfs/",)
    return preferred + ("https://ipfs.io/ipfs/", "https://gateway.pinata.cloud/ipfs/")
