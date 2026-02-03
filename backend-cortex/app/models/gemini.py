// Source Reference: backend-cortex/app/models/gemini.py
// 這是與 Python Pydantic 1:1 對應的型別定義

// 1. 潛意識思考痕跡
export interface ThoughtTrace {
  observation: string;
  reasoning: string;
  critical_check: string;
}

// 2. 任務項目
export interface TaskItem {
  title: string;
  status: 'PENDING' | 'COMPLETED';
  is_urgent: boolean;
}

// 3. 完整的結構化輸出 (Sorter Agent)
export interface LogAnalysisResult {
  thought_trace: ThoughtTrace;
  meta: {
    mood: number;
    focus: number;
    energy: number;
    tags: string[];
    date: string;
  };
  content: {
    summary: string;
    markdown_body: string;
    action_items: TaskItem[];
  };
}