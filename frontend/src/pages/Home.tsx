import { Link } from 'react-router-dom';
import { Upload, FileCheck, BarChart3, Zap } from 'lucide-react';

const features = [
  {
    icon: Upload,
    title: 'Upload Assessment',
    description: 'Upload your marking guide and assessment criteria in PDF format',
    to: '/upload-assessment',
    color: 'text-blue-500',
  },
  {
    icon: FileCheck,
    title: 'Mark Answers',
    description: 'Upload student answer sheets and get AI-powered grading',
    to: '/mark-answers',
    color: 'text-green-500',
  },
  {
    icon: BarChart3,
    title: 'View Reports',
    description: 'Access detailed marking reports and analytics',
    to: '/reports',
    color: 'text-purple-500',
  },
];

export default function Home() {
  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <div className="text-center space-y-4 py-12">
        <h1 className="text-5xl font-bold text-foreground">
          AI-Powered Answer Sheet Marking
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Automate your grading process with Claude Sonnet 4.5. Fast, accurate, and consistent
          assessment marking for educators.
        </p>
        <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground mt-6">
          <Zap className="h-4 w-4 text-yellow-500" />
          <span>Powered by Anthropic's Claude Sonnet 4.5</span>
        </div>
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {features.map((feature) => {
          const Icon = feature.icon;
          return (
            <Link
              key={feature.to}
              to={feature.to}
              className="block p-6 rounded-lg border border-border bg-card hover:border-primary transition-all hover:shadow-lg"
            >
              <Icon className={`h-12 w-12 ${feature.color} mb-4`} />
              <h3 className="text-xl font-semibold text-foreground mb-2">
                {feature.title}
              </h3>
              <p className="text-muted-foreground">{feature.description}</p>
            </Link>
          );
        })}
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-8">
        <div className="text-center p-6 rounded-lg bg-card border border-border">
          <div className="text-3xl font-bold text-primary">~5 min</div>
          <div className="text-sm text-muted-foreground mt-2">Average marking time per student</div>
        </div>
        <div className="text-center p-6 rounded-lg bg-card border border-border">
          <div className="text-3xl font-bold text-primary">100%</div>
          <div className="text-sm text-muted-foreground mt-2">Consistent grading criteria</div>
        </div>
        <div className="text-center p-6 rounded-lg bg-card border border-border">
          <div className="text-3xl font-bold text-primary">PDF</div>
          <div className="text-sm text-muted-foreground mt-2">Support for standard formats</div>
        </div>
      </div>
    </div>
  );
}
