"""
Automated text and image summarization for files in nested S3 folders.

For each subfolder in the input S3 bucket:
- Summarize the text content of a JSON file (if present) and write
  'article_text_summary.json' to the corresponding subfolder of the output bucket
- Generate captions for any .jpg/.jpeg/.png images and write image summary JSON
  files to the corresponding subfolder of the output bucket

Image model: nlpconnect/vit-gpt2-image-captioning
Text model: facebook/bart-large-cnn (default) or t5-base

Environment variables:
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_REGION

Usage:
    python summarize_all.py --input-bucket <INPUT> --output-bucket <OUTPUT> \
        [--text-model facebook/bart-large-cnn] [--image-model nlpconnect/vit-gpt2-image-captioning]
"""

import argparse
import io
import json
import os
import sys
import tempfile
from typing import Dict, Iterable, List, Optional, Tuple

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


from PIL import Image

# Global lazy pipelines
_TEXT_SUMMARY_PIPELINE = None
_IMAGE_CAPTION_PIPELINE = None


def _device_map_or_none() -> Optional[str]:
    """Return a safe device_map value for transformers pipelines.

    If TRANSFORMERS_DEVICE_MAP is set to "auto" but Accelerate isn't installed,
    return None to avoid runtime errors requiring accelerate.
    """
    env_val = os.getenv("TRANSFORMERS_DEVICE_MAP", "auto").lower()
    if env_val in {"none", "cpu", "off"}:
        return None
    if env_val != "auto":
        return env_val
    try:
        import accelerate  # noqa: F401
        return "auto"
    except Exception:
        return None


def _print(msg: str) -> None:
    print(msg, flush=True)


def get_s3_client() -> boto3.client:
    region = os.getenv("AWS_REGION")
    config_kwargs: Dict[str, object] = {}
    if region:
        config_kwargs["region_name"] = region
    # Add some basic retries on top of botocore's standard strategy
    config_kwargs["retries"] = {"max_attempts": 5, "mode": "standard"}
    return boto3.client("s3", config=Config(**config_kwargs))


def list_folders(bucket: str, prefix: str = "") -> List[str]:
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
                    if not folder_prefix:
                        continue
                    discovered.append(folder_prefix)
                    stack.append(folder_prefix)
        except ClientError as e:
            _print(f"[ERROR] Failed listing folders in s3://{bucket}/{current_prefix}: {e}")
            continue

    # If there are files at root, include root as a folder token ""
    try:
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter="/"):
            if page.get("Contents"):
                if prefix == "":
                    discovered.insert(0, "")
                else:
                    root = prefix if prefix.endswith("/") else f"{prefix}/"
                    if root not in discovered:
                        discovered.insert(0, root)
                break
    except ClientError:
        pass

    # Unique + sorted for stable processing order
    uniq = sorted(set(discovered))
    return uniq


def list_files_in_folder(bucket: str, folder_prefix: str, extensions: Tuple[str, ...]) -> List[str]:
    """List files directly under a folder with specific extensions (non-recursive)."""
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
                lower = key.lower()
                # Skip generated summary files
                if lower.endswith("_summary.json") or lower.endswith("_text_summary.json"):
                    continue
                if any(lower.endswith(ext) for ext in extensions):
                    keys.append(key)
    except ClientError as e:
        _print(f"[ERROR] Failed listing files in s3://{bucket}/{normalized_prefix}: {e}")

    return sorted(keys)


def download_file(bucket: str, key: str, local_path: str) -> bool:
    s3 = get_s3_client()
    try:
        s3.download_file(bucket, key, local_path)
        _print(f"    [OK] Downloaded s3://{bucket}/{key}")
        return True
    except ClientError as e:
        _print(f"    [ERROR] Download failed for s3://{bucket}/{key}: {e}")
        return False


def upload_bytes(bucket: str, key: str, content_bytes: bytes, content_type: str = "application/json") -> bool:
    s3 = get_s3_client()
    try:
        s3.put_object(Bucket=bucket, Key=key, Body=content_bytes, ContentType=content_type)
        _print(f"    [OK] Uploaded -> s3://{bucket}/{key}")
        return True
    except ClientError as e:
        _print(f"    [ERROR] Upload failed for s3://{bucket}/{key}: {e}")
        return False


