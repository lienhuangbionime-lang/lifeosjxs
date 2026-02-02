// frontend-body/lib/types.ts

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
