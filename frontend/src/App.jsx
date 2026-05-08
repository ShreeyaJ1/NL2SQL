import React, { useState } from 'react';
import FileUpload from './components/FileUpload';
import ChatComponent from './components/ChatComponent';

function App() {
  const [isDbUploaded, setIsDbUploaded] = useState(false);
  const [dbStats, setDbStats] = useState(null);

  const handleUploadSuccess = (data) => {
    setDbStats(data);
    setIsDbUploaded(true);
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-50 font-sans selection:bg-blue-500/30">
      {!isDbUploaded ? (
        <FileUpload onUploadSuccess={handleUploadSuccess} />
      ) : (
        <ChatComponent dbStats={dbStats} />
      )}
    </div>
  );
}

export default App;
