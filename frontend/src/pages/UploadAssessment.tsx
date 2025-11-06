import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import FileUpload from '../components/FileUpload';
import Button from '../components/ui/Button';
import { uploadMarkingGuide } from '../lib/api/markingGuides';
import { FileText, CheckCircle2 } from 'lucide-react';

// Temporary inline type definition
interface QuestionSummary {
  question_number: number;
  max_marks: number;
  marking_criteria: string;
}

interface MarkingGuideResponse {
  id: string;
  filename: string;
  upload_time: string;
  total_questions: number;
  total_marks: number;
  questions: QuestionSummary[];
}

type UploadStatus = 'idle' | 'uploading' | 'success' | 'error';

export default function UploadAssessment() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>('idle');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState('');
  const [uploadedGuide, setUploadedGuide] = useState<MarkingGuideResponse | null>(null);

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setUploadStatus('idle');
    setErrorMessage('');
    setUploadedGuide(null);
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setUploadStatus('idle');
    setErrorMessage('');
    setUploadProgress(0);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploadStatus('uploading');
    setUploadProgress(0);
    setErrorMessage('');

    // Simulate upload progress
    const progressInterval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + 10;
      });
    }, 200);

    try {
      const response = await uploadMarkingGuide(selectedFile);
      clearInterval(progressInterval);
      setUploadProgress(100);
      setUploadStatus('success');
      setUploadedGuide(response);
    } catch (error: any) {
      clearInterval(progressInterval);
      setUploadStatus('error');
      setErrorMessage(
        error.response?.data?.detail ||
        'Failed to upload assessment. Please try again.'
      );
    }
  };

  const handleUploadAnother = () => {
    setSelectedFile(null);
    setUploadStatus('idle');
    setErrorMessage('');
    setUploadProgress(0);
    setUploadedGuide(null);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-foreground">Upload Assessment</h2>
        <p className="text-muted-foreground mt-2">
          Upload a PDF containing the questions and marking guide
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Select Assessment PDF</CardTitle>
          <CardDescription>
            The PDF should contain questions with their marking criteria and maximum marks
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <FileUpload
            accept=".pdf"
            maxSize={10 * 1024 * 1024}
            onFileSelect={handleFileSelect}
            onRemove={handleRemoveFile}
            selectedFile={selectedFile}
            uploadStatus={uploadStatus}
            uploadProgress={uploadProgress}
            errorMessage={errorMessage}
            disabled={uploadStatus === 'uploading'}
          />

          {selectedFile && uploadStatus === 'idle' && (
            <div className="flex justify-end">
              <Button onClick={handleUpload} size="lg">
                Upload Assessment
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {uploadStatus === 'success' && uploadedGuide && (
        <Card className="border-green-200 bg-green-50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-6 w-6 text-green-600" />
              <CardTitle className="text-green-900">Upload Successful!</CardTitle>
            </div>
            <CardDescription className="text-green-700">
              Your assessment has been processed and is ready for grading
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4 p-4 bg-white rounded-lg border border-green-200">
              <div>
                <p className="text-sm text-muted-foreground">Assessment ID</p>
                <p className="font-mono text-sm font-medium">{uploadedGuide.id}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Filename</p>
                <p className="text-sm font-medium truncate">{uploadedGuide.filename}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Questions</p>
                <p className="text-2xl font-bold text-primary">{uploadedGuide.total_questions}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Marks</p>
                <p className="text-2xl font-bold text-primary">{uploadedGuide.total_marks}</p>
              </div>
            </div>

            <div className="space-y-2">
              <h4 className="font-semibold text-foreground flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Questions Breakdown
              </h4>
              <div className="space-y-2">
                {uploadedGuide.questions.map((q, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-white rounded border border-green-200 flex justify-between items-center"
                  >
                    <span className="text-sm">Question {q.question_number}</span>
                    <span className="text-sm font-medium">{q.max_marks} marks</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex gap-3">
              <Button onClick={handleUploadAnother} variant="outline" className="flex-1">
                Upload Another Assessment
              </Button>
              <Button
                onClick={() => window.location.href = '/mark-answers'}
                className="flex-1"
              >
                Start Marking
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
