import { useState, useCallback } from 'react';
import { Message, ToolCall } from '../types';

const API_BASE_URL = 'http://localhost:8000';

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (userMessage: string) => {
    if (!userMessage.trim()) return;

    setError(null);
    setIsLoading(true);

    try {
      // Add user message to history
      const newMessage: Message = {
        role: 'user',
        content: userMessage,
      };
      setMessages((prev) => [...prev, newMessage]);

      // Call the chat API
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          history: messages,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      let assistantContent = '';
      const toolsCalled: ToolCall[] = [];

      // Handle streaming response
      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');

        // Process all complete lines
        for (let i = 0; i < lines.length - 1; i++) {
          const line = lines[i];
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === 'text') {
                assistantContent += data.content;
              } else if (data.type === 'tool_use') {
                toolsCalled.push({
                  name: data.tool,
                  input: data.input,
                });
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e);
            }
          }
        }

        // Keep the last incomplete line in the buffer
        buffer = lines[lines.length - 1];
      }

      // Process any remaining data
      if (buffer && buffer.startsWith('data: ')) {
        try {
          const data = JSON.parse(buffer.slice(6));
          if (data.type === 'text') {
            assistantContent += data.content;
          } else if (data.type === 'tool_use') {
            toolsCalled.push({
              name: data.tool,
              input: data.input,
            });
          }
        } catch (e) {
          console.error('Error parsing final SSE data:', e);
        }
      }

      const assistantMsg: Message = {
        role: 'assistant',
        content: assistantContent,
        tools_used: toolsCalled.length > 0 ? toolsCalled : undefined,
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setIsLoading(false);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);
      setIsLoading(false);
    }
  }, [messages]);

  const clearHistory = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearHistory,
  };
}
