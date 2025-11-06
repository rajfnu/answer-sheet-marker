import { Link } from 'react-router-dom';
import { GraduationCap } from 'lucide-react';

export default function Header() {
  return (
    <header className="border-b border-border bg-card">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity cursor-pointer">
            <GraduationCap className="h-8 w-8 text-primary" />
            <div>
              <h1 className="text-2xl font-bold text-foreground">Answer Sheet Marker</h1>
              <p className="text-sm text-muted-foreground">AI-Powered Assessment Grading</p>
            </div>
          </Link>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">
              Powered by Claude Sonnet 4.5
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
