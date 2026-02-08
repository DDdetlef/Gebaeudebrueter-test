import re
import time
from typing import Tuple, Dict, Optional, Callable

def _normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()

def sanitize_street(s: str) -> Tuple[str, Dict[str,int], str]:
    """Return (cleaned_street, flags, original).

    Flags: has_comma, has_slash, has_range, multiple_numbers, multiple_streets, kept_text_after_number
    """
    original = s or ''
    s = _normalize_ws(s)
    # remove parenthetical notes
    s = re.sub(r"\([^)]*\)", "", s).strip()
    flags = {
        'has_comma': 1 if ',' in original else 0,
        'has_slash': 1 if re.search(r'[;/|]', original) else 0,
        'has_range': 1 if re.search(r'\d+\s*[-–/]\s*\d+', original) else 0,
        'multiple_numbers': 0,
        'multiple_streets': 0,
        'kept_text_after_number': 0,
    }
    parts = re.split(r"[;/|]", s)
    flags['multiple_streets'] = 1 if len(parts) > 1 else 0
    pick = None
    for p in parts:
        p2 = _normalize_ws(p)
        if re.search(r"\d", p2):
            pick = p2
            break
    if pick is None and parts:
        pick = _normalize_ws(parts[0])
    pick = pick or ''

    # normalize misplaced commas like '30 , Heckmann' -> '30, Heckmann'
    pick = re.sub(r"\s+,\s*", ", ", pick)

    # extract house number and trailing text
    m = re.search(r"^(.*?\D)?(\d+[A-Za-z]?)(.*)$", pick)
    cleaned = pick
    if m:
        street_before = (m.group(1) or '').strip()
        number = m.group(2).strip()
        rest = _normalize_ws(m.group(3) or '')
        nums = re.findall(r"\d+", pick)
        flags['multiple_numbers'] = 1 if len(nums) > 1 else 0

        # Blacklist tokens that indicate non-address suffixes
        blacklist = re.compile(r"\b(hotel|schule|grundschule|kita|kindergarten|hinterhof|hof|höfe|hofe|zentrum|center|apartment|wohnung|büro|restaurant|hostel|hostal|ibis)\b", re.IGNORECASE)
        street_kw = re.compile(r"\b(strasse|straße|str\.?|weg\b|allee\b|platz\b|gasse\b|ring\b|chaussee\b|ufer\b)\b", re.IGNORECASE)

        # Determine whether rest is descriptive text or a house-number suffix.
        def _rest_is_house_suffix(text: str) -> bool:
            t = (text or '').strip()
            if not t:
                return False
            # single-letter tokens or letter ranges like 'a-c', 'a,b,d', '+b' count as suffix
            # allow plus or hyphen/comma separators
            return bool(re.match(r"^[\s,]*[+\-]?[A-Za-z](?:\s*[-–]\s*[A-Za-z])?(?:\s*(?:,|\s)\s*[+\-]?[A-Za-z](?:\s*[-–]\s*[A-Za-z])?)*[\s,]*$", t))

        # If rest begins with a numeric range (e.g. '-13' or '/13'), fold it into the house number
        range_match = re.match(r"^\s*([-–/])\s*(\d+[A-Za-z]?)", rest)
        if range_match:
            sep = range_match.group(1)
            range_num = range_match.group(2)
            # append normalized range to number (e.g. '10-13')
            number = f"{number}{sep}{range_num}"
            # remove the consumed part from rest
            rest = _normalize_ws(rest[range_match.end():] or '')
            flags['has_range'] = 1

        # Decide if rest should be considered descriptive text after number.
        is_house_suffix = _rest_is_house_suffix(rest)
        # If rest still contains digits after attempting to consume a numeric range, treat it conservatively
        if rest and not is_house_suffix and not street_kw.search(rest) and not re.search(r"\d", rest):
            flags['flag_has_text_after_number'] = 1
        else:
            flags['flag_has_text_after_number'] = 0

        # Per policy: do not keep any trailing descriptive text after the house number in cleaned street.
        cleaned = f"{street_before} {number}".strip()
    else:
        cleaned = pick.split(',')[0].strip()

    # final whitespace normalize
    cleaned = _normalize_ws(cleaned)
    return cleaned, flags, original

def geocode_with_fallbacks(geocode_callable: Callable[[str], Optional[object]], cleaned_street: str, plz: str, ort: str, max_attempts: int = 3, pause: float = 1.0):
    """Try geocoding with several address variants using provided geocode callable.

    geocode_callable should accept an address string and return a location-like object or None.
    Returns (location, used_address)
    """
    variants = []
    cleaned = cleaned_street or ''
    # prefer full cleaned
    if cleaned:
        variants.append(f"{cleaned}, {plz}, {ort}, Deutschland")
        # try without any suffix after comma
        if ',' in cleaned:
            variants.append(f"{cleaned.split(',')[0].strip()}, {plz}, {ort}, Deutschland")
        # try street+num only (strip trailing text)
        m = re.match(r"^(.*?\D)?(\d+[A-Za-z0-9\-–/]*)(.*)$", cleaned)
        if m:
            street_before = (m.group(1) or '').strip()
            number_raw = m.group(2).strip()
            # when number contains a range (e.g. '10-13' or '/13'), use the first number for geocoding
            num_match = re.match(r"^(\d+[A-Za-z]?)", number_raw)
            if num_match:
                number = num_match.group(1)
            else:
                number = number_raw
            variants.append(f"{street_before} {number}, {plz}, {ort}, Deutschland")
            variants.append(f"{street_before} {number} {ort}, Deutschland")
    # fallback to plz+ort
    variants.append(f"{plz}, {ort}, Deutschland")

    for addr in variants:
        addr = addr.strip()
        if not addr:
            continue
        attempt = 0
        while attempt < max_attempts:
            try:
                loc = geocode_callable(addr)
            except Exception:
                loc = None
            if loc:
                return loc, addr
            attempt += 1
            time.sleep(pause)
    return None, None
