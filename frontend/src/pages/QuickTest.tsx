import { useState, useEffect } from 'react';
import { Zap, BookOpen, Calculator, History, Send, Lightbulb } from 'lucide-react';

interface QuickTestRequest {
  question: string;
  student_answer: string;
  question_type: string;
  max_marks: number;
  marking_guide?: string;
  model_answer?: string;
}

interface QuickTestResponse {
  marks_obtained: number;
  max_marks: number;
  percentage: number;
  feedback: string;
  marking_breakdown: Record<string, number>;
  question_analysis?: {
    question_type: string;
    difficulty: string;
    key_concepts: string[];
  };
}

interface Example {
  name: string;
  question: string;
  question_type: string;
  max_marks: number;
  model_answer: string;
  sample_student_answer: string;
}

const questionTypes = [
  { value: 'short_answer', label: 'Short Answer' },
  { value: 'long_answer', label: 'Long Answer' },
  { value: 'mcq', label: 'Multiple Choice' },
  { value: 'numerical', label: 'Numerical' },
  { value: 'true_false', label: 'True/False' },
];

export default function QuickTest() {
  const [formData, setFormData] = useState<QuickTestRequest>({
    question: '',
    student_answer: '',
    question_type: 'short_answer',
    max_marks: 5,
    marking_guide: '',
    model_answer: '',
  });

  const [result, setResult] = useState<QuickTestResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [examples, setExamples] = useState<Example[]>([]);
  const [showExamples, setShowExamples] = useState(false);

  // Fetch examples on mount
  useEffect(() => {
    fetch('http://localhost:8001/quick-test/examples')
      .then((res) => res.json())
      .then((data) => setExamples(data.examples || []))
      .catch((err) => console.error('Failed to load examples:', err));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch('http://localhost:8001/quick-test/mark', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: QuickTestResponse = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to mark answer');
    } finally {
      setIsLoading(false);
    }
  };

  const loadExample = (example: Example) => {
    setFormData({
      question: example.question,
      student_answer: example.sample_student_answer,
      question_type: example.question_type,
      max_marks: example.max_marks,
      model_answer: example.model_answer,
      marking_guide: '',
    });
    setResult(null);
    setShowExamples(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="flex items-center justify-center gap-2">
          <Zap className="h-8 w-8 text-yellow-500" />
          <h1 className="text-4xl font-bold text-foreground">Quick Test</h1>
        </div>
        <p className="text-muted-foreground max-w-2xl mx-auto">
          Test the AI marking system with a single question and answer. Perfect for exploring how
          the system works without uploading files.
        </p>
      </div>

      {/* Example Templates */}
      <div className="bg-card border border-border rounded-lg p-4">
        <button
          onClick={() => setShowExamples(!showExamples)}
          className="flex items-center gap-2 text-primary font-semibold hover:text-primary/80 transition-colors"
        >
          <Lightbulb className="h-5 w-5" />
          {showExamples ? 'Hide' : 'Show'} Example Templates
        </button>

        {showExamples && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
            {examples.map((example, idx) => {
              const icons = [BookOpen, Calculator, History];
              const Icon = icons[idx] || BookOpen;
              return (
                <button
                  key={idx}
                  onClick={() => loadExample(example)}
                  className="text-left p-4 rounded-lg border border-border bg-background hover:border-primary transition-all"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <Icon className="h-5 w-5 text-primary" />
                    <h3 className="font-semibold text-foreground">{example.name}</h3>
                  </div>
                  <p className="text-sm text-muted-foreground line-clamp-2">{example.question}</p>
                  <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                    <span className="px-2 py-1 bg-primary/10 rounded">
                      {example.max_marks} marks
                    </span>
                    <span className="px-2 py-1 bg-primary/10 rounded capitalize">
                      {example.question_type.replace('_', ' ')}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Split Screen Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Input Form */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h2 className="text-2xl font-bold text-foreground mb-4">Question & Answer</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Question */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Question <span className="text-red-500">*</span>
              </label>
              <textarea
                value={formData.question}
                onChange={(e) => setFormData({ ...formData, question: e.target.value })}
                placeholder="Enter the question here..."
                className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary min-h-[100px]"
                required
              />
            </div>

            {/* Student Answer */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Student Answer <span className="text-red-500">*</span>
              </label>
              <textarea
                value={formData.student_answer}
                onChange={(e) => setFormData({ ...formData, student_answer: e.target.value })}
                placeholder="Enter the student's answer here..."
                className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary min-h-[120px]"
                required
              />
            </div>

            {/* Question Type & Max Marks */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Question Type
                </label>
                <select
                  value={formData.question_type}
                  onChange={(e) => setFormData({ ...formData, question_type: e.target.value })}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  {questionTypes.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Maximum Marks
                </label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={formData.max_marks}
                  onChange={(e) =>
                    setFormData({ ...formData, max_marks: parseFloat(e.target.value) })
                  }
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                />
              </div>
            </div>

            {/* Optional: Model Answer */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Model Answer <span className="text-muted-foreground text-xs">(Optional)</span>
              </label>
              <textarea
                value={formData.model_answer}
                onChange={(e) => setFormData({ ...formData, model_answer: e.target.value })}
                placeholder="Provide an ideal answer for reference..."
                className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary min-h-[80px]"
              />
            </div>

            {/* Optional: Marking Guide */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Marking Guide <span className="text-muted-foreground text-xs">(Optional)</span>
              </label>
              <textarea
                value={formData.marking_guide}
                onChange={(e) => setFormData({ ...formData, marking_guide: e.target.value })}
                placeholder="Provide specific marking criteria (will be auto-generated if not provided)..."
                className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary min-h-[80px]"
              />
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading || !formData.question || !formData.student_answer}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary text-primary-foreground rounded-lg font-semibold hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              <Send className="h-5 w-5" />
              {isLoading ? 'Marking...' : 'Mark Answer'}
            </button>
          </form>
        </div>

        {/* Right: Results Display */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h2 className="text-2xl font-bold text-foreground mb-4">Marking Results</h2>

          {!result && !error && !isLoading && (
            <div className="flex items-center justify-center h-64 text-center text-muted-foreground">
              <div>
                <Zap className="h-12 w-12 mx-auto mb-3 text-muted-foreground/50" />
                <p>Results will appear here after marking</p>
              </div>
            </div>
          )}

          {isLoading && (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="animate-spin h-12 w-12 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4"></div>
                <p className="text-muted-foreground">Analyzing answer...</p>
              </div>
            </div>
          )}

          {error && (
            <div className="p-4 bg-red-500/10 border border-red-500 rounded-lg">
              <p className="text-red-500 font-semibold">Error</p>
              <p className="text-sm text-muted-foreground mt-1">{error}</p>
            </div>
          )}

          {result && (
            <div className="space-y-6">
              {/* Score Display */}
              <div className="text-center p-6 bg-primary/5 border border-primary/20 rounded-lg">
                <div className="text-5xl font-bold text-primary mb-2">
                  {result.marks_obtained} / {result.max_marks}
                </div>
                <div className="text-xl text-muted-foreground">
                  {result.percentage.toFixed(1)}%
                </div>
              </div>

              {/* Feedback */}
              <div>
                <h3 className="font-semibold text-foreground mb-2">Feedback</h3>
                <div className="p-4 bg-background border border-border rounded-lg">
                  <p className="text-muted-foreground whitespace-pre-wrap">{result.feedback}</p>
                </div>
              </div>

              {/* Marking Breakdown */}
              {result.marking_breakdown && Object.keys(result.marking_breakdown).length > 0 && (
                <div>
                  <h3 className="font-semibold text-foreground mb-2">Marking Breakdown</h3>
                  <div className="space-y-2">
                    {Object.entries(result.marking_breakdown).map(([key, value]) => (
                      <div
                        key={key}
                        className="flex justify-between items-center p-3 bg-background border border-border rounded-lg"
                      >
                        <span className="text-foreground capitalize">
                          {key.replace(/_/g, ' ')}
                        </span>
                        <span className="font-semibold text-primary">{value.toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Question Analysis */}
              {result.question_analysis && (
                <div>
                  <h3 className="font-semibold text-foreground mb-2">Question Analysis</h3>
                  <div className="p-4 bg-background border border-border rounded-lg space-y-2">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Type:</span>
                      <span className="text-foreground capitalize">
                        {result.question_analysis.question_type.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Difficulty:</span>
                      <span className="text-foreground capitalize">
                        {result.question_analysis.difficulty}
                      </span>
                    </div>
                    {result.question_analysis.key_concepts &&
                      result.question_analysis.key_concepts.length > 0 && (
                        <div>
                          <span className="text-muted-foreground block mb-1">Key Concepts:</span>
                          <div className="flex flex-wrap gap-2">
                            {result.question_analysis.key_concepts.map((concept, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-1 bg-primary/10 text-primary text-sm rounded"
                              >
                                {concept}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
