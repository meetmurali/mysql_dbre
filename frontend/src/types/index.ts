export interface Message {
  role: 'user' | 'assistant';
  content: string;
  tools_used?: ToolCall[];
  thinking?: string;
}

export interface ToolCall {
  name: string;
  input: Record<string, any>;
}

export interface ToolResult {
  tool_name: string;
  result: string;
}

export interface ChatEvent {
  type: 'text' | 'tool_use' | 'error';
  content?: string;
  tool?: string;
  input?: Record<string, any>;
  result?: string;
}
