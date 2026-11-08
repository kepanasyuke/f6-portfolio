from app import scoring, service, variants


def test_distance_basics():
    assert scoring.distance("f6security.example", "f6security.example") == 0
    assert scoring.distance("f6security.example", "f6securit.example") == 1
    assert scoring.distance("abc", "") == 3


def test_omissions_drop_characters():
    assert "f6ecurity.example" in variants.omissions("f6security.example")


def test_transpositions_swap_neighbours():
    assert "fs6ecurity.example" in variants.transpositions("f6security.example")


def test_homoglyphs_use_cyrillic():
    produced = variants.homoglyphs("analyst.example")
    assert produced
    assert any(any(ord(letter) > 127 for letter in variant) for variant in produced)


def test_confusables_replace_characters():
    assert "f6s3curity.example" in variants.confusables("f6security.example")


def test_tld_swaps_change_suffix():
    assert "f6security.co" in variants.tld_swaps("f6security.example")


def test_subdomains_prefix_brand():
    assert "login.f6security.example" in variants.subdomains("f6security.example")


def test_generate_returns_unique_variants_without_brand():
    produced = service.generate("f6security.example")
    assert len(produced) == len(set(produced))
    assert "f6security.example" not in produced


def test_assess_rewards_close_variants():
    close = service.assess("f6security.example", "f6security.exampl")
    far = service.assess("f6security.example", "totally-different-domain.example")
    assert close["risk"] > far["risk"]
    assert close["distance"] < far["distance"]


def test_verdict_thresholds():
    assert scoring.verdict(80) == "critical"
    assert scoring.verdict(60) == "high"
    assert scoring.verdict(40) == "medium"
    assert scoring.verdict(10) == "low"


def test_signals_are_deterministic():
    assert scoring.signals("f6security.co") == scoring.signals("f6security.co")
