from app.models import DocumentType
from app.ocr.fields import extract_fields


def test_extract_fields_from_ine_sample() -> None:
    sample_text = """
    NOMBRE: MARIA PEREZ LOPEZ
    DOMICILIO: AV. REVOLUCION 123, COL. CENTRO, CDMX
    CURP: PERM900101MDFLRS09
    FECHA DE NACIMIENTO 01/01/1990
    VIGENCIA 2030
    """

    result = extract_fields(sample_text, DocumentType.INE)

    assert result.name == "MARIA PEREZ LOPEZ"
    assert "AV. REVOLUCION" in (result.address or "")
    assert result.curp == "PERM900101MDFLRS09"
    assert result.birth_date == "01/01/1990"
    assert result.validity == "2030"


def test_extract_fields_from_curp_sample_when_curp_inline() -> None:
    sample_text = """
    NOMBRE JUAN CARLOS HERNANDEZ
    CURP JCHJ850215HDFRRL05
    ENTIDAD: CIUDAD DE MEXICO
    FECHA-DE-NACIMIENTO 15-02-1985
    """

    result = extract_fields(sample_text, DocumentType.CURP)

    assert result.name == "JUAN CARLOS HERNANDEZ"
    assert result.curp == "JCHJ850215HDFRRL05"
    assert result.birth_date == "15-02-1985"
    assert result.address == "CIUDAD DE MEXICO"
