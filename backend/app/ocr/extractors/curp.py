from __future__ import annotations

from app.models import OCRFields
from app.ocr.extractors import common


class CURPExtractor:
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
        address = common.value_after_keywords(lines, ("DOMICILIO", "ENTIDAD"))
        birth_date = common.extract_birth_date(lines, normalized_text)
        validity = common.extract_validity(lines)
        curp = common.extract_curp(normalized_text)
        if not curp:
            curp = common.value_after_keywords(lines, ("CURP", "CLAVE"))

        certification_status, is_certified = common.extract_curp_certification(lines)

        if not address:
            address = common.extract_address_fallback(lines)

        return OCRFields(
            full_text=text,
            name=name,
            address=address,
            curp=curp,
            clave=curp,
            certification_status=certification_status,
            is_certified=is_certified,
            birth_date=birth_date,
            validity=validity,
        )

