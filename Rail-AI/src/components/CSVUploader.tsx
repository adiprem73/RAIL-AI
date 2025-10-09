import { useState, useCallback } from 'react';
import { Upload, Download, FileText } from 'lucide-react';
import type { DatasetType } from '../types';
import { api } from '../services/api';

interface CSVUploaderProps {
  dataset: DatasetType;
  onUploadComplete: () => void;
}

export default function CSVUploader({ dataset, onUploadComplete }: CSVUploaderProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.name.endsWith('.csv')) {
        setFile(droppedFile);
        setError(null);
      } else {
        setError('Please upload a CSV file');
      }
    }
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (selectedFile.name.endsWith('.csv')) {
        setFile(selectedFile);
        setError(null);
      } else {
        setError('Please upload a CSV file');
      }
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);

    try {
      const result = await api.uploadDataset(dataset, file);
      alert(`Successfully uploaded ${result.records_created} records`);
      setFile(null);
      onUploadComplete();
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const blob = await api.getTemplate(dataset);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${dataset}_template.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      setError(err.message || 'Failed to download template');
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-sm font-medium text-gray-700">
          Upload CSV for {dataset}
        </h3>
        <button
          onClick={handleDownloadTemplate}
          className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
        >
          <Download className="h-3 w-3 mr-1" />
          Template
        </button>
      </div>

      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-6 text-center ${
          dragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 bg-gray-50'
        }`}
      >
        <Upload className="mx-auto h-8 w-8 text-gray-400" />
        <p className="mt-2 text-sm text-gray-600">
          Drag and drop CSV file here, or{' '}
          <label className="text-blue-600 hover:text-blue-500 cursor-pointer">
            browse
            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="hidden"
            />
          </label>
        </p>

        {file && (
          <div className="mt-3 flex items-center justify-center text-sm text-gray-600">
            <FileText className="h-4 w-4 mr-2" />
            {file.name}
          </div>
        )}
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-3">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {file && (
        <button
          onClick={handleUpload}
          disabled={uploading}
          className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
        >
          {uploading ? 'Uploading...' : 'Upload to Server'}
        </button>
      )}
    </div>
  );
}
