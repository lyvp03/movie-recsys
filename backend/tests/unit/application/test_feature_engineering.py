def test_build_feature_text_all_fields():
    from application.feature_engineering import build_feature_text
    
    class DummyMovie:
        genres = "Action,Adventure"
        overview = "A great movie."
        cast = "Actor A,Actor B"
        keywords = "alien,space"
        
    movie = DummyMovie()
    text = build_feature_text(movie)
    assert text == "Action Adventure A great movie. Actor A Actor B alien space"

def test_build_feature_text_missing_fields():
    from application.feature_engineering import build_feature_text
    
    class DummyMovie:
        genres = None
        overview = "A great movie."
        cast = ""
        keywords = None
        
    movie = DummyMovie()
    text = build_feature_text(movie)
    assert text == "A great movie."
