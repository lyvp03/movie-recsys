interface StarRatingProps {
  rating: number;
  maxRating?: number;
  size?: 'sm' | 'md';
}

export default function StarRating({ rating, maxRating = 5, size = 'sm' }: StarRatingProps) {
  const percentage = (rating / maxRating) * 100;
  const sizeClass = size === 'sm' ? 'text-sm' : 'text-lg';

  return (
    <div className="flex items-center gap-1.5">
      <div className={`relative ${sizeClass}`}>
        <div className="text-gray-600">★★★★★</div>
        <div
          className="absolute inset-0 overflow-hidden text-accent"
          style={{ width: `${percentage}%` }}
        >
          ★★★★★
        </div>
      </div>
      <span className="text-xs text-gray-400 font-medium">{rating.toFixed(1)}</span>
    </div>
  );
}
