import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, TerminalSquare, AlertTriangle, RefreshCw, Server, Search } from 'lucide-react';

const MessageBubble = ({ message, onRetry }) => {
  const isBot = message.role === 'bot';
  
  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex w-full mb-6 ${isBot ? 'justify-start' : 'justify-end'}`}
    >
      <div className={`max-w-[85%] md:max-w-[75%] rounded-2xl p-5 ${
        isBot ? 'bg-zinc-900 border border-zinc-800' : 'bg-blue-600 text-white'
      }`}>
        {isBot && (
          <div className="flex items-center space-x-2 mb-3 text-zinc-400">
            <Server className="w-4 h-4" />
            <span className="text-xs font-semibold uppercase tracking-wider">NL2SQL Assistant</span>
          </div>
        )}
        
        {message.type === 'error' ? (
          <div className="space-y-4">
            <div className="flex items-start space-x-3 text-red-400 bg-red-400/10 p-4 rounded-xl border border-red-500/20">
              <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <p className="text-sm leading-relaxed">{message.content}</p>
            </div>
            {onRetry && (
              <button 
                onClick={onRetry}
                className="flex items-center space-x-2 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm transition-colors text-zinc-200"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Retry</span>
              </button>
            )}
          </div>
        ) : (
          <div className="text-sm md:text-base leading-relaxed break-words text-zinc-200 whitespace-pre-wrap">
            {message.content}
          </div>
        )}

        {/* Render SQL Block if present */}
        {message.sql && (
          <div className="mt-4 bg-black/50 rounded-xl overflow-hidden border border-zinc-800">
            <div className="flex items-center space-x-2 px-4 py-2 bg-zinc-800/50 border-b border-zinc-800">
              <TerminalSquare className="w-4 h-4 text-zinc-400" />
              <span className="text-xs font-mono text-zinc-400">Generated SQL</span>
              {message.source && (
                 <span className="ml-auto text-[10px] bg-zinc-700 px-2 py-0.5 rounded text-zinc-300">
                   {message.source}
                 </span>
              )}
            </div>
            <div className="p-4 overflow-x-auto">
              <code className="text-sm font-mono text-blue-300 whitespace-pre">
                {message.sql}
              </code>
            </div>
          </div>
        )}

        {/* Render Data Table if present */}
        {message.columns && message.rows && (
          <div className="mt-4 rounded-xl overflow-hidden border border-zinc-800">
             <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-zinc-400 uppercase bg-zinc-800/50">
                  <tr>
                    {message.columns.map((col, idx) => (
                      <th key={idx} className="px-4 py-3 font-medium whitespace-nowrap">{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800">
                  {message.rows.length > 0 ? (
                    message.rows.map((row, rIdx) => (
                      <tr key={rIdx} className="hover:bg-zinc-800/30 transition-colors">
                        {row.map((cell, cIdx) => (
                          <td key={cIdx} className="px-4 py-3 text-zinc-300 whitespace-nowrap">
                            {cell !== null ? String(cell) : <span className="text-zinc-600 italic">null</span>}
                          </td>
                        ))}
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={message.columns.length} className="px-4 py-8 text-center text-zinc-500 italic">
                        No results found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            {message.rowCount !== undefined && (
              <div className="bg-zinc-800/30 px-4 py-2 text-xs text-zinc-500 border-t border-zinc-800 flex justify-between">
                <span>{message.rowCount} row(s) returned</span>
              </div>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
};

const ChatComponent = ({ dbStats }) => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'bot',
      type: 'text',
      content: `Database connected successfully! I've indexed ${dbStats?.tables || 0} tables.\n\nWhat would you like to know about your data?`
    }
  ]);
  const [input, setInput] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isThinking]);

  const handleSend = async (queryToSubmit) => {
    const query = queryToSubmit || input;
    if (!query.trim() || isThinking) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      type: 'text',
      content: query.trim()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsThinking(true);

    try {
      const response = await axios.post('http://localhost:5010/api/query', {
        question: query.trim()
      });

      const data = response.data;
      
      const botMessage = {
        id: Date.now() + 1,
        role: 'bot',
        type: data.success ? 'data' : 'error',
        content: data.success ? (data.message || 'Here are the results for your query:') : (data.message || data.error),
        sql: data.sql,
        columns: data.columns,
        rows: data.rows,
        rowCount: data.row_count,
        source: data.source,
        originalQuery: query.trim() // store for retry
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const botMessage = {
        id: Date.now() + 1,
        role: 'bot',
        type: 'error',
        content: error.response?.data?.message || error.response?.data?.error || 'Failed to connect to the server or process your query.',
        originalQuery: query.trim()
      };
      setMessages(prev => [...prev, botMessage]);
    } finally {
      setIsThinking(false);
    }
  };

  return (
    <div className="flex flex-col h-screen max-h-[100dvh] bg-zinc-950">
      {/* Header */}
      <header className="flex-shrink-0 bg-zinc-900/80 backdrop-blur-md border-b border-zinc-800 p-4 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
            <Search className="w-4 h-4 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-zinc-100 leading-tight">NL2SQL Assistant</h2>
            <p className="text-xs text-green-400 flex items-center">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500 mr-1.5"></span>
              Connected to {dbStats?.db_name || 'Database'}
            </p>
          </div>
        </div>
      </header>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6 scroll-smooth">
        <div className="max-w-4xl mx-auto">
          {messages.map(msg => (
            <MessageBubble 
              key={msg.id} 
              message={msg} 
              onRetry={msg.type === 'error' ? () => handleSend(msg.originalQuery) : undefined}
            />
          ))}
          
          {isThinking && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex justify-start mb-6"
            >
              <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 flex items-center space-x-2 w-24">
                <div className="flex space-x-1.5">
                  <motion.div 
                    animate={{ y: [0, -5, 0] }} 
                    transition={{ duration: 0.6, repeat: Infinity, delay: 0 }}
                    className="w-2 h-2 rounded-full bg-zinc-500"
                  />
                  <motion.div 
                    animate={{ y: [0, -5, 0] }} 
                    transition={{ duration: 0.6, repeat: Infinity, delay: 0.2 }}
                    className="w-2 h-2 rounded-full bg-zinc-500"
                  />
                  <motion.div 
                    animate={{ y: [0, -5, 0] }} 
                    transition={{ duration: 0.6, repeat: Infinity, delay: 0.4 }}
                    className="w-2 h-2 rounded-full bg-zinc-500"
                  />
                </div>
              </div>
            </motion.div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="flex-shrink-0 p-4 md:p-6 bg-gradient-to-t from-zinc-950 via-zinc-950 to-transparent">
        <div className="max-w-4xl mx-auto relative group">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Ask a question about your data..."
            className="w-full bg-zinc-900 border border-zinc-700 text-zinc-100 rounded-2xl py-4 pl-5 pr-14 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none overflow-hidden transition-all shadow-lg hover:border-zinc-600"
            rows="1"
            style={{ minHeight: '60px', maxHeight: '200px' }}
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isThinking}
            className="absolute right-3 bottom-3 p-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:hover:bg-blue-600 transition-colors shadow-sm"
          >
            <Send className="w-5 h-5 ml-0.5 mt-0.5" />
          </button>
        </div>
        <p className="text-center text-xs text-zinc-600 mt-3">
          SQL generated by AI. Always verify before making business decisions.
        </p>
      </div>
    </div>
  );
};

export default ChatComponent;
