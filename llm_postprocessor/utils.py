import copy
import re
import unicodedata

def merge_dict(template, start_idx_list):
    merged_dict = {}
    for start_idx in start_idx_list:
        json_filename = template.format(start_idx=start_idx)
        with open(json_filename, 'r') as f:
            content = json.load(f)
            merged_dict = merged_dict | content

    return merged_dict

# ALLOWED_CHARS_PATTERN = r"[a-zA-Z0-9\s.,:;\'\"‘’“”!?()\[\]\-]"
# def contains_non_english(s):
#     return bool(re.search(f"[^{ALLOWED_CHARS_PATTERN}]", s))
ALLOWED_CHARS_PATTERN = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \t\n\r.,:;'\"‘’“”!?()-[]|+=`&><~$°º"
def contains_non_english(s):
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
            return True
    return False


def contains_non_latin_homoglyphs(s):
    for c in s:
        # Normalize the character
        normalized = unicodedata.normalize('NFKC', c)

        # Check if it's a standard Latin letter/digit or common punctuation
        if normalized in ALLOWED_CHARS_PATTERN:
            continue

        # Reject characters not from the Latin script
        try:
            name = unicodedata.name(c)
        except ValueError:
            return True  # Unnamed character (likely non-printable or control)

        # Check script family — allow only Latin and common punctuation
        if not name.startswith("LATIN") and not name.startswith("DIGIT") and not unicodedata.category(c).startswith("P"):
            return True
    return False

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
        processed_tracks.append(k)
        new_dict[k] = {}
        new_dict[k]['metadata'] = v['metadata']
        new_dict[k]['captions'] = []
        max_iteration = len(v['captions'])
        flag = False
        for idx, caption in enumerate(v['captions']):
            if len(caption.split()) < MIN_CAPTION_LENGTH or len(caption.split()) > MAX_CAPTION_LENGTH:
                flag = True
                continue
            # checking if there are non-english characters in the caption
            # step 1: check if the caption contains homoglyphs
            if contains_non_latin_homoglyphs(caption):
                caption = replace_homoglyphs(caption)
                flag = True
                continue
            # step 2: check if the caption contains other non-english characters
            if contains_non_english(caption):
                flag = True
                continue
            new_dict[k]['captions'].append(caption)

            if len(new_dict[k]['captions']) == 2:
                flag = False
                break
            elif idx == max_iteration - 1 and len(new_dict[k]['captions']) < 2:
                flag = True
                print(f"Run out of captions for {k}, only {len(new_dict[k]['captions'])} valid captions found.")
        if flag:
            problem_tracks.append(k)
        else:
            debug_list.remove(k)

    # check if all tracks are processed
    print(f"Number of processed tracks: {len(processed_tracks)}")
    print(f"Number of tracks in the original dictionary: {len(filtered_dict)}")
    assert len(processed_tracks) == len(filtered_dict), "Not all tracks are processed"
    return new_dict, problem_tracks

# anormality detection
# check if the string in the list per item in the dict is not too short (< 10 words) or too long (> 100 words)
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