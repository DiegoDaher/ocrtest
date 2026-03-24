from __future__ import annotations

from app.models import OCRFields
from app.ocr.extractors import common


class INEExtractor:
    def extract(self, text: str) -> OCRFields:
        normalized_text = common.normalize(text)
        lines = common.line_iter(normalized_text)

        name = common.value_after_keywords(
            lines,
            ("NOMBRE", "NOMBRES"),
            max_lookahead=8,
            validator=common.looks_like_person_name,
            stop_keywords=common.NAME_STOP_KEYWORDS,
        )
        if not name:
            name = common.extract_ine_name_block(lines)

        address = common.value_after_keywords(lines, ("DOMICILIO", "DIRECCION"))
        birth_date = common.extract_birth_date(lines, normalized_text)
        validity = common.extract_validity(lines)
        curp = common.extract_curp(normalized_text)

        if not name or not birth_date or not validity:
            mrz_name, mrz_birth_date, mrz_validity = common.extract_from_mrz(lines)
            if not name and mrz_name:
                name = mrz_name
            if not birth_date and mrz_birth_date:
                birth_date = mrz_birth_date
            if not validity and mrz_validity:
                validity = mrz_validity

        if not address:
            address = common.extract_address_fallback(lines)

        return OCRFields(
            full_text=text,
            name=name,
            address=address,
            curp=curp,
            clave=None,
            certification_status=None,
            is_certified=None,
            birth_date=birth_date,
            validity=validity,
        )

