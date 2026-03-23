from __future__ import annotations

from datetime import datetime
from functools import lru_cache
import re
import unicodedata
from typing import Callable, Iterable

from app.models import DocumentType, OCRFields

CURP_REGEX = re.compile(r"[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d")
DATE_REGEX = re.compile(r"\b(\d{2}[\/-]\d{2}[\/-]\d{4})\b")
VALIDITY_REGEX = re.compile(r"\b(\d{2}[\/-]\d{2}[\/-]\d{4}|\d{4})\b")
MRZ_NAME_REGEX = re.compile(r"([A-Z]{2,}(?:<[A-Z]{2,})+)<<([A-Z]{2,}(?:<[A-Z]{2,})*)")
MRZ_DATES_REGEX = re.compile(r"(?P<birth>\d{6})\d[HM](?P<valid>\d{6})")
ADDRESS_HINT_REGEX = re.compile(r"\b(PRIV|CALLE|AV|AVENIDA|FRACC|COL|BOULEVARD|BLVD|MZ|LT|NUM|NO|C\.?P)\b")
ADDRESS_BLOCKLIST = ("CURP", "CLAVE", "ELECTOR", "SEXO", "VIGENCIA", "NACIMIENTO", "IDMEX")
VALIDITY_YEAR_REGEX = re.compile(r"\b(19\d{2}|20\d{2}|21\d{2})\b")

NAME_STOP_KEYWORDS = (
    "DOMICILIO",
    "DIRECCION",
    "CURP",
    "CLAVE",
    "FECHA",
    "NACIMIENTO",
    "VIGENCIA",
    "SECCION",
    "IDMEX",
)
NAME_CONNECTOR_TOKENS = {"DE", "DEL", "LA", "LAS", "LOS", "MC", "VON", "VAN"}
NAME_BLOCKED_TOKENS = {
    "COL",
    "FRACC",
    "CALLE",
    "AV",
    "AVENIDA",
    "BLVD",
    "BOULEVARD",
    "MEXICO",
    "DOMICILIO",
    "DIRECCION",
}

KEYWORD_CHAR_ALIASES: dict[str, str] = {
    "A": "A4",
    "B": "B8",
    "E": "E3",
    "G": "G6",
    "I": "I1L",
    "L": "L1I",
    "O": "O0",
    "S": "S5",
    "T": "T7",
}

DIGIT_TO_LETTER: dict[str, str] = {
    "0": "O",
    "1": "I",
    "2": "Z",
    "3": "E",
    "4": "A",
    "5": "S",
    "6": "G",
    "7": "T",
    "8": "B",
}

LETTER_TO_DIGIT: dict[str, str] = {
    "O": "0",
    "Q": "0",
    "I": "1",
    "L": "1",
    "Z": "2",
    "S": "5",
    "G": "6",
    "B": "8",
}

