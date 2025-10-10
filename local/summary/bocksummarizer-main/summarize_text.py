"""
Automated text summarization for JSON files in nested S3 folders.

Reads all subfolders from an input S3 bucket, summarizes the text content of
each JSON file using a Hugging Face summarization model, and writes the result
to an output S3 bucket while preserving the original folder structure.

Environment variables:
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_REGION

Usage:
    python summarize_text.py --input-bucket <INPUT_BUCKET> --output-bucket <OUTPUT_BUCKET> [--model <MODEL_NAME>]

Where model may be "facebook/bart-large-cnn" (default) or "t5-base".
"""

import argparse
import json
import os
import sys
import tempfile
from typing import Dict, Iterable, List, Optional, Tuple

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

# Lazily initialized global summarizer to avoid re-loading per call
_SUMMARIZER_PIPELINE = None


def _print(msg: str) -> None:
    print(msg, flush=True)


def get_s3_client() -> boto3.client:
    region = os.getenv("AWS_REGION")
    cfg = Config(region_name=region) if region else None
    return boto3.client("s3", config=cfg)


def list_folders(bucket: str, prefix: str = "") -> List[str]:
    """Recursively list all folder prefixes (ending with '/') under the given prefix.

    Returns a list of folder prefixes relative to the given prefix, including nested ones.
    The empty string represents the bucket root.
    """
    s3 = get_s3_client()
    paginator = s3.get_paginator("list_objects_v2")

    discovered: List[str] = []
    stack: List[str] = [prefix]

    while stack:
        current_prefix = stack.pop()
        try:
            for page in paginator.paginate(Bucket=bucket, Prefix=current_prefix, Delimiter="/"):
                for cp in page.get("CommonPrefixes", []) or []:
                    folder_prefix = cp.get("Prefix")
                    if folder_prefix is None:
                        continue
                    discovered.append(folder_prefix)
                    stack.append(folder_prefix)
        except ClientError as e:
            _print(f"[ERROR] Failed listing folders in s3://{bucket}/{current_prefix}: {e}")
            continue

    # Ensure root is present if there are files at the root
    try:
        has_root_files = False
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter="/"):
            if page.get("Contents"):
                has_root_files = True
                break
        if has_root_files and (prefix if prefix.endswith("/") else f"{prefix}") not in discovered:
            # Represent root by the input prefix itself or empty string
            if prefix == "":
                discovered.insert(0, "")
            else:
                discovered.insert(0, prefix if prefix.endswith("/") else f"{prefix}")
    except ClientError:
        pass

    return sorted(set(discovered))


def list_files_in_folder(bucket: str, folder_prefix: str) -> List[str]:
    """List JSON file keys directly under a folder prefix (non-recursive).

    Args:
        bucket: S3 bucket name
        folder_prefix: Prefix representing a folder (may be empty string for root). Should end with '/' for folders.
    """
    s3 = get_s3_client()
    paginator = s3.get_paginator("list_objects_v2")

    normalized_prefix = folder_prefix
    if normalized_prefix and not normalized_prefix.endswith("/"):
        normalized_prefix += "/"

    keys: List[str] = []
    try:
        for page in paginator.paginate(Bucket=bucket, Prefix=normalized_prefix, Delimiter="/"):
            for obj in page.get("Contents", []) or []:
                key = obj.get("Key")
                if not key:
                    continue
                if key.endswith(".json") and not key.endswith("_summary.json") and not key.endswith("_text_summary.json"):
                    # only include JSON files directly under this folder (Delimiter ensures no deeper)
                    keys.append(key)
    except ClientError as e:
        _print(f"[ERROR] Failed listing files in s3://{bucket}/{normalized_prefix}: {e}")

    return sorted(keys)


def download_file(bucket: str, key: str, local_path: str) -> bool:
    s3 = get_s3_client()
    try:
        s3.download_file(bucket, key, local_path)
        _print(f"[OK] Downloaded s3://{bucket}/{key} -> {local_path}")
        return True
    except ClientError as e:
        _print(f"[ERROR] Download failed for s3://{bucket}/{key}: {e}")
        return False


