import re

SUPPORTED_CAPTION_EXTENSIONS = ['.txt', '.caption']

_TEXT_NORMALIZATION = {
    r"\:(\s+)?\d+(\.\d+)?": " ",  # remove weights ':1' and ':1.0', etc
    r"\\\((\s+)?": "_---",  # replace escaped brackets (
    r"(\s+)?\\\)": "---_",  # replace escaped brackets )
    r"\\\[(\s+)?": "___-",  # replace escaped brackets [
    r"(\s+)?\\\]": "-___",  # replace escaped brackets ]
    r"[\(\)\[\]]": " ",  # remove left over brackets
    r"—": "-",
    "'s": "_--_",  # plural
    "s'": "-__-",  # plural
    "<.+?>": " ",  # remove loras - maybe find a better way to handle loras?
    r"\\": "",  # remove slashes left over from escaped
    r"\:": ", ",  # replace left colons as commas, can't trained merged tags
    r"\|": ", ",  # replace pipes with commas, can't train dynamic or merged tags
    r"\*": " ",  # remove asterisks
    r"\.(?!\w)": ", ",  # remove periods but preserve things like y.o or 1.8
    "[;'\"+]": ", ",  # remove extraneous punctuation
    "[{}]": " ",  # remove brackets
    r"\s+": " ",  # remove extra whitespace
    "_--_": "'s",  # reverse plural
    "-__-": "'s",  # reverse plural
    "_---": "\\(",  # reverse escaped brackets (
    "---_": "\\)",  # reverse escaped brackets )
    "___-": "\\[",  # reverse escaped brackets [
    "-___": "\\]",  # reverse escaped brackets ]
}


def is_caption_text(filepath: str) -> bool:
    for extension in SUPPORTED_CAPTION_EXTENSIONS:
        if filepath.endswith(extension):
            return True

    return False


def load_text_from_file(filepath: str) -> str:
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read().strip()


def normalize_caption_text(text: str) -> str:
    normalized_tags: list[str] = []
    caption_tags: list[str] = bulk_text_replacement(text, _TEXT_NORMALIZATION)

    for caption_tag in caption_tags:
        if len(caption_tag) > 0 and caption_tag not in normalized_tags:
            normalized_tags.append(caption_tag)

    return ", ".join(normalized_tags).strip().lower()


def bulk_text_replacement(text: str, replacements: dict[str, str]) -> list[str]:
    for s, r in replacements.items():
        text = re.sub(s, r, text, flags=re.IGNORECASE)

    normalized_tags: list[str] = []
    caption_tags: list[str] = text.split(',')

    for caption_tag in caption_tags:
        caption_tag = caption_tag.strip()

        if caption_tag != '':
            normalized_tags.append(caption_tag)

    return normalized_tags
