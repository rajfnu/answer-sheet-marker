import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import Button from '../components/ui/Button';
import { getAllReportsWithDetails, type MarkingReportResponse } from '../lib/api/reports';
import { listMarkingGuides } from '../lib/api/markingGuides';
import {
  BarChart3,
  AlertCircle,
  User,
  Calendar,
  Award,
  CheckCircle2,
  XCircle,
  Clock
} from 'lucide-react';

type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export default function Reports() {
  const navigate = useNavigate();
  const [reports, setReports] = useState<MarkingReportResponse[]>([]);
  const [assessments, setAssessments] = useState<string[]>([]);
  const [selectedAssessment, setSelectedAssessment] = useState<string>('all');
  const [loadingState, setLoadingState] = useState<LoadingState>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoadingState('loading');
    setErrorMessage('');

    try {
      const [reportsData, assessmentsData] = await Promise.all([
        getAllReportsWithDetails(),
        listMarkingGuides()
      ]);

      setReports(reportsData);
      setAssessments(assessmentsData);
      setLoadingState('success');
    } catch (error: any) {
      setLoadingState('error');
      setErrorMessage(
        error.response?.data?.detail ||
        'Failed to load reports. Please try again.'
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

  const filteredReports = selectedAssessment === 'all'
    ? reports
    : reports.filter(r => r.marking_guide_id === selectedAssessment);

  const sortedReports = [...filteredReports].sort(
    (a, b) => new Date(b.marked_at).getTime() - new Date(a.marked_at).getTime()
  );

  // Statistics
  const totalReports = filteredReports.length;
  const passedCount = filteredReports.filter(r => r.score.passed).length;
  const avgScore = totalReports > 0
    ? filteredReports.reduce((sum, r) => sum + r.score.percentage, 0) / totalReports
    : 0;

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-foreground">Marking Reports</h2>
        <p className="text-muted-foreground mt-2">
          View and analyze all student marking results
        </p>
      </div>

      {loadingState === 'loading' && (
        <Card>
          <CardContent className="py-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="text-muted-foreground mt-4">Loading reports...</p>
          </CardContent>
        </Card>
      )}

      {loadingState === 'error' && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="py-6">
            <div className="flex items-center gap-3">
              <AlertCircle className="h-6 w-6 text-red-600" />
              <div>
                <p className="font-medium text-red-900">Error Loading Reports</p>
                <p className="text-sm text-red-700 mt-1">{errorMessage}</p>
              </div>
            </div>
            <Button onClick={loadData} variant="outline" className="mt-4">
              Try Again
            </Button>
          </CardContent>
        </Card>
      )}

      {loadingState === 'success' && (
        <>
          {/* Statistics */}
          {reports.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <BarChart3 className="h-8 w-8 text-primary" />
                    <div>
                      <p className="text-3xl font-bold text-foreground">{totalReports}</p>
                      <p className="text-sm text-muted-foreground">Total Reports</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <CheckCircle2 className="h-8 w-8 text-green-600" />
                    <div>
                      <p className="text-3xl font-bold text-foreground">
                        {passedCount}/{totalReports}
                      </p>
                      <p className="text-sm text-muted-foreground">Pass Rate</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <Award className="h-8 w-8 text-primary" />
                    <div>
                      <p className="text-3xl font-bold text-foreground">{avgScore.toFixed(1)}%</p>
                      <p className="text-sm text-muted-foreground">Average Score</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Filter */}
          {reports.length > 0 && assessments.length > 1 && (
            <Card>
              <CardContent className="py-4">
                <div className="flex items-center gap-4">
                  <label htmlFor="assessment-filter" className="text-sm font-medium text-foreground">
                    Filter by Assessment:
                  </label>
                  <select
                    id="assessment-filter"
                    value={selectedAssessment}
                    onChange={(e) => setSelectedAssessment(e.target.value)}
                    className="px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary bg-background text-foreground"
                  >
                    <option value="all">All Assessments ({reports.length})</option>
                    {assessments.map((assessmentId) => {
                      const count = reports.filter(r => r.marking_guide_id === assessmentId).length;
                      return (
                        <option key={assessmentId} value={assessmentId}>
                          {assessmentId} ({count})
                        </option>
                      );
                    })}
                  </select>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Reports List */}
          {reports.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <BarChart3 className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-foreground mb-2">
                  No Reports Yet
                </h3>
                <p className="text-muted-foreground mb-6">
                  Start marking answer sheets to generate reports
                </p>
                <Button onClick={() => navigate('/mark-answers')}>
                  Mark Answer Sheet
                </Button>
              </CardContent>
            </Card>
          ) : sortedReports.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <p className="text-muted-foreground">
                  No reports found for the selected assessment
                </p>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  All Reports ({sortedReports.length})
                </CardTitle>
                <CardDescription>
                  Click on any report to view detailed breakdown
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {sortedReports.map((report) => (
                    <div
                      key={report.report_id}
                      className="p-4 rounded border border-border bg-card hover:border-primary transition-all cursor-pointer"
                      onClick={() => navigate(`/reports/${report.report_id}`)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4 flex-1">
                          <div className="flex items-center gap-2">
                            <User className="h-4 w-4 text-muted-foreground" />
                            <div>
                              <p className="font-medium text-foreground">
                                {report.student_id}
                              </p>
                              <p className="text-xs text-muted-foreground">
                                {report.assessment_title}
                              </p>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-4">
                          <div className="text-right">
                            <p className="text-lg font-bold text-foreground">
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

                          <div className="flex flex-col items-end text-xs text-muted-foreground">
                            <div className="flex items-center gap-1">
                              <Calendar className="h-3 w-3" />
                              {formatDate(report.marked_at)}
                            </div>
                            <div className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {report.processing_time.toFixed(1)}s
                            </div>
                          </div>
                        </div>
                      </div>

                      {report.requires_review && (
                        <div className="mt-2 text-xs px-2 py-1 rounded bg-yellow-100 text-yellow-800 border border-yellow-200 inline-block">
                          ⚠️ Requires Review
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
