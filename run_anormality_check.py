import json
import logging
from pathlib import Path
from llm_postprocessor.cli import run_anormality_check
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
    run_anormality_check()
if __name__ == "__main__":
    main()