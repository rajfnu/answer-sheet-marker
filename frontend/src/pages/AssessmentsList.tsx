import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import Button from '../components/ui/Button';
import { getAllMarkingGuidesWithDetails } from '../lib/api/markingGuides';
import { FileText, Calendar, Hash, Award, Upload, AlertCircle, Tag } from 'lucide-react';
import type { MarkingGuideResponse } from '../types';

type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export default function AssessmentsList() {
  const navigate = useNavigate();
  const [assessments, setAssessments] = useState<MarkingGuideResponse[]>([]);
  const [loadingState, setLoadingState] = useState<LoadingState>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    loadAssessments();
  }, []);

  const loadAssessments = async () => {
    setLoadingState('loading');
    setErrorMessage('');

    try {
      const guides = await getAllMarkingGuidesWithDetails();
      setAssessments(guides);
      setLoadingState('success');
    } catch (error: any) {
      setLoadingState('error');
      setErrorMessage(
        error.response?.data?.detail ||
        'Failed to load assessments. Please try again.'
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

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-foreground">Assessments</h2>
          <p className="text-muted-foreground mt-2">
            View and manage all your uploaded assessments
          </p>
        </div>
        <Button onClick={() => navigate('/upload-assessment')} size="lg">
          <Upload className="h-4 w-4 mr-2" />
          Create New Assessment
        </Button>
      </div>

      {loadingState === 'loading' && (
        <Card>
          <CardContent className="py-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="text-muted-foreground mt-4">Loading assessments...</p>
          </CardContent>
        </Card>
      )}

      {loadingState === 'error' && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="py-6">
            <div className="flex items-center gap-3">
              <AlertCircle className="h-6 w-6 text-red-600" />
              <div>
                <p className="font-medium text-red-900">Error Loading Assessments</p>
                <p className="text-sm text-red-700 mt-1">{errorMessage}</p>
              </div>
            </div>
            <Button onClick={loadAssessments} variant="outline" className="mt-4">
              Try Again
            </Button>
          </CardContent>
        </Card>
      )}

      {loadingState === 'success' && assessments.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center">
            <FileText className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-foreground mb-2">
              No Assessments Yet
            </h3>
            <p className="text-muted-foreground mb-6">
              Get started by uploading your first assessment
            </p>
            <Button onClick={() => navigate('/upload-assessment')}>
              <Upload className="h-4 w-4 mr-2" />
              Create Assessment
            </Button>
          </CardContent>
        </Card>
      )}

      {loadingState === 'success' && assessments.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {assessments.map((assessment) => (
            <Card
              key={assessment.guide_id}
              className="hover:shadow-lg transition-shadow cursor-pointer"
              onClick={() => navigate(`/assessments/${assessment.guide_id}`)}
            >
              <CardHeader>
                <CardTitle className="text-lg flex items-start gap-2">
                  <FileText className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                  <span className="line-clamp-2">{assessment.title}</span>
                </CardTitle>
                <CardDescription className="space-y-1">
                  <div className="flex items-center gap-1 text-xs">
                    <Calendar className="h-3 w-3" />
                    {formatDate(assessment.created_at)}
                  </div>
                  <div className="flex items-center gap-1 text-xs font-mono bg-muted px-2 py-1 rounded w-fit">
                    <Tag className="h-3 w-3" />
                    <span className="font-semibold">ID:</span> {assessment.guide_id}
                  </div>
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center gap-2">
                    <Hash className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="text-2xl font-bold text-primary">
                        {assessment.num_questions}
                      </p>
                      <p className="text-xs text-muted-foreground">Questions</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Award className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="text-2xl font-bold text-primary">
                        {assessment.total_marks}
                      </p>
                      <p className="text-xs text-muted-foreground">Total Marks</p>
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t">
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/assessments/${assessment.guide_id}`);
                    }}
                  >
                    View Details
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
