import { Link, useLocation } from 'react-router-dom';

const navLinks = [
  { to: '/', label: 'Home', icon: '🏠' },
  { to: '/emotion', label: 'Emotion Search', icon: '💭' },
  { to: '/evaluation', label: 'Evaluation', icon: '📊' },
];

export default function Navbar() {
  const location = useLocation();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass-card border-t-0 border-x-0 rounded-none">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 group">
          <span className="text-2xl">🎬</span>
          <span className="text-xl font-bold bg-gradient-to-r from-primary-400 to-accent bg-clip-text text-transparent
                           group-hover:from-primary-300 group-hover:to-yellow-400 transition-all duration-300">
            MovieRecSys
          </span>
        </Link>

        <div className="flex items-center gap-1">
          {navLinks.map((link) => {
            const isActive = location.pathname === link.to;
            return (
              <Link
                key={link.to}
                to={link.to}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 flex items-center gap-2
                  ${isActive
                    ? 'bg-primary-600/20 text-primary-300 border border-primary-500/30'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
                  }`}
              >
                <span>{link.icon}</span>
                {link.label}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
