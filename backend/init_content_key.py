"""Initialize local encrypted storage once without printing or replacing secrets."""
import base64
import os
from pathlib import Path
from dotenv import dotenv_values, set_key


def main():
    path = Path(__file__).with_name(".env")
    current = dotenv_values(path).get("CONTENT_MASTER_KEY")
    if current:
        if len(base64.b64decode(current, validate=True)) != 32:
            raise ValueError("Existing CONTENT_MASTER_KEY is invalid; do not replace it without reviewing stored files")
        print("Existing content key preserved.")
        return
    set_key(str(path), "CONTENT_MASTER_KEY", base64.b64encode(os.urandom(32)).decode("ascii"))
    print("Content key initialized in ignored backend/.env. Back it up securely before using protected uploads.")


if __name__ == "__main__":
    main()
