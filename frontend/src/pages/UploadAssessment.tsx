import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import FileUpload from '../components/FileUpload';
import Button from '../components/ui/Button';
import { uploadMarkingGuide } from '../lib/api/markingGuides';
import { FileText, CheckCircle2 } from 'lucide-react';
import type { MarkingGuideResponse } from '../types';

type UploadStatus = 'idle' | 'uploading' | 'success' | 'error';

export default function UploadAssessment() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [subject, setSubject] = useState('');
  const [grade, setGrade] = useState('');
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
    if (!selectedFile || !title.trim()) return;

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
      const response = await uploadMarkingGuide(
        selectedFile,
        title.trim(),
        description.trim() || undefined,
        subject.trim() || undefined,
        grade.trim() || undefined
      );
      clearInterval(progressInterval);
      setUploadProgress(100);
      setUploadStatus('success');
      setUploadedGuide(response);
    } catch (error: any) {
      clearInterval(progressInterval);
      setUploadStatus('error');
      setErrorMessage(
        error.response?.data?.detail ||
        'Failed to create assessment. Please try again.'
      );
    }
  };

  const handleUploadAnother = () => {
    setSelectedFile(null);
    setTitle('');
    setDescription('');
    setSubject('');
    setGrade('');
    setUploadStatus('idle');
    setErrorMessage('');
    setUploadProgress(0);
    setUploadedGuide(null);
  };

  const isFormValid = selectedFile && title.trim();

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-foreground">Create Assessment</h2>
        <p className="text-muted-foreground mt-2">
          Set up a new assessment with marking guide and metadata
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Assessment Information</CardTitle>
          <CardDescription>
            Provide details about the assessment for better organization
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Assessment Name */}
          <div className="space-y-2">
            <label htmlFor="title" className="text-sm font-medium text-foreground">
              Assessment Name <span className="text-red-500">*</span>
            </label>
            <input
              id="title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Financial Accounting Final Exam"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              disabled={uploadStatus === 'uploading'}
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <label htmlFor="description" className="text-sm font-medium text-foreground">
              Description
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description of what this assessment covers"
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              disabled={uploadStatus === 'uploading'}
            />
          </div>

          {/* Subject and Grade */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label htmlFor="subject" className="text-sm font-medium text-foreground">
                Subject
              </label>
              <input
                id="subject"
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="e.g., Accounting, Mathematics"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                disabled={uploadStatus === 'uploading'}
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="grade" className="text-sm font-medium text-foreground">
                Grade Level
              </label>
              <input
                id="grade"
                type="text"
                value={grade}
                onChange={(e) => setGrade(e.target.value)}
                placeholder="e.g., Grade 10, Year 12"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                disabled={uploadStatus === 'uploading'}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Marking Guide PDF</CardTitle>
          <CardDescription>
            Upload the PDF containing questions with marking criteria and maximum marks
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
              <Button
                onClick={handleUpload}
                size="lg"
                disabled={!isFormValid}
              >
                Create Assessment
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
              <CardTitle className="text-green-900">Assessment Created Successfully!</CardTitle>
            </div>
            <CardDescription className="text-green-700">
              Your assessment has been processed and is ready for marking
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 bg-white rounded-lg border border-green-200 space-y-3">
              <div>
                <p className="text-sm text-muted-foreground">Assessment Name</p>
                <p className="text-lg font-semibold">{uploadedGuide.title}</p>
              </div>
              {uploadedGuide.description && (
                <div>
                  <p className="text-sm text-muted-foreground">Description</p>
                  <p className="text-sm">{uploadedGuide.description}</p>
                </div>
              )}
              <div className="grid grid-cols-2 gap-4">
                {uploadedGuide.subject && (
                  <div>
                    <p className="text-sm text-muted-foreground">Subject</p>
                    <p className="text-sm font-medium">{uploadedGuide.subject}</p>
                  </div>
                )}
                {uploadedGuide.grade && (
                  <div>
                    <p className="text-sm text-muted-foreground">Grade</p>
                    <p className="text-sm font-medium">{uploadedGuide.grade}</p>
                  </div>
                )}
                <div>
                  <p className="text-sm text-muted-foreground">Total Questions</p>
                  <p className="text-2xl font-bold text-primary">{uploadedGuide.num_questions}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total Marks</p>
                  <p className="text-2xl font-bold text-primary">{uploadedGuide.total_marks}</p>
                </div>
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
                Create Another Assessment
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
