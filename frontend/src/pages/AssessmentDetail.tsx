import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import Button from '../components/ui/Button';
import { getMarkingGuide } from '../lib/api/markingGuides';
import { getReportsByAssessment, type MarkingReportResponse } from '../lib/api/reports';
import type { MarkingGuideResponse } from '../types';
import {
  FileText,
  Calendar,
  Hash,
  Award,
  Upload,
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Clock,
  User,
  ChevronDown,
  ChevronUp,
  BookOpen,
  ListChecks,
  AlertTriangle,
  Lightbulb
} from 'lucide-react';

type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export default function AssessmentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [assessment, setAssessment] = useState<MarkingGuideResponse | null>(null);
  const [reports, setReports] = useState<MarkingReportResponse[]>([]);
  const [loadingState, setLoadingState] = useState<LoadingState>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const [expandedQuestionId, setExpandedQuestionId] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadAssessmentData(id);
    }
  }, [id]);

  const loadAssessmentData = async (guideId: string) => {
    setLoadingState('loading');
    setErrorMessage('');

    try {
      const [assessmentData, reportsData] = await Promise.all([
        getMarkingGuide(guideId),
        getReportsByAssessment(guideId)
      ]);

      setAssessment(assessmentData);
      setReports(reportsData);
      setLoadingState('success');
    } catch (error: any) {
      setLoadingState('error');
      setErrorMessage(
        error.response?.data?.detail ||
        'Failed to load assessment details. Please try again.'
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

  if (loadingState === 'loading') {
    return (
      <div className="max-w-7xl mx-auto">
        <Card>
          <CardContent className="py-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="text-muted-foreground mt-4">Loading assessment details...</p>
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
                <p className="font-medium text-red-900">Error Loading Assessment</p>
                <p className="text-sm text-red-700 mt-1">{errorMessage}</p>
              </div>
            </div>
            <div className="flex gap-3 mt-4">
              <Button onClick={() => navigate('/assessments')} variant="outline">
                Back to Assessments
              </Button>
              <Button onClick={() => id && loadAssessmentData(id)}>
                Try Again
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!assessment) {
    return null;
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="outline"
            onClick={() => navigate('/assessments')}
            className="flex items-center gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back
          </Button>
          <div>
            <h2 className="text-3xl font-bold text-foreground">{assessment.title}</h2>
            <p className="text-sm text-muted-foreground mt-1 flex items-center gap-2">
              <Calendar className="h-3 w-3" />
              Uploaded {formatDate(assessment.created_at)}
            </p>
          </div>
        </div>
        <Button
          onClick={() => navigate('/mark-answers', { state: { assessmentId: assessment.guide_id } })}
          size="lg"
        >
          <Upload className="h-4 w-4 mr-2" />
          Mark Answer Sheet
        </Button>
      </div>

      {/* Assessment Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Hash className="h-8 w-8 text-primary" />
              <div>
                <p className="text-3xl font-bold text-foreground">{assessment.num_questions}</p>
                <p className="text-sm text-muted-foreground">Questions</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Award className="h-8 w-8 text-primary" />
              <div>
                <p className="text-3xl font-bold text-foreground">{assessment.total_marks}</p>
                <p className="text-sm text-muted-foreground">Total Marks</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card
          className={reports.length > 0 ? "cursor-pointer hover:border-primary transition-all" : ""}
          onClick={() => {
            if (reports.length > 0) {
              document.getElementById('student-reports')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
          }}
        >
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <User className="h-8 w-8 text-primary" />
              <div>
                <p className="text-3xl font-bold text-foreground">{reports.length}</p>
                <p className="text-sm text-muted-foreground">Students Marked</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Questions List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Questions Breakdown
          </CardTitle>
          <CardDescription>
            Overview of all questions in this assessment
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {assessment.questions.map((question, idx) => {
              const isExpanded = expandedQuestionId === question.question_id;

              return (
                <div
                  key={idx}
                  className="rounded border border-border bg-card transition-all"
                >
                  {/* Question Header - Clickable */}
                  <div
                    className="p-3 flex justify-between items-center hover:border-primary hover:bg-accent cursor-pointer transition-colors"
                    onClick={() => setExpandedQuestionId(isExpanded ? null : question.question_id)}
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-medium text-foreground">
                        Question {question.question_number}
                      </span>
                      <span className="text-xs px-2 py-1 rounded bg-muted text-muted-foreground">
                        {question.question_type}
                      </span>
                      <span className="text-xs px-2 py-1 rounded bg-blue-100 text-blue-700">
                        {question.key_concepts.length} concepts
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="font-medium text-primary">{question.max_marks} marks</span>
                      {isExpanded ? (
                        <ChevronUp className="h-5 w-5 text-muted-foreground" />
                      ) : (
                        <ChevronDown className="h-5 w-5 text-muted-foreground" />
                      )}
                    </div>
                  </div>

                  {/* Expanded Content */}
                  {isExpanded && (
                    <div className="p-4 border-t border-border bg-muted/30 space-y-4">
                      {/* Question Text */}
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <BookOpen className="h-4 w-4 text-primary" />
                          <h4 className="font-semibold text-foreground">Question</h4>
                        </div>
                        <p className="text-sm text-foreground bg-background p-3 rounded border border-border">
                          {question.question_text}
                        </p>
                      </div>

                      {/* Key Concepts */}
                      {question.key_concepts.length > 0 && (
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <ListChecks className="h-4 w-4 text-primary" />
                            <h4 className="font-semibold text-foreground">Key Concepts & Marking Criteria</h4>
                          </div>
                          <div className="space-y-2">
                            {question.key_concepts.map((concept, conceptIdx) => (
                              <div
                                key={conceptIdx}
                                className="bg-background p-3 rounded border border-border"
                              >
                                <div className="flex justify-between items-start mb-1">
                                  <span className="font-medium text-foreground">{concept.concept}</span>
                                  <div className="flex items-center gap-2">
                                    <span className="text-sm font-medium text-primary">{concept.points} pts</span>
                                    {concept.mandatory && (
                                      <span className="text-xs px-2 py-0.5 rounded bg-red-100 text-red-700">
                                        Required
                                      </span>
                                    )}
                                  </div>
                                </div>
                                {concept.description && (
                                  <p className="text-xs text-muted-foreground mt-1">{concept.description}</p>
                                )}
                                {concept.keywords.length > 0 && (
                                  <div className="flex gap-1 mt-2 flex-wrap">
                                    {concept.keywords.map((keyword, kwIdx) => (
                                      <span
                                        key={kwIdx}
                                        className="text-xs px-2 py-0.5 rounded bg-blue-50 text-blue-700"
                                      >
                                        {keyword}
                                      </span>
                                    ))}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Evaluation Criteria */}
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <Award className="h-4 w-4 text-primary" />
                          <h4 className="font-semibold text-foreground">Evaluation Criteria</h4>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          <div className="bg-green-50 border border-green-200 p-2 rounded">
                            <p className="text-xs font-semibold text-green-900 mb-1">Excellent</p>
                            <p className="text-xs text-green-700">{question.evaluation_criteria.excellent}</p>
                          </div>
                          <div className="bg-blue-50 border border-blue-200 p-2 rounded">
                            <p className="text-xs font-semibold text-blue-900 mb-1">Good</p>
                            <p className="text-xs text-blue-700">{question.evaluation_criteria.good}</p>
                          </div>
                          <div className="bg-yellow-50 border border-yellow-200 p-2 rounded">
                            <p className="text-xs font-semibold text-yellow-900 mb-1">Satisfactory</p>
                            <p className="text-xs text-yellow-700">{question.evaluation_criteria.satisfactory}</p>
                          </div>
                          <div className="bg-red-50 border border-red-200 p-2 rounded">
                            <p className="text-xs font-semibold text-red-900 mb-1">Poor</p>
                            <p className="text-xs text-red-700">{question.evaluation_criteria.poor}</p>
                          </div>
                        </div>
                      </div>

                      {/* Common Mistakes */}
                      {question.common_mistakes.length > 0 && (
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <AlertTriangle className="h-4 w-4 text-orange-500" />
                            <h4 className="font-semibold text-foreground">Common Mistakes to Watch For</h4>
                          </div>
                          <ul className="space-y-1">
                            {question.common_mistakes.map((mistake, mistakeIdx) => (
                              <li key={mistakeIdx} className="text-sm text-orange-700 flex items-start gap-2">
                                <span className="text-orange-500 mt-0.5">•</span>
                                {mistake}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Sample Answer */}
                      {question.sample_answer && (
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <Lightbulb className="h-4 w-4 text-yellow-500" />
                            <h4 className="font-semibold text-foreground">Sample Answer</h4>
                          </div>
                          <p className="text-sm text-foreground bg-background p-3 rounded border border-border italic">
                            {question.sample_answer}
                          </p>
                        </div>
                      )}

                      {/* Instructions */}
                      {question.instructions && (
                        <div className="bg-blue-50 border border-blue-200 p-3 rounded">
                          <p className="text-sm text-blue-900">
                            <span className="font-semibold">Marking Instructions: </span>
                            {question.instructions}
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Student Reports */}
      <Card id="student-reports">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            Student Reports
          </CardTitle>
          <CardDescription>
            {reports.length === 0
              ? 'No students have been marked yet'
              : `${reports.length} student${reports.length === 1 ? '' : 's'} marked`
            }
          </CardDescription>
        </CardHeader>
        <CardContent>
          {reports.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground mb-4">
                No answer sheets have been marked yet for this assessment
              </p>
              <Button onClick={() => navigate('/mark-answers', { state: { assessmentId: assessment.guide_id } })}>
                <Upload className="h-4 w-4 mr-2" />
                Mark First Answer Sheet
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {reports
                .sort((a, b) => new Date(b.marked_at).getTime() - new Date(a.marked_at).getTime())
                .map((report) => (
                  <div
                    key={report.report_id}
                    className="p-4 rounded border border-border bg-card hover:border-primary transition-all cursor-pointer"
                    onClick={() => navigate(`/reports/${report.report_id}`)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div>
                          <p className="font-medium text-foreground">
                            {report.student_id}
                          </p>
                          <p className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
                            <Clock className="h-3 w-3" />
                            {formatDate(report.marked_at)}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="text-2xl font-bold text-foreground">
                            {report.score.total_marks.toFixed(1)}/{report.score.max_marks.toFixed(1)}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {report.score.percentage.toFixed(1)}%
                          </p>
                        </div>

                        <div className={`px-3 py-1 rounded border font-semibold ${getGradeColor(report.score.grade)}`}>
                          {report.score.grade}
                        </div>

                        {report.score.passed ? (
                          <CheckCircle2 className="h-5 w-5 text-green-600" />
                        ) : (
                          <XCircle className="h-5 w-5 text-red-600" />
                        )}

                        {report.requires_review && (
                          <span className="text-xs px-2 py-1 rounded bg-yellow-100 text-yellow-700 border border-yellow-200">
                            Review Required
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
