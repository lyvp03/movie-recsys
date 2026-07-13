import type { AlgorithmType } from '../types/movie';

const ALGORITHMS: { value: AlgorithmType; label: string; description: string; needsUser: boolean }[] = [
  { value: 'content-tfidf', label: 'TF-IDF', description: 'Keyword matching', needsUser: false },
  { value: 'content-embedding', label: 'Embedding', description: 'Semantic similarity', needsUser: false },
  { value: 'collab', label: 'Collaborative', description: 'User behavior', needsUser: true },
  { value: 'hybrid-tfidf', label: 'Hybrid (TF-IDF)', description: 'CB + CF combined', needsUser: true },
  { value: 'hybrid-embedding', label: 'Hybrid (Embed)', description: 'CB + CF combined', needsUser: true },
];

interface AlgorithmSelectorProps {
  selected: AlgorithmType;
  onSelect: (algo: AlgorithmType) => void;
}

export default function AlgorithmSelector({ selected, onSelect }: AlgorithmSelectorProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {ALGORITHMS.map((algo) => (
        <button
          key={algo.value}
          onClick={() => onSelect(algo.value)}
          className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300
            ${selected === algo.value
              ? 'bg-primary-600 text-white shadow-lg shadow-primary-600/30'
              : 'glass-card text-gray-400 hover:text-gray-200 hover:bg-white/10'
            }`}
        >
          <span className="block">{algo.label}</span>
          <span className="block text-[10px] opacity-70">{algo.description}</span>
        </button>
      ))}
    </div>
  );
}
