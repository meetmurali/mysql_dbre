import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Message as MessageType } from '../types';

interface MessageProps {
  message: MessageType;
}

export function Message({ message }: MessageProps) {
  const [showTools, setShowTools] = useState(false);
  const isUser = message.role === 'user';

  const copyToClipboard = async () => {
    await navigator.clipboard.writeText(message.content);
  };

  const downloadMessage = () => {
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(message.content));
    element.setAttribute('download', `message-${Date.now()}.txt`);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div className={`flex mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-xs lg:max-w-md xl:max-w-lg px-4 py-3 rounded-lg ${
          isUser
            ? 'bg-blue-600 text-white rounded-br-none'
            : 'bg-gray-200 text-gray-900 rounded-bl-none'
        }`}
      >
        {message.thinking && (
          <div className="mb-2 p-2 bg-opacity-20 bg-white rounded text-sm italic">
            <details>
              <summary>Claude is thinking...</summary>
              <p className="mt-1">{message.thinking}</p>
            </details>
          </div>
        )}

        <div className="prose prose-sm max-w-none">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>

        {message.tools_used && message.tools_used.length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-400 border-opacity-30">
            <button
              onClick={() => setShowTools(!showTools)}
              className="text-xs font-semibold hover:underline"
            >
              {showTools ? '▼' : '▶'} Tools Used ({message.tools_used.length})
            </button>
            {showTools && (
              <div className="mt-1 space-y-1 text-xs">
                {message.tools_used.map((tool, idx) => (
                  <details key={idx} className="bg-opacity-20 bg-white p-1 rounded">
                    <summary className="font-mono font-semibold cursor-pointer">
                      {tool.name}
                    </summary>
                    <pre className="mt-1 overflow-x-auto text-xs">
                      {JSON.stringify(tool.input, null, 2)}
                    </pre>
                  </details>
                ))}
              </div>
            )}
          </div>
        )}

        {!isUser && (
          <div className="mt-2 flex gap-2 text-xs">
            <button
              onClick={copyToClipboard}
              className="hover:underline opacity-70 hover:opacity-100"
            >
              Copy
            </button>
            <button
              onClick={downloadMessage}
              className="hover:underline opacity-70 hover:opacity-100"
            >
              Download
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
