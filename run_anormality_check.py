import argparse
import json
import logging
from pathlib import Path

from llm_postprocessor.utils import self_fix, anormality_check_musicllm


def load_jsonl(path: Path) -> dict:
    """Load a JSONL file into a dict keyed by question_id."""
    result = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            qid = data.get("question_id")
            if qid is None:
                logging.warning("Skipping entry without question_id: %s", data)
                continue
            result[qid] = data
    return result


def main():
    parser = argparse.ArgumentParser(description="Run anormality check on JSONL data.")
    parser.add_argument("--input", required=True, type=Path, help="Path to input JSONL file")
    parser.add_argument("--min_caption_length", type=int, default=5, help="Minimum caption length")
    parser.add_argument("--max_caption_length", type=int, default=200, help="Maximum caption length")
    parser.add_argument("--output", type=Path, help="Optional path to write results as JSON")
    parser.add_argument("--tolerance", type=int, default=1, help="Number of foreign characters are allowed in a caption before filtering out")
    parser.add_argument("--self_fix", action="store_true", help="Apply self-fixing minor mistakes to captions")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    logging.info("Loading input file: %s", args.input)
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

    if args.output:
        logging.info("Writing results to %s", args.output)
        with args.output.open("w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    else:
        logging.info("Results:\n%s", json.dumps(results, indent=2, ensure_ascii=False))

    # append the string `filtered_` to the input filename
    filtered_output_path = args.input.parent / f"filtered_{args.input.name}"
    with filtered_output_path.open("w", encoding="utf-8") as f:
        json.dump(filtered_dict, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()