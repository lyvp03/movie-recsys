const EMOTION_COLORS: Record<string, string> = {
  joy: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  trust: 'bg-green-500/20 text-green-300 border-green-500/30',
  fear: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
  surprise: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
  sadness: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  disgust: 'bg-lime-500/20 text-lime-300 border-lime-500/30',
  anger: 'bg-red-500/20 text-red-300 border-red-500/30',
  anticipation: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
};

const EMOTION_ICONS: Record<string, string> = {
  joy: '😊',
  trust: '🤝',
  fear: '😨',
  surprise: '😲',
  sadness: '😢',
  disgust: '🤢',
  anger: '😠',
  anticipation: '🤔',
};

interface EmotionTagProps {
  emotion: string;
  score: number;
}

export default function EmotionTag({ emotion, score }: EmotionTagProps) {
  if (score < 0.05) return null;

  const colorClass = EMOTION_COLORS[emotion] || 'bg-gray-500/20 text-gray-300 border-gray-500/30';
  const icon = EMOTION_ICONS[emotion] || '•';

  return (
    <span className={`emotion-badge border ${colorClass} flex items-center gap-1`}>
      <span>{icon}</span>
      <span className="capitalize">{emotion}</span>
      <span className="opacity-70">{(score * 100).toFixed(0)}%</span>
    </span>
  );
}
