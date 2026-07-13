import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import MoviePage from './pages/MoviePage';
import EmotionPage from './pages/EmotionPage';
import EvaluationPage from './pages/EvaluationPage';

function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/movie/:id" element={<MoviePage />} />
        <Route path="/emotion" element={<EmotionPage />} />
        <Route path="/evaluation" element={<EvaluationPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
