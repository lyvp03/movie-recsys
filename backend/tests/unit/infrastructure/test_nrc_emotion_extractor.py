import pytest

from infrastructure.ml.nrc_emotion_extractor import NRCEmotionExtractor


@pytest.fixture
def extractor():
    """Create a real NRCEmotionExtractor using the bundled NRCLex lexicon."""
    return NRCEmotionExtractor()


def test_extract_emotion_empty_text(extractor):
    vector = extractor.extract("")
    assert vector.joy == 0.0
    assert vector.fear == 0.0


def test_extract_emotion_no_hits(extractor):
    # Words unlikely to be in the NRC lexicon
    vector = extractor.extract("xyzzy qwrtyuiop asdfghjkl")
    assert sum(vector.to_list()) == 0.0


def test_extract_emotion_happy_text(extractor):
    vector = extractor.extract("happy")
    # "happy" should have joy and trust in NRC lexicon
    assert vector.joy > 0.0
    assert sum(vector.to_list()) == pytest.approx(1.0)


def test_extract_case_insensitive(extractor):
    vector_upper = extractor.extract("HAPPY")
    vector_lower = extractor.extract("happy")
    assert vector_upper == vector_lower


def test_extract_normalizes_to_one(extractor):
    text = "This terrifying movie left me feeling abandoned and hopeless"
    vector = extractor.extract(text)
    total = sum(vector.to_list())
    # Should normalize to ~1.0 if any hits found
    if total > 0:
        assert total == pytest.approx(1.0)


def test_extract_fear_from_scary_words(extractor):
    vector = extractor.extract("fear terror horror scary")
    # At least some fear should be detected
    assert vector.fear > 0.0