def _load_text_from_json(path: str) -> Optional[str]:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        _print(f"    [ERROR] Invalid JSON: {path}")
        return None
    except OSError as e:
        _print(f"    [ERROR] Failed reading file {path}: {e}")
        return None

    if data is None:
        return None
    if isinstance(data, str):
        text = data.strip()
        return text if text else None
    if isinstance(data, dict):
        for field in ["text", "content", "article", "body", "document", "data"]:
            value = data.get(field)
            if isinstance(value, str) and value.strip():
                return value.strip()
    try:
        s = str(data).strip()
        return s if s else None
    except Exception:
        return None


def _init_text_summarizer(model_name: str):
    global _TEXT_SUMMARY_PIPELINE
    if _TEXT_SUMMARY_PIPELINE is not None:
        return _TEXT_SUMMARY_PIPELINE
    from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
    _print(f"    [INFO] Loading text model: {model_name} ...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    _TEXT_SUMMARY_PIPELINE = pipeline(
        "summarization",
        model=model,
        tokenizer=tokenizer,
        device_map=_device_map_or_none(),
    )
    return _TEXT_SUMMARY_PIPELINE


def _init_image_captioner(model_name: str):
    global _IMAGE_CAPTION_PIPELINE
    if _IMAGE_CAPTION_PIPELINE is not None:
        return _IMAGE_CAPTION_PIPELINE
    from transformers import pipeline, AutoProcessor, VisionEncoderDecoderModel
    _print(f"    [INFO] Loading image model: {model_name} ...")
    # Use pipeline 'image-to-text' which internally handles processor/model combo
    _IMAGE_CAPTION_PIPELINE = pipeline(
        task="image-to-text",
        model=model_name,
        device_map=_device_map_or_none(),
    )
    return _IMAGE_CAPTION_PIPELINE


def _chunk_text_by_words(text: str, max_words: int) -> List[str]:
    words = text.split()
    if not words:
        return []
    return [" ".join(words[i : i + max_words]).strip() for i in range(0, len(words), max_words)]


def summarize_text_content(text: str, model_name: str) -> str:
    if not text or not text.strip():
        raise ValueError("Text is empty")
    # Light normalization: collapse whitespace and trim extremely long inputs
    cleaned = " ".join(text.split())
    # Cap to avoid pathological inputs; roughly first 250k characters
    if len(cleaned) > 250_000:
        cleaned = cleaned[:250_000]
    summarizer = _init_text_summarizer(model_name)
    # Conservative per-chunk size to avoid model overflow
    chunks = _chunk_text_by_words(cleaned, 800)
    if not chunks:
        raise ValueError("Text is empty after preprocessing")
    
    def safe_summarize(chunk_text: str, max_len: int, min_len: int) -> str:
        """Safely summarize with fallback strategies."""
        try:
            result = summarizer(
                chunk_text,
                max_length=max_len,
                min_length=min_len,
                do_sample=False,
                truncation=True,
            )
            if result and len(result) > 0:
                return result[0]["summary_text"].strip()
        except Exception as e:
            _print(f"    [WARN] Summarization failed: {e}")
        
        # Fallback 1: Try with smaller max_length
        try:
            result = summarizer(
                chunk_text[:1000],  # Truncate further
                max_length=150,
                min_length=20,
                do_sample=False,
                truncation=True,
            )
            if result and len(result) > 0:
                return result[0]["summary_text"].strip()
        except Exception:
            pass
        
        # Fallback 2: Return first few sentences
        sentences = chunk_text.split('. ')
        if len(sentences) >= 2:
            return '. '.join(sentences[:2]) + '.'
        return chunk_text[:200] + "..."
    
    if len(chunks) == 1:
        return safe_summarize(chunks[0], 220, 40)
    
    partials: List[str] = []
    for chunk in chunks:
        partials.append(safe_summarize(chunk, 220, 40))
    
    combined = "\n".join(partials)
    return safe_summarize(combined, 240, 60)


def caption_image(image_path: str, model_name: str) -> str:
    captioner = _init_image_captioner(model_name)
    try:
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            outputs = captioner(img)
    except OSError as e:
        raise ValueError(f"Unreadable image: {e}")
    if not outputs:
        raise ValueError("Empty caption output")
    # pipeline returns list of dicts with 'generated_text'
    text = outputs[0].get("generated_text", "").strip()
    if not text:
        raise ValueError("No generated_text in caption output")
    return text


def _derive_text_output_key(input_key: str) -> str:
    dir_prefix = "" if "/" not in input_key else input_key.rsplit("/", 1)[0] + "/"
    return f"{dir_prefix}article_text_summary.json"


