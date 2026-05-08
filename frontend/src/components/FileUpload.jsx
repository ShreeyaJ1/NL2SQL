import React, { useState, useRef } from 'react';
import axios from 'axios';
import { UploadCloud, CheckCircle, Loader2, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';

const FileUpload = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('idle'); // idle, uploading, success, error
  const [errorMessage, setErrorMessage] = useState('');
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const validateAndSetFile = (selectedFile) => {
    if (!selectedFile) return;
    
    if (!selectedFile.name.endsWith('.db') && !selectedFile.name.endsWith('.sqlite')) {
      setStatus('error');
      setErrorMessage('Please upload a valid SQLite database file (.db or .sqlite).');
      return;
    }

    if (selectedFile.size > 50 * 1024 * 1024) {
      setStatus('error');
      setErrorMessage('File size exceeds the 50MB limit.');
      return;
    }

    setFile(selectedFile);
    setStatus('idle');
    setErrorMessage('');
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    validateAndSetFile(droppedFile);
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    validateAndSetFile(selectedFile);
  };

  const handleUpload = async () => {
    if (!file) return;

    setStatus('uploading');
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:5010/upload_db', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      setStatus('success');
      setTimeout(() => {
        onUploadSuccess(response.data);
      }, 1500);
    } catch (error) {
      setStatus('error');
      setErrorMessage(error.response?.data?.error || 'Failed to upload database.');
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-4">
      <div className="text-center mb-8 mt-12">
        <h1 className="text-4xl font-bold mb-4 tracking-tight">NL2SQL Assistant</h1>
        <p className="text-zinc-400 text-lg">Hello! I am your SQL assistant. Please upload an SQLite database (.db) to begin.</p>
      </div>

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className={`w-full max-w-xl p-8 rounded-2xl border-2 border-dashed transition-colors duration-200 ease-in-out ${
          isDragging ? 'border-blue-500 bg-blue-500/10' : 'border-zinc-700 bg-zinc-900/50 hover:border-zinc-500'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input 
          type="file" 
          accept=".db,.sqlite"
          className="hidden" 
          ref={fileInputRef} 
          onChange={handleFileChange}
        />
        
        <div className="flex flex-col items-center justify-center space-y-4">
          <div className="p-4 bg-zinc-800 rounded-full">
            <UploadCloud className="w-10 h-10 text-blue-400" />
          </div>
          
          <div className="text-center">
            {file ? (
              <p className="text-lg font-medium text-zinc-200">{file.name} ({(file.size / (1024 * 1024)).toFixed(2)} MB)</p>
            ) : (
              <>
                <p className="text-lg font-medium text-zinc-200">Drag & drop your database here</p>
                <p className="text-sm text-zinc-400 mt-1">or</p>
              </>
            )}
          </div>

          {!file && (
            <button 
              onClick={() => fileInputRef.current?.click()}
              className="px-6 py-2.5 mt-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
            >
              Browse Files
            </button>
          )}

          {file && status === 'idle' && (
            <button 
              onClick={handleUpload}
              className="px-8 py-3 mt-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl transition-all shadow-lg hover:shadow-blue-500/25 flex items-center space-x-2"
            >
              <UploadCloud className="w-5 h-5" />
              <span>Connect Database</span>
            </button>
          )}

          {status === 'uploading' && (
            <div className="flex flex-col items-center mt-4 space-y-2">
              <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
              <p className="text-zinc-400">Uploading and indexing...</p>
            </div>
          )}

          {status === 'success' && (
            <motion.div 
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="flex items-center space-x-2 text-green-400 mt-4 bg-green-400/10 px-4 py-2 rounded-lg"
            >
              <CheckCircle className="w-5 h-5" />
              <span>Upload successful! Redirecting...</span>
            </motion.div>
          )}

          {status === 'error' && (
            <motion.div 
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="flex items-center space-x-2 text-red-400 mt-4 bg-red-400/10 px-4 py-2 rounded-lg max-w-full"
            >
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span className="text-sm text-left truncate">{errorMessage}</span>
            </motion.div>
          )}
          
          <p className="text-xs text-zinc-500 mt-4">Maximum file size: 50MB</p>
        </div>
      </motion.div>
    </div>
  );
};

export default FileUpload;
