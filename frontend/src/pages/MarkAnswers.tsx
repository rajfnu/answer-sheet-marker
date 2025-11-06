import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import FileUpload from '../components/FileUpload';
import Button from '../components/ui/Button';
import { listMarkingGuides } from '../lib/api/markingGuides';
import { markAnswerSheet } from '../lib/api/answerSheets';
import type { MarkingReportResponse } from '../lib/api/reports';
import { Upload, CheckCircle2, FileText, Award, Clock } from 'lucide-react';

type MarkingState = 'idle' | 'marking' | 'success' | 'error';

interface LocationState {
  assessmentId?: string;
}

export default function MarkAnswers() {
  const location = useLocation();
  const navigate = useNavigate();
  const locationState = location.state as LocationState | null;

  const [assessments, setAssessments] = useState<string[]>([]);
  const [selectedAssessment, setSelectedAssessment] = useState<string>('');
  const [studentId, setStudentId] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [markingState, setMarkingState] = useState<MarkingState>('idle');
  const [markingProgress, setMarkingProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState('');
  const [report, setReport] = useState<MarkingReportResponse | null>(null);
  const [loadingAssessments, setLoadingAssessments] = useState(true);

  useEffect(() => {
    loadAssessments();
  }, []);

  useEffect(() => {
    if (locationState?.assessmentId && assessments.includes(locationState.assessmentId)) {
      setSelectedAssessment(locationState.assessmentId);
    }
  }, [locationState, assessments]);

  const loadAssessments = async () => {
    setLoadingAssessments(true);
    try {
      const guides = await listMarkingGuides();
      setAssessments(guides);
      if (locationState?.assessmentId && guides.includes(locationState.assessmentId)) {
        setSelectedAssessment(locationState.assessmentId);
      } else if (guides.length > 0) {
        setSelectedAssessment(guides[0]);
      }
    } catch (error) {
      setErrorMessage('Failed to load assessments');
    } finally {
      setLoadingAssessments(false);
    }
  };

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setMarkingState('idle');
    setErrorMessage('');
    setReport(null);
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setMarkingState('idle');
    setErrorMessage('');
    setMarkingProgress(0);
  };

  const handleMark = async () => {
    if (!selectedFile || !selectedAssessment || !studentId.trim()) return;

    setMarkingState('marking');
    setMarkingProgress(0);
    setErrorMessage('');

    // Simulate progress for better UX
    const progressInterval = setInterval(() => {
      setMarkingProgress((prev) => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + 10;
      });
    }, 500);

    try {
      const result = await markAnswerSheet(selectedAssessment, studentId.trim(), selectedFile);
      clearInterval(progressInterval);
      setMarkingProgress(100);
      setMarkingState('success');
      setReport(result);
    } catch (error: any) {
      clearInterval(progressInterval);
      setMarkingState('error');
      setErrorMessage(
        error.response?.data?.detail ||
        'Failed to mark answer sheet. Please try again.'
      );
    }
  };

  const handleMarkAnother = () => {
    setSelectedFile(null);
    setStudentId('');
    setMarkingState('idle');
    setErrorMessage('');
    setMarkingProgress(0);
    setReport(null);
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

  const canSubmit = selectedAssessment && studentId.trim() && selectedFile && markingState === 'idle';

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-foreground">Mark Answer Sheet</h2>
        <p className="text-muted-foreground mt-2">
          Select an assessment, enter student details, and upload the answer sheet to grade
        </p>
      </div>

      {/* Form */}
      <Card>
        <CardHeader>
          <CardTitle>Marking Details</CardTitle>
          <CardDescription>
            Provide the assessment and student information
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Assessment Selection */}
          <div>
            <label htmlFor="assessment" className="block text-sm font-medium text-foreground mb-2">
              Select Assessment
            </label>
            {loadingAssessments ? (
              <div className="text-sm text-muted-foreground">Loading assessments...</div>
            ) : assessments.length === 0 ? (
              <div className="text-sm text-muted-foreground">
                No assessments found. Please upload an assessment first.
              </div>
            ) : (
              <select
                id="assessment"
                value={selectedAssessment}
                onChange={(e) => setSelectedAssessment(e.target.value)}
                disabled={markingState === 'marking'}
                className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary bg-background text-foreground"
              >
                {assessments.map((assessmentId) => (
                  <option key={assessmentId} value={assessmentId}>
                    {assessmentId}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Student ID */}
          <div>
            <label htmlFor="studentId" className="block text-sm font-medium text-foreground mb-2">
              Student ID
            </label>
            <input
              id="studentId"
              type="text"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
              disabled={markingState === 'marking'}
              placeholder="Enter student identifier"
              className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary bg-background text-foreground"
            />
          </div>

          {/* File Upload */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Answer Sheet PDF
            </label>
            <FileUpload
              accept=".pdf"
              maxSize={10 * 1024 * 1024}
              onFileSelect={handleFileSelect}
              onRemove={handleRemoveFile}
              selectedFile={selectedFile}
              uploadStatus={markingState === 'marking' ? 'uploading' : 'idle'}
              uploadProgress={markingProgress}
              errorMessage={errorMessage}
              disabled={markingState === 'marking'}
            />
          </div>

          {/* Submit Button */}
          {selectedFile && markingState === 'idle' && (
            <div className="flex justify-end pt-2">
              <Button onClick={handleMark} disabled={!canSubmit} size="lg">
                <Upload className="h-4 w-4 mr-2" />
                Mark Answer Sheet
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Success Result */}
      {markingState === 'success' && report && (
        <Card className="border-green-200 bg-green-50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-6 w-6 text-green-600" />
              <CardTitle className="text-green-900">Marking Complete!</CardTitle>
            </div>
            <CardDescription className="text-green-700">
              The answer sheet has been successfully graded
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Report Summary */}
            <div className="grid grid-cols-2 gap-4 p-4 bg-white rounded-lg border border-green-200">
              <div>
                <p className="text-sm text-muted-foreground">Student ID</p>
                <p className="font-mono text-sm font-medium">{report.student_id}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Report ID</p>
                <p className="font-mono text-sm font-medium">{report.report_id}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Score</p>
                <p className="text-2xl font-bold text-primary">
                  {report.score.total_marks.toFixed(1)}/{report.score.max_marks.toFixed(1)}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Percentage</p>
                <p className="text-2xl font-bold text-primary">{report.score.percentage.toFixed(1)}%</p>
              </div>
            </div>

            {/* Grade Badge */}
            <div className="flex items-center justify-center gap-4 p-4 bg-white rounded-lg border border-green-200">
              <div className="text-center">
                <p className="text-sm text-muted-foreground mb-2">Final Grade</p>
                <div className={`inline-block px-6 py-3 rounded border text-3xl font-bold ${getGradeColor(report.score.grade)}`}>
                  {report.score.grade}
                </div>
              </div>
              <div className="text-center">
                <p className="text-sm text-muted-foreground mb-2">Status</p>
                <p className={`text-lg font-semibold ${report.score.passed ? 'text-green-600' : 'text-red-600'}`}>
                  {report.score.passed ? 'PASSED' : 'FAILED'}
                </p>
              </div>
            </div>

            {/* Additional Info */}
            <div className="grid grid-cols-2 gap-4 p-4 bg-white rounded-lg border border-green-200">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-xs text-muted-foreground">Questions</p>
                  <p className="text-sm font-medium">{report.num_questions}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-xs text-muted-foreground">Processing Time</p>
                  <p className="text-sm font-medium">{report.processing_time.toFixed(1)}s</p>
                </div>
              </div>
              <div className="col-span-2 flex items-center gap-2">
                <Award className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-xs text-muted-foreground">Marked At</p>
                  <p className="text-sm font-medium">{formatDate(report.marked_at)}</p>
                </div>
              </div>
              {report.requires_review && (
                <div className="col-span-2">
                  <p className="text-sm px-3 py-2 rounded bg-yellow-100 text-yellow-800 border border-yellow-200">
                    ⚠️ This marking requires human review
                  </p>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              <Button onClick={handleMarkAnother} variant="outline" className="flex-1">
                Mark Another Sheet
              </Button>
              <Button
                onClick={() => navigate(`/reports/${report.report_id}`)}
                className="flex-1"
              >
                View Detailed Report
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
