from unittest.mock import MagicMock, patch

from infrastructure.ml.surprise_svd_model import SurpriseSVDModel


def test_predict_without_model():
    model = SurpriseSVDModel(model_path="non_existent_file.pkl")
    score = model.predict(user_id=1, movie_id=10)
    assert score == 0.0


@patch("infrastructure.ml.surprise_svd_model.Path.exists")
@patch("builtins.open")
@patch("pickle.load")
def test_predict_with_model(mock_pickle_load, mock_open, mock_exists):
    mock_exists.return_value = True
    
    mock_svd = MagicMock()
    # Surprise prediction object has 'est' attribute
    mock_prediction = MagicMock()
    mock_prediction.est = 4.2
    mock_svd.predict.return_value = mock_prediction
    
    mock_pickle_load.return_value = mock_svd
    
    model = SurpriseSVDModel(model_path="fake_path.pkl")
    
    score = model.predict(user_id=1, movie_id=10)
    
    assert score == 4.2
    mock_svd.predict.assert_called_once_with(uid=1, iid=10)


@patch("infrastructure.ml.surprise_svd_model.Path.exists")
@patch("builtins.open")
@patch("pickle.load")
def test_get_top_n(mock_pickle_load, mock_open, mock_exists):
    mock_exists.return_value = True
    
    mock_svd = MagicMock()
    
    # Return different scores for different movie ids
    def side_effect(uid, iid):
        pred = MagicMock()
        scores = {10: 3.5, 20: 4.8, 30: 2.1, 40: 4.5}
        pred.est = scores.get(iid, 0.0)
        return pred
        
    mock_svd.predict.side_effect = side_effect
    mock_pickle_load.return_value = mock_svd
    
    model = SurpriseSVDModel(model_path="fake_path.pkl")
    
    candidates = [10, 20, 30, 40]
    top_n = model.get_top_n(user_id=1, movie_ids=candidates, n=2)
    
    assert len(top_n) == 2
    # Should be sorted descending by score: 20 (4.8), 40 (4.5)
    assert top_n[0] == (20, 4.8)
    assert top_n[1] == (40, 4.5)
