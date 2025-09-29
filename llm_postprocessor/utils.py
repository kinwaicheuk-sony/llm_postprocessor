import copy
import re
import unicodedata
from tqdm import tqdm
from pathlib import Path
import json

def merge_dict(template, start_idx_list):
    merged_dict = {}
    for start_idx in start_idx_list:
        json_filename = template.format(start_idx=start_idx)
        with open(json_filename, 'r') as f:
            content = json.load(f)
            merged_dict = merged_dict | content

    return merged_dict

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


# ALLOWED_CHARS_PATTERN = r"[a-zA-Z0-9\s.,:;\'\"‘’“”!?()\[\]\-]"
# def contains_non_english(s):
#     return bool(re.search(f"[^{ALLOWED_CHARS_PATTERN}]", s))
ALLOWED_CHARS_PATTERN = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \t\n\r.,:;'\"‘’“”!?()-[]|+=`&><~$°º"
def contains_non_english(s):
    counter = 0
    flag = False
    for c in s:
        if c in ALLOWED_CHARS_PATTERN:
            continue
        if unicodedata.category(c).startswith("P"):  # Punctuation
            continue
        if unicodedata.category(c).startswith("Z"):  # Space separators
            continue
        # Reject anything that is not Latin
        name = unicodedata.name(c, "")
        if not name.startswith("LATIN") and not name.startswith("DIGIT"):
            flag = True
            counter += 1
    return flag, counter


def contains_non_latin_homoglyphs(s):
    counter = 0
    flag = False    
    for c in s:
        # Normalize the character7
        normalized = unicodedata.normalize('NFKC', c)

        # Check if it's a standard Latin letter/digit or common punctuation
        if normalized in ALLOWED_CHARS_PATTERN:
            continue

        # Reject characters not from the Latin script
        try:
            name = unicodedata.name(c)
        # Check script family — allow only Latin and common punctuation
            if not name.startswith("LATIN") and not name.startswith("DIGIT") and not unicodedata.category(c).startswith("P"):
                flag = True
                counter += 1
        except ValueError:
            counter += 1 
            flag = True  # Unnamed character (likely non-printable or control)


    return flag, counter

def find_non_latin_homoglyphs(s):
    non_latin_chars = []

    for c in s:
        normalized = unicodedata.normalize('NFKC', c)

        if normalized in ALLOWED_CHARS_PATTERN:
            continue

        try:
            name = unicodedata.name(c)
        except ValueError:
            non_latin_chars.append((c, '<unnamed>'))
            continue

        # FIXED: Check category for punctuation, not name
        if not name.startswith("LATIN") and not name.startswith("DIGIT") and not unicodedata.category(c).startswith("P"):
            non_latin_chars.append((c, name))

    return non_latin_chars

# # export file_list into txt
# with open('kpm_train_set.txt', 'w') as f:
#     for item in file_list:
#         f.write(f"{item}\n")

def self_fix(filtered_dict):
    new_dict = {}
    problem_tracks = []
    processed_tracks = []
    debug_list = list(filtered_dict.keys())
    
    for k, v in filtered_dict.items():
        caption = replace_homoglyphs(v['text']) # fixing homoglyphs errors first
        new_dict[k] = v
        new_dict[k]['text'] = caption
        flag = False


    return new_dict

# anormality detection
# check if the string in the list per item in the dict is not too short (< 10 words) or too long (> 100 words)
def anormality_check_dict(filtered_dict, MIN_CAPTION_LENGTH=5, MAX_CAPTION_LENGTH=200):
    anormality_list = []
    non_english_list = []
    homoglyphs_list = []
    for k, v in tqdm(filtered_dict.items()):
        for idx, caption in enumerate(v['captions']):
            if len(caption.split()) < MIN_CAPTION_LENGTH or len(caption.split()) > MAX_CAPTION_LENGTH:
                anormality_list.append((k, caption, idx))
            # checking if there are non-english characters in the caption
            # step 1: check if the caption contains homoglyphs
            if contains_non_latin_homoglyphs(caption):
                caption = replace_homoglyphs(caption)
                homoglyphs_list.append((k, caption, idx))
            # step 2: check if the caption contains other non-english characters
            if contains_non_english(caption):
                non_english_list.append((k, caption, idx))


    return anormality_list, non_english_list, homoglyphs_list


