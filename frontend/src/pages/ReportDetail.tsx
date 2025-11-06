import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import Button from '../components/ui/Button';
import { getReport, type MarkingReportResponse, type QuestionEvaluation } from '../lib/api/reports';
import {
  User,
  Calendar,
  Award,
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Clock,
  FileText,
  Hash
} from 'lucide-react';

type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export default function ReportDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [report, setReport] = useState<MarkingReportResponse | null>(null);
  const [loadingState, setLoadingState] = useState<LoadingState>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    if (id) {
      loadReport(id);
    }
  }, [id]);

  const loadReport = async (reportId: string) => {
    setLoadingState('loading');
    setErrorMessage('');

    try {
      const data = await getReport(reportId);
      setReport(data);
      setLoadingState('success');
    } catch (error: any) {
      setLoadingState('error');
      setErrorMessage(
        error.response?.data?.detail ||
        'Failed to load report. Please try again.'
      );
    }
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  const getGradeColor = (grade: string) => {
    const gradeColors: Record<string, string> = {
      'A+': 'text-green-600 bg-green-50 border-green-200',
      'A': 'text-green-600 bg-green-50 border-green-200',
      'B': 'text-blue-600 bg-blue-50 border-blue-200',
      'C': 'text-yellow-600 bg-yellow-50 border-yellow-200',
      'D': 'text-orange-600 bg-orange-50 border-orange-200',
      'F': 'text-red-600 bg-red-50 border-red-200',
    };
    return gradeColors[grade] || 'text-gray-600 bg-gray-50 border-gray-200';
  };

  const getQualityColor = (quality: string) => {
    const qualityColors: Record<string, string> = {
      'excellent': 'text-green-700 bg-green-100 border-green-300',
      'good': 'text-blue-700 bg-blue-100 border-blue-300',
      'satisfactory': 'text-yellow-700 bg-yellow-100 border-yellow-300',
      'poor': 'text-orange-700 bg-orange-100 border-orange-300',
      'inadequate': 'text-red-700 bg-red-100 border-red-300',
    };
    return qualityColors[quality] || 'text-gray-700 bg-gray-100 border-gray-300';
  };

  if (loadingState === 'loading') {
    return (
      <div className="max-w-7xl mx-auto">
        <Card>
          <CardContent className="py-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="text-muted-foreground mt-4">Loading report...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (loadingState === 'error') {
    return (
      <div className="max-w-7xl mx-auto">
        <Card className="border-red-200 bg-red-50">
          <CardContent className="py-6">
            <div className="flex items-center gap-3">
              <AlertCircle className="h-6 w-6 text-red-600" />
              <div>
                <p className="font-medium text-red-900">Error Loading Report</p>
                <p className="text-sm text-red-700 mt-1">{errorMessage}</p>
              </div>
            </div>
            <div className="flex gap-3 mt-4">
              <Button onClick={() => navigate('/reports')} variant="outline">
                Back to Reports
              </Button>
              <Button onClick={() => id && loadReport(id)}>
                Try Again
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!report) {
    return null;
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="outline"
            onClick={() => navigate('/reports')}
            className="flex items-center gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back
          </Button>
          <div>
            <h2 className="text-3xl font-bold text-foreground">
              Report for Student {report.student_id}
            </h2>
            <p className="text-sm text-muted-foreground mt-1 flex items-center gap-2">
              <FileText className="h-3 w-3" />
              {report.assessment_title}
            </p>
          </div>
        </div>
      </div>

      {/* Score Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Award className="h-8 w-8 text-primary" />
              <div>
                <p className="text-3xl font-bold text-foreground">
                  {report.score.total_marks.toFixed(1)}
                </p>
                <p className="text-sm text-muted-foreground">Total Score</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Hash className="h-8 w-8 text-primary" />
              <div>
                <p className="text-3xl font-bold text-foreground">
                  {report.score.max_marks.toFixed(1)}
                </p>
                <p className="text-sm text-muted-foreground">Max Marks</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className={`px-4 py-2 rounded border font-bold text-2xl ${getGradeColor(report.score.grade)}`}>
                {report.score.grade}
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Grade</p>
                <p className="text-lg font-semibold text-foreground">
                  {report.score.percentage.toFixed(1)}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              {report.score.passed ? (
                <CheckCircle2 className="h-8 w-8 text-green-600" />
              ) : (
                <XCircle className="h-8 w-8 text-red-600" />
              )}
              <div>
                <p className="text-3xl font-bold text-foreground">
                  {report.score.passed ? 'Pass' : 'Fail'}
                </p>
                <p className="text-sm text-muted-foreground">Status</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Report Details */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Report Details
          </CardTitle>
          <CardDescription>
            Comprehensive marking information
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Student ID</p>
              <p className="text-lg font-medium text-foreground flex items-center gap-2">
                <User className="h-4 w-4" />
                {report.student_id}
              </p>
            </div>

            <div>
              <p className="text-sm text-muted-foreground">Assessment</p>
              <p className="text-lg font-medium text-foreground">
                {report.assessment_title}
              </p>
            </div>

            <div>
              <p className="text-sm text-muted-foreground">Marked At</p>
              <p className="text-lg font-medium text-foreground flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                {formatDate(report.marked_at)}
              </p>
            </div>

            <div>
              <p className="text-sm text-muted-foreground">Processing Time</p>
              <p className="text-lg font-medium text-foreground flex items-center gap-2">
                <Clock className="h-4 w-4" />
                {report.processing_time.toFixed(1)}s
              </p>
            </div>

            <div>
              <p className="text-sm text-muted-foreground">Number of Questions</p>
              <p className="text-lg font-medium text-foreground">
                {report.num_questions}
              </p>
            </div>

            <div>
              <p className="text-sm text-muted-foreground">Review Required</p>
              <p className="text-lg font-medium text-foreground">
                {report.requires_review ? (
                  <span className="text-yellow-600">Yes ⚠️</span>
                ) : (
                  <span className="text-green-600">No ✓</span>
                )}
              </p>
            </div>
          </div>

          {report.requires_review && (
            <div className="mt-4 p-4 rounded bg-yellow-50 border border-yellow-200">
              <p className="text-sm font-medium text-yellow-900">
                ⚠️ This report requires manual review
              </p>
              <p className="text-xs text-yellow-700 mt-1">
                Some answers may need additional verification or clarification
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Question Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Hash className="h-5 w-5" />
            Question-by-Question Breakdown
          </CardTitle>
          <CardDescription>
            Detailed evaluation for each question
          </CardDescription>
        </CardHeader>
        <CardContent>
          {report.question_evaluations && report.question_evaluations.length > 0 ? (
            <div className="space-y-4">
              {report.question_evaluations.map((qe, index) => (
                <Card key={qe.question_id} className="border-l-4 border-l-primary">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg flex items-center gap-2">
                        <Hash className="h-4 w-4" />
                        Question {qe.question_id}
                      </CardTitle>
                      <div className="flex items-center gap-3">
                        <div className={`px-3 py-1 rounded border text-sm font-semibold ${getQualityColor(qe.overall_quality)}`}>
                          {qe.overall_quality.toUpperCase()}
                        </div>
                        {qe.requires_human_review && (
                          <div className="px-3 py-1 rounded border text-sm font-semibold text-yellow-700 bg-yellow-100 border-yellow-300">
                            REVIEW REQUIRED
                          </div>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Score Summary */}
                    <div className="flex items-center gap-4 p-3 bg-gray-50 rounded">
                      <div className="flex items-center gap-2">
                        <Award className="h-5 w-5 text-primary" />
                        <span className="text-2xl font-bold text-foreground">
                          {qe.marks_awarded.toFixed(1)}
                        </span>
                        <span className="text-muted-foreground">/ {qe.max_marks.toFixed(1)}</span>
                      </div>
                      <div className="h-8 w-px bg-gray-300" />
                      <div className="text-lg font-semibold text-foreground">
                        {qe.percentage.toFixed(1)}%
                      </div>
                    </div>

                    {/* Strengths */}
                    {qe.strengths && qe.strengths.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-foreground mb-2 flex items-center gap-2">
                          <CheckCircle2 className="h-4 w-4 text-green-600" />
                          Strengths
                        </h4>
                        <ul className="space-y-2">
                          {qe.strengths.map((strength, idx) => (
                            <li key={idx} className="flex gap-2 text-sm text-foreground">
                              <span className="text-green-600 mt-0.5">•</span>
                              <span>{strength}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Weaknesses */}
                    {qe.weaknesses && qe.weaknesses.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-foreground mb-2 flex items-center gap-2">
                          <XCircle className="h-4 w-4 text-red-600" />
                          Weaknesses
                        </h4>
                        <ul className="space-y-2">
                          {qe.weaknesses.map((weakness, idx) => (
                            <li key={idx} className="flex gap-2 text-sm text-foreground">
                              <span className="text-red-600 mt-0.5">•</span>
                              <span>{weakness}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <FileText className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">
                No question breakdown available for this report
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
