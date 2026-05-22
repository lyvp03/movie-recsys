import pytest
from domain.entities.emotion import EmotionVector
from domain.exceptions import ValidationError

def test_emotion_vector_defaults():
    ev = EmotionVector()
    assert ev.joy == 0.0
    assert ev.to_list() == [0.0] * 8

def test_emotion_vector_validation():
    with pytest.raises(ValidationError):
        EmotionVector(joy=-0.1)

def test_emotion_vector_to_from_dict():
    data = {"joy": 0.8, "fear": 0.2}
    ev = EmotionVector.from_dict(data)
    assert ev.joy == 0.8
    assert ev.fear == 0.2
    assert ev.trust == 0.0
    
    out_dict = ev.to_dict()
    assert out_dict["joy"] == 0.8
    assert out_dict["fear"] == 0.2
    assert out_dict["trust"] == 0.0

def test_cosine_similarity():
    ev1 = EmotionVector(joy=1.0)
    ev2 = EmotionVector(joy=1.0)
    assert pytest.approx(ev1.cosine_similarity(ev2)) == 1.0
    
    ev3 = EmotionVector(fear=1.0)
    assert ev1.cosine_similarity(ev3) == 0.0
    
    ev4 = EmotionVector(joy=0.5, fear=0.5)
    # Cosine sim between [1,0] and [0.5, 0.5] should be 1 * 0.5 / sqrt(0.5) = 1/sqrt(2) = 0.707
    assert pytest.approx(ev1.cosine_similarity(ev4), 0.01) == 0.707

def test_cosine_similarity_zero_vector():
    ev1 = EmotionVector(joy=1.0)
    ev_zero = EmotionVector()
    assert ev1.cosine_similarity(ev_zero) == 0.0
