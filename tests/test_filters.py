from keko_licitacoes.filters import any_keyword_matches, normalize_text, split_terms


def test_normalize_text_removes_accents_and_case() -> None:
    assert normalize_text("Pregao Eletronico") == "pregao eletronico"
    assert normalize_text("Aquisição de CALHAS") == "aquisicao de calhas"


def test_split_terms_supports_repeated_and_comma_values() -> None:
    assert split_terms(["calha, rufo", "telhado"]) == ["calha", "rufo", "telhado"]


def test_any_keyword_matches_across_fields() -> None:
    assert any_keyword_matches(["Compra de calhas", "Prefeitura"], ["calha"])
    assert not any_keyword_matches(["Compra de lampadas"], ["calha"])
