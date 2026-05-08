import { ChatWindow } from './components/ChatWindow';
import { MessageInput } from './components/MessageInput';
import { useChat } from './hooks/useChat';
import './App.css';

function App() {
  const { messages, isLoading, error, sendMessage, clearHistory } = useChat();

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">MySQL DBRE Agent</h1>
          <p className="text-sm text-gray-600">Database Reliability Engineering Assistant</p>
        </div>
        {messages.length > 0 && (
          <button
            onClick={clearHistory}
            className="px-4 py-2 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 font-medium"
          >
            Clear History
          </button>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mx-4 mt-4 rounded">
          <p className="font-bold">Error</p>
          <p>{error}</p>
        </div>
      )}

      {/* Chat Window */}
      <ChatWindow messages={messages} isLoading={isLoading} />

      {/* Input Area */}
      <MessageInput onSend={sendMessage} isLoading={isLoading} />
    </div>
  );
}

export default App;
