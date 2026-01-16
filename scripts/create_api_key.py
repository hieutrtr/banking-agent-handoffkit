#!/usr/bin/env python3
"""Script to generate a new API key."""

import argparse
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from handoffkit.api.auth import generate_api_key, hash_key
from handoffkit.api.database import SessionLocal
from handoffkit.api.models.auth import APIKey


def create_api_key(name: str):
    """Create a new API key."""
    db = SessionLocal()
    try:
        raw_key = generate_api_key()
        key_hash = hash_key(raw_key)

        api_key = APIKey(
            key_hash=key_hash,
            name=name,
            is_active=True
        )

        db.add(api_key)
        db.commit()
        db.refresh(api_key)

        print(f"API Key created successfully for '{name}'")
        print(f"Key ID: {api_key.id}")
        print(f"\nAPI KEY: {raw_key}")
        print("\nWARNING: Store this key safely. It cannot be retrieved again!")

    except Exception as e:
        print(f"Error creating API key: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a new API key")
    parser.add_argument("name", help="Name/Description for the API key")
    args = parser.parse_args()

    create_api_key(args.name)