def anormality_check_musicllm(filtered_dict, MIN_CAPTION_LENGTH=5, MAX_CAPTION_LENGTH=200, tolerance=5):
    anormality_list = []
    non_english_list = []
    homoglyphs_list = []
    new_dict = {}
    for k, v in tqdm(filtered_dict.items()):
        tmp_caption = [v['text']] # dirty hack to fit musicLLM
        for idx, caption in enumerate(tmp_caption):
            english_check = contains_non_english(caption) # Boolean, count
            latin_char_check = contains_non_latin_homoglyphs(caption)

            if len(caption.split()) < MIN_CAPTION_LENGTH or len(caption.split()) > MAX_CAPTION_LENGTH:
                anormality_list.append((k, caption, len(caption.split(' '))))
                continue
            # checking if there are non-english characters in the caption
            # step 1: check if the caption contains homoglyphs
            if latin_char_check[0]:
                homoglyphs_list.append((k, caption, latin_char_check[1]))
            # step 2: check if the caption contains other non-english characters
            if english_check[0]:
                non_english_list.append((k, caption, english_check[1]))

            if english_check[1] > tolerance or latin_char_check[1] > tolerance:
                pass # doesn't not include it in the new dict
            else:
                new_dict[k] = v


    return anormality_list, non_english_list, homoglyphs_list, new_dict

def anormality_check(filtered_dict):
    anormality_list = []
    non_english_list = []
    homoglyphs_list = []
    for k, v in filtered_dict.items():
        for idx, caption in enumerate(v['captions']):
            if len(caption.split()) < MIN_CAPTION_LENGTH or len(caption.split()) > MAX_CAPTION_LENGTH:
                anormality_list.append((k, caption, idx))
            # checking if there are non-english characters in the caption
            # step 1: check if the caption contains homoglyphs
            if contains_non_latin_homoglyphs(caption):
                caption = replace_homoglyphs(caption)
                homoglyphs_list.append((k, caption, idx))
            # step 2: check if the caption contains other non-english characters
            if contains_non_english(caption):
                non_english_list.append((k, caption, idx))


    return anormality_list, non_english_list, homoglyphs_list

def fixing_anormality(filtered_dict, anormality_list=None, patch_dict=None):
    ignored_keys = []
    # fixing long caption
    for key, caption, loc in anormality_list:
        try:
            current_item = patch_dict[key]
            if len(current_item['captions']) > 2:
                # check if the third caption is not too short or too long
                for new_caption in current_item['captions']:
                    if len(new_caption.split()) >= MIN_CAPTION_LENGTH and len(new_caption.split()) <= MAX_CAPTION_LENGTH and not contains_non_english(new_caption):
                        filtered_dict[key]['captions'][loc] = new_caption
                        # remove the item from the patch_dict
                        patch_dict[key]['captions'].remove(new_caption)
                        break
            else:
                print('not enough alternative captions for long caption fix')
        except KeyError:
            # print(f"Key {key} not found in patch_dict, skipping.")
            ignored_keys.append(key)

    return ignored_keys

homoglyph_map = {
    '\u0397': 'H',  # Greek Capital Eta
    '\u0410': 'A',  # Cyrillic Capital A
    'Α': 'A',  # Greek Capital Alpha
    '\u0415': 'E',  # Cyrillic Capital E
    '\u041E': 'O',  # Cyrillic Capital O
    '\u0420': 'P',  # Cyrillic Capital P
    '\u0430': 'a',  # Cyrillic small a
    '\u03B5': 'e',  # Greek small epsilon
    '\u0406': 'I',  # Cyrillic capital І
    '\u0456': 'i',  # Cyrillic small і
    '\u03C1': 'p',  # Greek rho
    'р': 'p',  # Cyrillic small p
    'с': 'c',  # Cyrillic small c
    'е': 'e',  # Cyrillic small e
    '\u043E': 'o',  # Cyrillic o
    '\u03BF': 'o',  # Greek omicron
    'у': 'y',  # Cyrillic small y
    '�': '', # remove this symbol
    'м': '' # remove this symbol that always appear in the caption
    # ... add more as needed
}

def replace_homoglyphs(text):
    return ''.join(homoglyph_map.get(c, c) for c in text)

def export_redo_txt(problem_list, output_file='redo_list'):
    redo_list = []
    for key, _, _ in problem_list:
        redo_list.append(key)
    # export it to txt file
    with open(f'{output_file}.txt', 'w') as f:
        for item in redo_list:
            f.write(f"{item}\n")