import argparse
from pathlib import Path
from .utils import load_jsonl
import json

def fix_llava_json():
    parser = argparse.ArgumentParser(description="Run anormality check on JSONL data.")
    parser.add_argument("input", type=Path, help="Path to input JSONL file")

    args = parser.parse_args()
    data = load_jsonl(args.input)

    output_path = args.input.parent / f"fixed_{args.input.stem}.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)