def _load_text_from_json(path: str) -> Optional[str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        _print(f"[ERROR] Invalid JSON: {path}")
        return None
    except OSError as e:
        _print(f"[ERROR] Failed reading file {path}: {e}")
        return None

    if data is None:
        return None

    if isinstance(data, str):
        text = data.strip()
        return text if text else None

    if isinstance(data, dict):
        # Try common text fields by priority
        candidate_fields = [
            "text",
            "content",
            "article",
            "body",
            "document",
            "data",
        ]
        for field in candidate_fields:
            value = data.get(field)
            if isinstance(value, str) and value.strip():
                return value.strip()

    # As a last resort, try to stringify
    try:
        s = str(data).strip()
        return s if s else None
    except Exception:
        return None


def _init_summarizer(model_name: str):
    global _SUMMARIZER_PIPELINE
    if _SUMMARIZER_PIPELINE is not None:
        return _SUMMARIZER_PIPELINE

    from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM

    _print(f"[INFO] Loading summarization model: {model_name} (this may take a while)...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    _SUMMARIZER_PIPELINE = pipeline(
        "summarization",
        model=model,
        tokenizer=tokenizer,
        device_map="auto" if os.getenv("TRANSFORMERS_DEVICE_MAP", "auto") == "auto" else None,
    )
    return _SUMMARIZER_PIPELINE


def _chunk_text_by_words(text: str, max_words: int) -> List[str]:
    words = text.split()
    if not words:
        return []
    chunks: List[str] = []
    for i in range(0, len(words), max_words):
        chunk = " ".join(words[i : i + max_words]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks


def summarize_text(text: str, model_name: str = "facebook/bart-large-cnn") -> str:
    """Summarize text using a HF transformers pipeline.

    Handles long inputs by chunking and performing hierarchical summarization.
    """
    if not text or not text.strip():
        raise ValueError("Text is empty")

    summarizer = _init_summarizer(model_name)

    # Heuristic: approx 900 words per chunk to stay within typical model limits
    chunks = _chunk_text_by_words(text, max_words=900)
    if not chunks:
        raise ValueError("Text is empty after preprocessing")

    if len(chunks) == 1:
        result = summarizer(chunks[0], truncation=True)[0]["summary_text"]
        return result.strip()

    # Summarize each chunk, then summarize the concatenation of chunk summaries
    partials: List[str] = []
    for idx, chunk in enumerate(chunks, start=1):
        _print(f"[INFO] Summarizing chunk {idx}/{len(chunks)} (~{len(chunk.split())} words)")
        summary = summarizer(chunk, truncation=True)[0]["summary_text"].strip()
        partials.append(summary)

    combined = "\n".join(partials)
    final = summarizer(combined, truncation=True)[0]["summary_text"].strip()
    return final


def _derive_output_key(input_key: str) -> Tuple[str, str]:
    """Given an input key like 'a/b/article.json', return (dir_prefix, output_key).

    Output filename is always 'article_text_summary.json' placed in the same folder.
    """
    dir_prefix = "" if "/" not in input_key else input_key.rsplit("/", 1)[0] + "/"
    output_key = f"{dir_prefix}article_text_summary.json"
    return dir_prefix, output_key


def upload_summary(bucket: str, key: str, content_bytes: bytes, content_type: str = "application/json") -> bool:
    s3 = get_s3_client()
    try:
        s3.put_object(Bucket=bucket, Key=key, Body=content_bytes, ContentType=content_type)
        _print(f"[OK] Uploaded summary -> s3://{bucket}/{key}")
        return True
    except ClientError as e:
        _print(f"[ERROR] Upload failed for s3://{bucket}/{key}: {e}")
        return False


def process_bucket(input_bucket: str, output_bucket: str, model_name: str) -> None:
    _print(f"[START] Processing input bucket: s3://{input_bucket} -> output: s3://{output_bucket}")

    folders = list_folders(input_bucket, prefix="")
    if "" not in folders:
        # Ensure we also inspect root for files
        folders = [""] + folders

    if not folders:
        _print("[WARN] No folders found in input bucket.")
        return

    for folder in folders:
        folder_disp = "/" if folder == "" else folder
        _print(f"[FOLDER] {folder_disp}")
        file_keys = list_files_in_folder(input_bucket, folder)
        if not file_keys:
            _print("  [INFO] No JSON files in this folder.")
            continue

        for key in file_keys:
            _print(f"  [FILE] {key}")
            # Download
            with tempfile.TemporaryDirectory() as tmpdir:
                local_path = os.path.join(tmpdir, os.path.basename(key))
                if not download_file(input_bucket, key, local_path):
                    continue

                # Read and extract text
                text = _load_text_from_json(local_path)
                if text is None or not text.strip():
                    _print(f"  [WARN] Empty or missing text in {key}; skipping.")
                    continue

                # Summarize
                try:
                    summary_text = summarize_text(text, model_name=model_name)
                except Exception as e:
                    _print(f"  [ERROR] Summarization failed for {key}: {e}")
                    continue

                # Build summary JSON
                filename_only = os.path.basename(key)
                summary_doc = {
                    "filename": filename_only,
                    "summary_type": "text",
                    "summary": summary_text,
                }
                payload = json.dumps(summary_doc, ensure_ascii=False, indent=2).encode("utf-8")

                # Upload preserving folder structure
                _, output_key = _derive_output_key(key)
                upload_summary(output_bucket, output_key, payload)

    _print("[DONE] Processing complete.")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize JSON text files from S3 and write summaries back to S3.")
    
    # Set default buckets from environment variables or use hardcoded defaults
    default_input_bucket = os.getenv("INPUT_BUCKET", "your-default-input-bucket")
    default_output_bucket = os.getenv("OUTPUT_BUCKET", "your-default-output-bucket")
    
    parser.add_argument("--input-bucket", default=default_input_bucket, help="Name of the S3 input bucket")
    parser.add_argument("--output-bucket", default=default_output_bucket, help="Name of the S3 output bucket")
    parser.add_argument(
        "--model",
        default=os.getenv("SUMMARY_MODEL", "facebook/bart-large-cnn"),
        help="HF model name (e.g., facebook/bart-large-cnn or t5-base)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    try:
        process_bucket(args.input_bucket, args.output_bucket, model_name=args.model)
        return 0
    except KeyboardInterrupt:
        _print("[INTERRUPTED] Exiting.")
        return 130
    except Exception as e:
        _print(f"[FATAL] Unhandled error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())


