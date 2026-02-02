// frontend-body/lib/types.ts
// 對應資料庫中的 LogEntry 表格
export interface LogEntry {
  id: string;
  date: string;     // ISO 8601 Date String
  content: string;  // 原始筆記
  mood: number;     // 1-10
  focus: number;    // 1-10
  tags: string[];   // 從 content 提取的標籤
  created_at: string;
}

// 系統健康狀態 (檢查資料庫有沒有連上)
export interface SystemHealth {
  database_status: 'connected' | 'disconnected';
  latency_ms: number;
}

// 來自後端 Evolution Agent 的升級提案 [4]
export interface EvolutionProposal {
  id: string;
  model_name: string; // 例如 "gemini-2.0-pro"
  performance_score: number;
  reason: string; // 例如 "發現新模型在邏輯推理上提升了 20%"
  timestamp: string;
}

// 思考過程的簽名 (Thought Signature) [5]
export interface ThoughtProcess {
  observation: string;
  connection: string;
  strategy: string;
}

// 核心對話回應
export interface AgentResponse {
  thought_signature: ThoughtProcess; // 顯示在 UI 的「思考氣泡」中
  final_response: string;
  suggested_actions: string[];
}

// 系統狀態 (顯示目前是哪顆大腦在運作)
export interface SystemState {
  current_model: string; // "gemini-2.0-flash" or "pro"
  is_evolving: boolean;
  evolution_proposal?: EvolutionProposal; // 若有值，前端需彈出確認視窗
}


export type NodeType = 'memory' | 'concept' | 'agent_thought';

export interface GraphNode {
  id: string;
  label: string;
  type: NodeType;
  val: number;        // 節點大小 (基於重要性或 mood/focus 分數)
  color?: string;     // 覆蓋預設顏色 (用於強調)
  metadata?: {        // 攜帶額外資訊，點擊時顯示
    date?: string;
    preview?: string;
    mood?: number;
  };
}

export interface GraphLink {
  source: string;     // Node ID
  target: string;     // Node ID
  value: number;      // 連線粗細 (代表語意相似度 0.0 - 1.0)
  type: 'semantic' | 'chronological' | 'tag'; // 連線類型：語意關聯、時間順序、標籤歸類
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
  stats: {
    total_memories: number;
    current_focus: string; // 目前系統關注的主題
  };
}
