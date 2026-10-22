"""Verify an exported CSV on the trusted server, without importing its contents."""
import argparse
from pathlib import Path
from export_integrity import verify_export

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('file',type=Path)
    args=p.parse_args()
    valid=verify_export(args.file.read_bytes())
    print('VALID: authentic, unchanged export' if valid else 'INVALID: changed, truncated, or unsigned export')
    raise SystemExit(0 if valid else 1)