def _derive_image_output_key(image_key: str, multiple_images: bool) -> str:
    dir_prefix = "" if "/" not in image_key else image_key.rsplit("/", 1)[0] + "/"
    if not multiple_images:
        return f"{dir_prefix}image_summary.json"
    base = os.path.splitext(os.path.basename(image_key))[0]
    return f"{dir_prefix}{base}_image_summary.json"


def process_bucket(input_bucket: str, output_bucket: str, text_model: str, image_model: str) -> None:
    _print(f"[START] Processing: s3://{input_bucket} -> s3://{output_bucket}")

    folders = list_folders(input_bucket, prefix="")
    if "" not in folders:
        folders = [""] + folders
    if not folders:
        _print("[WARN] No folders found in input bucket.")
        return

    for folder in folders:
        folder_name = folder if folder else "/"
        clean_folder_name = folder_name[:-1] if folder_name.endswith("/") else folder_name
        _print(f"Processing {clean_folder_name}...")

        # Text JSON (assume at most one primary JSON per folder, but handle many just in case)
        json_files = list_files_in_folder(input_bucket, folder, extensions=(".json",))
        # Filter out previously generated summaries explicitly
        json_files = [k for k in json_files if not k.lower().endswith(("_summary.json", "_text_summary.json"))]

        for idx, json_key in enumerate(json_files, start=1):
            with tempfile.TemporaryDirectory() as tmpdir:
                local_json = os.path.join(tmpdir, os.path.basename(json_key))
                if not download_file(input_bucket, json_key, local_json):
                    continue
                text = _load_text_from_json(local_json)
                if not text:
                    _print(f"  Skipped {os.path.basename(json_key)} (empty JSON)")
                    continue
                try:
                    summary = summarize_text_content(text, text_model)
                except Exception as e:
                    _print(f"  Error summarizing {os.path.basename(json_key)}: {e}")
                    continue
                out_doc = {
                    "filename": os.path.basename(json_key),
                    "summary_type": "text",
                    "summary": summary,
                }
                out_bytes = json.dumps(out_doc, ensure_ascii=False, indent=2).encode("utf-8")
                out_key = _derive_text_output_key(json_key)
                upload_bytes(output_bucket, out_key, out_bytes)
                _print(f"  Summarized {os.path.basename(json_key)} ✅")

        # Image files
        image_files = list_files_in_folder(input_bucket, folder, extensions=(".jpg", ".jpeg", ".png"))
        multiple_images = len(image_files) > 1
        for image_key in image_files:
            with tempfile.TemporaryDirectory() as tmpdir:
                local_image = os.path.join(tmpdir, os.path.basename(image_key))
                if not download_file(input_bucket, image_key, local_image):
                    continue
                try:
                    caption = caption_image(local_image, image_model)
                except Exception as e:
                    _print(f"  Error captioning {os.path.basename(image_key)}: {e}")
                    continue
                out_doc = {
                    "filename": os.path.basename(image_key),
                    "summary_type": "image",
                    "summary": caption,
                }
                out_bytes = json.dumps(out_doc, ensure_ascii=False, indent=2).encode("utf-8")
                out_key = _derive_image_output_key(image_key, multiple_images)
                upload_bytes(output_bucket, out_key, out_bytes)
                _print(f"  Summarized {os.path.basename(image_key)} ✅")

    _print("[DONE] All folders processed.")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize JSON text and caption images from S3 folders")
    
    # Set default buckets from environment variables or use hardcoded defaults
    default_input_bucket = os.getenv("INPUT_BUCKET", "your-default-input-bucket")
    default_output_bucket = os.getenv("OUTPUT_BUCKET", "your-default-output-bucket")
    
    parser.add_argument("--input-bucket", default=default_input_bucket, help="S3 input bucket")
    parser.add_argument("--output-bucket", default=default_output_bucket, help="S3 output bucket")
    parser.add_argument("--text-model", default=os.getenv("SUMMARY_MODEL", "facebook/bart-large-cnn"), help="HF text model")
    parser.add_argument(
        "--image-model",
        default=os.getenv("IMAGE_MODEL", "nlpconnect/vit-gpt2-image-captioning"),
        help="HF image captioning model",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    try:
        process_bucket(args.input_bucket, args.output_bucket, text_model=args.text_model, image_model=args.image_model)
        return 0
    except KeyboardInterrupt:
        _print("[INTERRUPTED] Exiting.")
        return 130
    except Exception as e:
        _print(f"[FATAL] Unhandled error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())


