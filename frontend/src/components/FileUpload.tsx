import { useCallback, useState } from 'react';
import { Upload, File, X, CheckCircle, AlertCircle } from 'lucide-react';
import { cn } from '../lib/utils';
import { formatFileSize } from '../lib/utils';
import Button from './ui/Button';

interface FileUploadProps {
  accept?: string;
  maxSize?: number;
  onFileSelect: (file: File) => void;
  onRemove?: () => void;
  disabled?: boolean;
  selectedFile?: File | null;
  uploadStatus?: 'idle' | 'uploading' | 'success' | 'error';
  uploadProgress?: number;
  errorMessage?: string;
}

export default function FileUpload({
  accept = '.pdf',
  maxSize = 10 * 1024 * 1024, // 10MB default
  onFileSelect,
  onRemove,
  disabled = false,
  selectedFile = null,
  uploadStatus = 'idle',
  uploadProgress = 0,
  errorMessage,
}: FileUploadProps) {
  const [isDragActive, setIsDragActive] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragActive(true);
    } else if (e.type === 'dragleave') {
      setIsDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragActive(false);

      if (disabled) return;

      const files = e.dataTransfer.files;
      if (files && files.length > 0) {
        const file = files[0];
        if (file.size > maxSize) {
          alert(`File size must be less than ${formatFileSize(maxSize)}`);
          return;
        }
        onFileSelect(file);
      }
    },
    [disabled, maxSize, onFileSelect]
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (disabled) return;

      const files = e.target.files;
      if (files && files.length > 0) {
        const file = files[0];
        if (file.size > maxSize) {
          alert(`File size must be less than ${formatFileSize(maxSize)}`);
          return;
        }
        onFileSelect(file);
      }
    },
    [disabled, maxSize, onFileSelect]
  );

  const handleRemove = useCallback(() => {
    if (onRemove) {
      onRemove();
    }
  }, [onRemove]);

  return (
    <div className="w-full">
      {!selectedFile ? (
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={cn(
            'relative border-2 border-dashed rounded-lg p-12 text-center transition-colors cursor-pointer',
            isDragActive
              ? 'border-primary bg-primary/5'
              : 'border-border hover:border-primary/50 hover:bg-accent/50',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
        >
          <input
            type="file"
            accept={accept}
            onChange={handleFileInput}
            disabled={disabled}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
          />
          <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-lg font-medium text-foreground mb-2">
            Drop your file here, or click to browse
          </p>
          <p className="text-sm text-muted-foreground">
            Supports {accept} files up to {formatFileSize(maxSize)}
          </p>
        </div>
      ) : (
        <div className="border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <File className="h-8 w-8 text-primary flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="font-medium text-foreground truncate">{selectedFile.name}</p>
                <p className="text-sm text-muted-foreground">{formatFileSize(selectedFile.size)}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {uploadStatus === 'success' && <CheckCircle className="h-5 w-5 text-green-500" />}
              {uploadStatus === 'error' && <AlertCircle className="h-5 w-5 text-destructive" />}
              {uploadStatus === 'idle' && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRemove}
                  disabled={disabled}
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>

          {uploadStatus === 'uploading' && (
            <div className="mt-4">
              <div className="w-full bg-secondary rounded-full h-2">
                <div
                  className="bg-primary h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="text-sm text-muted-foreground mt-2 text-center">
                Uploading... {uploadProgress}%
              </p>
            </div>
          )}

          {uploadStatus === 'error' && errorMessage && (
            <div className="mt-4 p-3 bg-destructive/10 border border-destructive/20 rounded-md">
              <p className="text-sm text-destructive">{errorMessage}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
