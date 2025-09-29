import argparse
from pathlib import Path
from .utils import load_jsonl, self_fix, anormality_check_musicllm
import json
import logging

def fix_llava_json():
    parser = argparse.ArgumentParser(description="Run anormality check on JSONL data.")
    parser.add_argument("input", type=Path, help="Path to input JSONL file")

    args = parser.parse_args()
    data = load_jsonl(args.input)

    output_path = args.input.parent / f"fixed_{args.input.stem}.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def run_anormality_check():
    parser = argparse.ArgumentParser(description="Run anormality check on JSONL data.")
    parser.add_argument("--input", required=True, type=Path, help="Path to input JSONL file")
    parser.add_argument("--min_caption_length", type=int, default=5, help="Minimum caption length")
    parser.add_argument("--max_caption_length", type=int, default=200, help="Maximum caption length")
    parser.add_argument("--output_folder", type=Path, help="Optional path to write results as JSON")
    parser.add_argument("--tolerance", type=int, default=1, help="Number of foreign characters are allowed in a caption before filtering out")
    parser.add_argument("--self_fix", action="store_true", help="Apply self-fixing minor mistakes to captions")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    logging.info("Loading input file: %s", args.input)
    try:
        # loading json normally
        with args.input.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        logging.warning("Failed to load JSON normally, trying to patch the llava json output...")
        data = load_jsonl(args.input)
    logging.info("Loaded %d records", len(data))

    if args.self_fix:
        logging.info("Applying self-fix to captions...")
        data = self_fix(data)

    logging.info("Running anormality check...")
    anormality_list, non_english_list, homoglyphs_list, filtered_dict = anormality_check_musicllm(
        data,
        args.min_caption_length,
        args.max_caption_length,
        tolerance=args.tolerance
    )

    results = {
        "anormality_list": anormality_list,
        "non_english_list": non_english_list,
        "homoglyphs_list": homoglyphs_list,
    }


    if args.output_folder:
        # create output folder if not exists
        args.output_folder.mkdir(parents=True, exist_ok=True)
        filtered_output_path = args.output_folder / f"filtered_{args.input.name}"
        problem_output_path = args.output_folder / f"problem_{args.input.name}"
    else:
        filtered_output_path = args.input.parent / f"filtered_{args.input.name}"
        problem_output_path = args.input.parent / f"problem_{args.input.name}"

    # exporting results
    logging.info("Writing results to %s", problem_output_path)
    with problem_output_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # append the string `filtered_` to the input filename
    with filtered_output_path.open("w", encoding="utf-8") as f:
        json.dump(filtered_dict, f, indent=2, ensure_ascii=False)