CURP_LETTER_POSITIONS = {0, 1, 2, 3, 11, 12, 13, 14, 15}
CURP_DIGIT_POSITIONS = {4, 5, 6, 7, 8, 9, 17}


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text.upper())
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def _line_iter(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


@lru_cache(maxsize=256)
def _keyword_pattern(keyword: str) -> re.Pattern[str]:
    chunks: list[str] = []
    for char in keyword:
        if char.isspace():
            chunks.append(r"[\s\W_]*")
            continue
        aliases = KEYWORD_CHAR_ALIASES.get(char, char)
        chunks.append(rf"[{re.escape(aliases)}][\s\W_]*")
    return re.compile("".join(chunks), flags=re.IGNORECASE)


def _keyword_match(line: str, keyword: str) -> re.Match[str] | None:
    return _keyword_pattern(keyword).search(line)


def _line_contains_keywords(line: str, keywords: tuple[str, ...]) -> bool:
    return any(_keyword_match(line, keyword) for keyword in keywords)


def _looks_like_person_name(value: str) -> bool:
    if "," in value:
        return False

    normalized = re.sub(r"[^A-Z ]", " ", value)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if not normalized:
        return False
    if ADDRESS_HINT_REGEX.search(normalized):
        return False

    tokens = [token for token in normalized.split(" ") if len(token) >= 2]
    if len(tokens) < 2 or len(tokens) > 6:
        return False
    if sum(len(token) for token in tokens) < 8:
        return False

    letters = sum(ch.isalpha() for ch in value)
    if letters / max(1, len(value)) < 0.6:
        return False

    blocked = {
        "CURP",
        "CLAVE",
        "CERTIFICADA",
        "REGISTRO",
        "ENTIDAD",
        "GOBIERNO",
        "MEXICO",
        "CONSTANCIA",
        "POBLACION",
        "COL",
        "FRACC",
        "CALLE",
        "AVENIDA",
        "DOMICILIO",
        "DIRECCION",
        "MEXICO",
        "MOR",
        "CDMX",
        "DGO",
        "GTO",
        "PUE",
        "OAX",
        "CHIH",
        "COAH",
        "GRO",
        "HGO",
        "JAL",
        "MEX",
        "MICH",
        "QRO",
        "QROO",
        "SLP",
        "SIN",
        "SON",
        "TAB",
        "TLAX",
        "VER",
        "YUC",
        "ZAC",
    }
    if any(token in blocked for token in tokens):
        return False
    return True


def _value_after_keywords(
    lines: Iterable[str],
    keywords: tuple[str, ...],
    *,
    max_lookahead: int = 5,
    validator: Callable[[str], bool] | None = None,
    stop_keywords: tuple[str, ...] = (),
) -> str | None:
    lines_list = list(lines)
    for idx, line in enumerate(lines_list):
        for keyword in keywords:
            match = _keyword_match(line, keyword)
            if not match:
                continue

            candidate = line[match.end() :].strip(" :.-")
            if not candidate and ":" in line:
                candidate = line.split(":", maxsplit=1)[1].strip(" :.-")

            if candidate and (validator is None or validator(candidate)):
                return candidate

            fallback: str | None = None
            for offset in range(1, max_lookahead + 1):
                next_idx = idx + offset
                if next_idx >= len(lines_list):
                    break
                next_value = lines_list[next_idx].strip(" :.-")
                if not next_value:
                    continue
                if stop_keywords and _line_contains_keywords(next_value, stop_keywords):
                    break
                if validator is None:
                    return next_value
                if validator(next_value):
                    return next_value
                if fallback is None and len(next_value) > 2:
                    fallback = next_value

            if fallback and validator is None:
                return fallback
    return None


def _parse_compact_birth_date(compact: str) -> str | None:
    if len(compact) != 8 or not compact.isdigit():
        return None

    day = int(compact[0:2])
    month = int(compact[2:4])
    year = int(compact[4:8])
    current_year = datetime.now().year
    if year < 1900 or year > current_year:
        return None

    try:
        parsed = datetime(year=year, month=month, day=day)
    except ValueError:
        return None
    return parsed.strftime("%d/%m/%Y")


def _compact_birth_candidates(token: str) -> list[str]:
    if len(token) == 8:
        return [token]
    if len(token) != 9:
        return []

    preferred_drop_indexes = [2, 4, 5, 3, 1, 0, 6, 7, 8]
    candidates: list[str] = []
    seen: set[str] = set()
    for index in preferred_drop_indexes:
        candidate = token[:index] + token[index + 1 :]
        if candidate in seen:
            continue
        seen.add(candidate)
        candidates.append(candidate)
    return candidates


def _extract_compact_birth_date(value: str) -> str | None:
    for token in re.findall(r"\d{8,9}", value):
        for candidate in _compact_birth_candidates(token):
            parsed = _parse_compact_birth_date(candidate)
            if parsed:
                return parsed
    return None


def _normalize_curp_candidate(candidate: str) -> str | None:
    if len(candidate) != 18:
        return None

    normalized_chars: list[str] = []
    for index, char in enumerate(candidate):
        if index in CURP_LETTER_POSITIONS:
            normalized_chars.append(DIGIT_TO_LETTER.get(char, char))
        elif index in CURP_DIGIT_POSITIONS:
            normalized_chars.append(LETTER_TO_DIGIT.get(char, char))
        elif index == 10:
            normalized_chars.append(char if char in {"H", "M"} else char)
        else:
            normalized_chars.append(char)

    normalized_candidate = "".join(normalized_chars)
    if CURP_REGEX.fullmatch(normalized_candidate):
        return normalized_candidate
    return None


def _extract_curp(normalized_text: str) -> str | None:
    compact_chunks = re.findall(r"[A-Z0-9]{18,}", re.sub(r"[^A-Z0-9]", " ", normalized_text))

    for chunk in compact_chunks:
        max_start = len(chunk) - 18
        for start in range(max_start + 1):
            candidate = chunk[start : start + 18]
            normalized_candidate = _normalize_curp_candidate(candidate)
            if normalized_candidate:
                return normalized_candidate
    return None


def _extract_birth_date(lines: list[str], normalized_text: str) -> str | None:
    birth_keywords = ("NACIMIENTO", "NAC1MIENTO", "NACIMENTO", "NAC1MENTO")
    for idx, line in enumerate(lines):
        if _line_contains_keywords(line, birth_keywords):
            match = DATE_REGEX.search(line)
            if match:
                return match.group(1)
            compact_match = _extract_compact_birth_date(line)
            if compact_match:
                return compact_match
            if idx + 1 < len(lines):
                next_line = lines[idx + 1]
                next_match = DATE_REGEX.search(next_line)
                if next_match:
                    return next_match.group(1)
                next_compact_match = _extract_compact_birth_date(next_line)
                if next_compact_match:
                    return next_compact_match

    match = DATE_REGEX.search(normalized_text)
    return match.group(1) if match else None


def _extract_validity(lines: list[str]) -> str | None:
    validity_keywords = ("VIGENCIA", "VENCE")
    for idx, line in enumerate(lines):
        if _line_contains_keywords(line, validity_keywords):
            years = VALIDITY_YEAR_REGEX.findall(line)
            if years:
                return years[-1]

            matches = VALIDITY_REGEX.findall(line)
            if matches:
                return matches[-1]

            if idx + 1 < len(lines):
                next_line = lines[idx + 1]
                combined = f"{line} {next_line}"
                combined_years = VALIDITY_YEAR_REGEX.findall(combined)
                if combined_years:
                    return combined_years[-1]

                combined_matches = VALIDITY_REGEX.findall(combined)
                if combined_matches:
                    return combined_matches[-1]
    return None


def _extract_name_tokens(value: str) -> list[str]:
    cleaned = re.sub(r"[^A-Z0-9 ]", " ", value)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return []

    if _keyword_match(cleaned, "DOMICILIO") or ADDRESS_HINT_REGEX.search(cleaned):
        return []

    tokens: list[str] = []
    for raw_token in cleaned.split(" "):
        token = "".join(DIGIT_TO_LETTER.get(char, char) for char in raw_token)
        if not token:
            continue
        if not re.fullmatch(r"[A-Z]+", token):
            continue
        if token.startswith("SEXO"):
            continue
        if token in NAME_BLOCKED_TOKENS:
            return []
        if len(token) > 14:
            continue
        if len(token) <= 2 and token not in NAME_CONNECTOR_TOKENS:
            continue
        tokens.append(token)
    return tokens


def _extract_ine_name_block(lines: list[str], max_lookahead: int = 8) -> str | None:
    name_keywords = ("NOMBRE", "NOMBRES")
    for idx, line in enumerate(lines):
        if not _line_contains_keywords(line, name_keywords):
            continue

        fragments: list[str] = []
        for keyword in name_keywords:
            match = _keyword_match(line, keyword)
            if match:
                fragments.extend(_extract_name_tokens(line[match.end() :]))
                break

        for offset in range(1, max_lookahead + 1):
            next_idx = idx + offset
            if next_idx >= len(lines):
                break
            next_line = lines[next_idx]
            if _line_contains_keywords(next_line, NAME_STOP_KEYWORDS):
                break
            if fragments and ":" in next_line:
                break

            tokens = _extract_name_tokens(next_line)
            if not tokens:
                if fragments and offset > 2:
                    break
                continue
            fragments.extend(tokens)
            if len(fragments) >= 6:
                break

        compact_name = " ".join(fragments).strip()
        if not compact_name:
            continue

        compact_name = re.sub(r"\s+", " ", compact_name).strip()
        if _looks_like_person_name(compact_name):
            return compact_name
    return None


def _mrz_compact(line: str) -> str:
    return re.sub(r"[^A-Z0-9<]", "", line)


def _parse_mrz_date(value: str, is_validity: bool) -> str | None:
    if len(value) != 6 or not value.isdigit():
        return None
    yy = int(value[0:2])
    mm = int(value[2:4])
    dd = int(value[4:6])

    try:
        if is_validity:
            year = 2000 + yy if yy <= 79 else 1900 + yy
        else:
            current_yy = datetime.now().year % 100
            year = 2000 + yy if yy <= current_yy else 1900 + yy
        parsed = datetime(year=year, month=mm, day=dd)
    except ValueError:
        return None

    return parsed.strftime("%d/%m/%Y")


def _extract_from_mrz(lines: list[str]) -> tuple[str | None, str | None, str | None]:
    mrz_name = None
    mrz_birth_date = None
    mrz_validity = None

    for line in lines:
        if "<" not in line:
            continue
        compact = _mrz_compact(line)
        if "<<" not in compact:
            continue

        if not mrz_name:
            name_match = MRZ_NAME_REGEX.search(compact)
            if name_match:
                surnames = name_match.group(1).replace("<", " ").strip()
                names = name_match.group(2).replace("<", " ").strip()
                full_name = " ".join(part for part in (surnames, names) if part).strip()
                if full_name:
                    mrz_name = re.sub(r"\s+", " ", full_name)

        if not mrz_birth_date or not mrz_validity:
            date_match = MRZ_DATES_REGEX.search(compact)
            if date_match:
                if not mrz_birth_date:
                    mrz_birth_date = _parse_mrz_date(date_match.group("birth"), is_validity=False)
                if not mrz_validity:
                    mrz_validity = _parse_mrz_date(date_match.group("valid"), is_validity=True)

    return mrz_name, mrz_birth_date, mrz_validity


def _clean_line_for_address(line: str) -> str:
    cleaned = re.sub(r"[^A-Z0-9,.\- ]", " ", line)
    return re.sub(r"\s+", " ", cleaned).strip(" ,.-")


def _extract_address_fallback(lines: list[str]) -> str | None:
    for idx, line in enumerate(lines):
        if any(block in line for block in ADDRESS_BLOCKLIST):
            continue
        if not ADDRESS_HINT_REGEX.search(line):
            continue

        parts = [_clean_line_for_address(line)]
        for next_idx in range(idx + 1, min(len(lines), idx + 6)):
            next_line = lines[next_idx]
            if any(block in next_line for block in ADDRESS_BLOCKLIST):
                break
            cleaned_next = _clean_line_for_address(next_line)
            if not cleaned_next:
                continue
            if len(cleaned_next) <= 3:
                continue

            looks_like_state = bool(re.search(r"\b[A-Z]{3,},\s*[A-Z]{2,4}\b", cleaned_next))
            looks_like_house_number = bool(re.fullmatch(r"[0-9A-Z\-]{1,8}", cleaned_next))

            if ADDRESS_HINT_REGEX.search(next_line) or "," in next_line or looks_like_state or looks_like_house_number:
                parts.append(cleaned_next)
            else:
                break

        address = ", ".join(part for part in parts if part)
        if len(address) >= 8:
            return address
    return None


def _extract_curp_certification(lines: list[str]) -> tuple[str | None, bool | None]:
    if not lines:
        return None, None

    full_text = " ".join(lines)
    has_certified = _line_contains_keywords(full_text, ("CURP CERTIFICADA", "CERTIFICADA"))
    has_registry = _line_contains_keywords(full_text, ("REGISTRO CIVIL",))
    has_verified = _line_contains_keywords(full_text, ("VERIFICADA", "VERIFICADO"))

    if has_certified and (has_registry or has_verified):
        return "CURP Certificada: verificada con el Registro Civil", True
    if has_certified:
        return "CURP Certificada", True
    return None, False


def extract_fields(text: str, document_type: DocumentType) -> OCRFields:
    normalized_text = _normalize(text)
    lines = _line_iter(normalized_text)

    name = None
    address = None
    clave = None
    certification_status = None
    is_certified = None
    birth_date = _extract_birth_date(lines, normalized_text)
    validity = _extract_validity(lines)
    curp = _extract_curp(normalized_text)

    if document_type == DocumentType.INE:
        name = _value_after_keywords(
            lines,
            ("NOMBRE", "NOMBRES"),
            max_lookahead=8,
            validator=_looks_like_person_name,
            stop_keywords=NAME_STOP_KEYWORDS,
        )
        if not name:
            name = _extract_ine_name_block(lines)
        address = _value_after_keywords(lines, ("DOMICILIO", "DIRECCION"))
    elif document_type == DocumentType.CURP:
        name = _value_after_keywords(
            lines,
            ("NOMBRE", "NOMBRES"),
            max_lookahead=8,
            validator=_looks_like_person_name,
            stop_keywords=NAME_STOP_KEYWORDS,
        )
        address = _value_after_keywords(lines, ("DOMICILIO", "ENTIDAD"))
        if not curp:
            curp = _value_after_keywords(lines, ("CURP", "CLAVE"))
        clave = curp
        certification_status, is_certified = _extract_curp_certification(lines)

    if document_type == DocumentType.INE and (not name or not birth_date or not validity):
        mrz_name, mrz_birth_date, mrz_validity = _extract_from_mrz(lines)
        if not name and mrz_name:
            name = mrz_name
        if not birth_date and mrz_birth_date:
            birth_date = mrz_birth_date
        if not validity and mrz_validity:
            validity = mrz_validity

    if not address:
        address = _extract_address_fallback(lines)

    return OCRFields(
        full_text=text,
        name=name,
        address=address,
        curp=curp,
        clave=clave,
        certification_status=certification_status,
        is_certified=is_certified,
        birth_date=birth_date,
        validity=validity,
    )
