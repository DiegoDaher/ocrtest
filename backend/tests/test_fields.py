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
    assert result.clave == "JCHJ850215HDFRRL05"
    assert result.birth_date == "15-02-1985"
    assert result.address == "CIUDAD DE MEXICO"


def test_extract_fields_tolerates_ocr_noise_on_keywords_and_curp() -> None:
    sample_text = """
    N0MBRE: ANA L0PEZ GARCIA
    D0MICILI0: CALLE 1 #25, CENTRO
    C U R P: L0GA900101MDFPRR08
    FECHA DE NAC1MIENTO 01/01/1990
    V1GENCIA 2032
    """

    result = extract_fields(sample_text, DocumentType.INE)

    assert result.name == "ANA L0PEZ GARCIA"
    assert "CALLE 1" in (result.address or "")
    assert result.curp == "LOGA900101MDFPRR08"
    assert result.birth_date == "01/01/1990"
    assert result.validity == "2032"


def test_extract_fields_reads_value_on_next_line_after_keyword() -> None:
    sample_text = """
    NOMBRE
    LUIS RAMIREZ
    DOMICILIO
    AV. INSURGENTES 500
    """

    result = extract_fields(sample_text, DocumentType.INE)

    assert result.name == "LUIS RAMIREZ"
    assert result.address == "AV. INSURGENTES 500"


def test_extract_fields_reads_validity_and_birth_date_on_next_line() -> None:
    sample_text = """
    FECHA DE NACIMIENTO
    07/11/1992
    V1GENCIA
    2034
    """

    result = extract_fields(sample_text, DocumentType.INE)

    assert result.birth_date == "07/11/1992"
    assert result.validity == "2034"


def test_extract_fields_ine_fallback_to_mrz_when_keywords_missing() -> None:
    sample_text = """
    IDMEX2519056837<<0340135625529
    0507303H3312315MEX<00<<26178<1
    DIAZ<CONTRERAS<<DIEGO<DAHER<<<
    """

    result = extract_fields(sample_text, DocumentType.INE)

    assert result.name == "DIAZ CONTRERAS DIEGO DAHER"
    assert result.birth_date == "30/07/2005"
    assert result.validity == "31/12/2033"


def test_extract_fields_address_fallback_when_no_domicilio_keyword() -> None:
    sample_text = """
    PRIV BALCON A
    FRACC BALCON D
    DURANGO, DGO
    CLAVE DE ELECTOR DZCD...
    """

    result = extract_fields(sample_text, DocumentType.INE)

    assert result.address == "PRIV BALCON A, FRACC BALCON D, DURANGO, DGO"


def test_extract_fields_curp_certification_status() -> None:
    sample_text = """
    NOMBRE: DIEGO DAHER DIAZ CONTRERAS
    CURP: DICD050730HDGZNGA8
    CURP CERTIFICADA: VERIFICADA CON EL REGISTRO CIVIL
    """

    result = extract_fields(sample_text, DocumentType.CURP)

    assert result.name == "DIEGO DAHER DIAZ CONTRERAS"
    assert result.curp == "DICD050730HDGZNGA8"
    assert result.clave == "DICD050730HDGZNGA8"
    assert result.certification_status == "CURP Certificada: verificada con el Registro Civil"
    assert result.is_certified is True


def test_extract_fields_curp_name_skips_noise_lines_after_nombre() -> None:
    sample_text = """
    CONSTANCIA DE LA CLAVE UNICA
    Clave:
    DICE141017HDGZNLA9
    Nombre
    Ea
    lk:
    es eo |
    ELIAN YOEL DIAZ CONTRERAS
    CURP Certificada: verificada con el Registro Civil
    """

    result = extract_fields(sample_text, DocumentType.CURP)

    assert result.name == "ELIAN YOEL DIAZ CONTRERAS"
    assert result.clave == "DICE141017HDGZNLA9"
    assert result.certification_status == "CURP Certificada: verificada con el Registro Civil"
    assert result.is_certified is True


def test_extract_fields_ine_handles_multiline_name_and_compact_birth_date_noise() -> None:
    sample_text = """
    . stg, eee
    ... oy XS, MEXICO INSTITUTO NACIONAL ELECTORAL .
    ! ee ES CREDENCIAL PARA VOTAR —
    N
    ic NOMBRE — SEXOH
    I MARTINEZ \\ —
    — E MILLAN - ,
    1E MANUEL \\ y
    J ; Don:CLIO — - —
    = CPRINERADEENEROS —. —| —
    : COL ADOLFO LOPEZ MATEOS 62828 i
    {et YECAPIXTLA, MOR.
    ; - CLAVEDEELECTOR ORMJRB80062501H500 , 1
    5 CURP ~ ANODE REGISTRO —
    qc OIMR800625HDFRJB03 2005 02 — '
    1E <b. FECHADENACIMENTO — SECCIÓN — VIGENCIA | ING - |
    (Oe 251061980 7 0859 2022 - 2032 s |
    . ' U —
    """

    result = extract_fields(sample_text, DocumentType.INE)

    assert result.name == "MARTINEZ MILLAN MANUEL"
    assert result.address == "COL ADOLFO LOPEZ MATEOS 62828 I, ET YECAPIXTLA, MOR"
    assert result.curp == "OIMR800625HDFRJB03"
    assert result.birth_date == "25/06/1980"
    assert result.validity == "2032"
