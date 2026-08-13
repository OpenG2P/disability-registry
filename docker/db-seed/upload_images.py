#!/usr/bin/env python3
"""Upload sample profile images to MinIO and link them to the person register.

Images come from the shared openg2p-data clone
(/openg2p-data/demography/images/*.jpg). Each is uploaded under its own filename
and the matching row in g2p_register_persons_with_disability is updated with
record_image_document_id = filename.

The link is made on `search_text`, not `functional_record_id`. The shared images
are named for the demography individual they depict (IND-0001.jpg), while this
registry mints its own PWD- functional ids — so matching on functional id, as
the reference loader does, updates zero rows and silently leaves every record
without a photo. load_sample_data.py stamps the source demography id into
search_text precisely so this join has something to match on.
"""

import os
import sys
from pathlib import Path

import psycopg2
from minio import Minio

TABLE = "g2p_register_persons_with_disability"


def env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if value is None or value == "":
        print(f"[upload-images] Missing required env var: {name}", file=sys.stderr)
        sys.exit(1)
    return value


def main() -> None:
    images_dir = Path(os.environ.get("IMAGES_DIR", "/openg2p-data/demography/images"))
    bucket_name = env("IMAGE_BUCKET_NAME", "registrant-photos")
    endpoint = env("MINIO_ENDPOINT")
    access_key = env("MINIO_ACCESS_KEY")
    secret_key = env("MINIO_SECRET_KEY")
    secure = os.environ.get("MINIO_SECURE", "false").lower() in ("1", "true", "yes")

    if not images_dir.is_dir():
        print(f"[upload-images] Images directory not found: {images_dir}", file=sys.stderr)
        sys.exit(1)

    image_files = sorted(images_dir.glob("*.jpg"))
    if not image_files:
        print(f"[upload-images] No .jpg files found in {images_dir}", file=sys.stderr)
        sys.exit(1)

    client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        print(f"[upload-images] Created MinIO bucket: {bucket_name}")

    print(f"[upload-images] Uploading {len(image_files)} image(s) to s3://{bucket_name}/ ...")
    uploaded: list[tuple[str, str]] = []
    for path in image_files:
        client.fput_object(bucket_name, path.name, str(path), content_type="image/jpeg")
        uploaded.append((path.stem, path.name))
    print(f"[upload-images] Uploaded {len(uploaded)} images.")

    conn = psycopg2.connect(
        host=env("PGHOST"),
        port=os.environ.get("PGPORT", "5432"),
        dbname=env("PGDATABASE"),
        user=env("PGUSER"),
        password=env("PGPASSWORD"),
    )
    conn.autocommit = False
    cur = conn.cursor()
    try:
        # Only a fraction of the demography individuals are registered here (see
        # load_sample_data.py), so most images will match nothing. That is
        # expected, and the count below is what says so out loud rather than
        # letting a zero look like success.
        updated = 0
        for source_id, object_key in uploaded:
            cur.execute(
                f'UPDATE "public"."{TABLE}" '
                "SET record_image_document_id = %s "
                "WHERE record_image_document_id IS NULL "
                "  AND search_text LIKE %s",
                (object_key, f"%{source_id}%"),
            )
            updated += cur.rowcount
        conn.commit()
        print(
            f"[upload-images] Linked {updated} of {len(uploaded)} image(s) to {TABLE} "
            f"(unmatched images depict people this registry did not register)."
        )
        if updated == 0:
            print(
                "[upload-images] WARNING: no images matched. Check that "
                "load_sample_data.py ran first and stamped the source demography "
                "id into search_text.",
                file=sys.stderr,
            )
    except Exception as exc:
        conn.rollback()
        print(f"[upload-images] DB update FAILED: {exc}", file=sys.stderr)
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
