import pytest
import os
from tempfile import NamedTemporaryFile

from infrastructure.ml.nrc_emotion_extractor import NRCEmotionExtractor

@pytest.fixture
def mock_lexicon():
    content = """abandoned\tanger\t1
abandoned\tfear\t1
abandoned\tjoy\t0
happy\tjoy\t1
happy\ttrust\t1
terrifying\tfear\t1
terrifying\tsurprise\t1
hopeless\tsadness\t1
hopeless\tfear\t1"""
    
    with NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_name = f.name
        
    yield temp_name
    os.unlink(temp_name)

def test_extract_emotion_empty_text(mock_lexicon):
    extractor = NRCEmotionExtractor(lexicon_path=mock_lexicon)
    vector = extractor.extract("")
    assert vector.joy == 0.0
    assert vector.fear == 0.0

def test_extract_emotion_no_hits(mock_lexicon):
    extractor = NRCEmotionExtractor(lexicon_path=mock_lexicon)
    vector = extractor.extract("a normal boring text with no emotions")
    assert vector.joy == 0.0
    assert sum(vector.to_list()) == 0.0

def test_extract_emotion_hits(mock_lexicon):
    extractor = NRCEmotionExtractor(lexicon_path=mock_lexicon)
    # text with "terrifying", "abandoned", "hopeless"
    # terrifying: fear(1), surprise(1)
    # abandoned: anger(1), fear(1)
    # hopeless: sadness(1), fear(1)
    # total hits = 6
    # fear = 3, surprise = 1, anger = 1, sadness = 1
    # normalized: fear=3/6=0.5, surprise=1/6=0.1666, anger=1/6=0.1666, sadness=1/6=0.1666
    
    text = "This terrifying movie left me feeling abandoned and hopeless"
    vector = extractor.extract(text)
    
    assert pytest.approx(vector.fear) == 0.5
    assert pytest.approx(vector.surprise) == 1/6
    assert pytest.approx(vector.anger) == 1/6
    assert pytest.approx(vector.sadness) == 1/6
    
    assert vector.joy == 0.0
    assert pytest.approx(sum(vector.to_list())) == 1.0

def test_extract_case_insensitive(mock_lexicon):
    extractor = NRCEmotionExtractor(lexicon_path=mock_lexicon)
    vector1 = extractor.extract("HAPPY")
    vector2 = extractor.extract("happy")
    
    assert vector1.joy == 0.5  # happy has joy=1, trust=1
    assert vector1.trust == 0.5
    assert vector1 == vector2
