#!/usr/bin/env python3
"""
Schema Evolution Assistant
AI 使用此工具來理解當前 schema 並生成遷移建議
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Literal

# Paths
SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"
REGISTRY_PATH = SCHEMAS_DIR / "registry.json"
EVOLUTION_LOG_PATH = SCHEMAS_DIR / "evolution_log.json"
MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"


class SchemaRegistry:
    """讀取和管理 schema registry"""
    
    def __init__(self):
        with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
            self.registry = json.load(f)
    
    def get_table_schema(self, table_name: str) -> Optional[Dict]:
        """獲取指定表的 schema"""
        return self.registry.get("tables", {}).get(table_name)
    
    def get_all_tables(self) -> List[str]:
        """獲取所有表名"""
        return list(self.registry.get("tables", {}).keys())
    
    def get_ai_instructions(self) -> Dict:
        """獲取 AI 操作指南"""
        return self.registry.get("ai_instructions", {})
    
    def has_column(self, table: str, column: str) -> bool:
        """檢查表中是否已有某個欄位"""
        table_schema = self.get_table_schema(table)
        if not table_schema:
            return False
        return column in table_schema.get("columns", {})


class MigrationSuggestion:
    """遷移建議生成器"""
    
    def __init__(self, registry: SchemaRegistry):
        self.registry = registry
    
    def analyze_request(self, user_request: str) -> Dict:
        """
        分析用戶需求，返回建議方案
        
        Args:
            user_request: 用戶的需求描述，例如「我想追蹤睡眠品質」
        
        Returns:
            包含多個方案的字典
        """
        # 簡單的關鍵詞分析（未來可以用 LLM 增強）
        request_lower = user_request.lower()
        
        # 判斷類型
        if any(word in request_lower for word in ['品質', '分數', '評分', '指標']):
            metric_type = 'simple_numeric'
        elif any(word in request_lower for word in ['記錄', '追蹤', '日誌']):
            metric_type = 'complex_tracking'
        elif any(word in request_lower for word in ['是否', '有沒有', '開關']):
            metric_type = 'boolean_flag'
        else:
            metric_type = 'unknown'
        
        return {
            "request": user_request,
            "detected_type": metric_type,
            "suggestions": self._generate_suggestions(metric_type, user_request)
        }
    
    def _generate_suggestions(self, metric_type: str, request: str) -> List[Dict]:
        """根據類型生成建議"""
        
        if metric_type == 'simple_numeric':
            return [
                {
                    "option": "A",
                    "method": "JSONB metadata",
                    "complexity": 1,
                    "performance": 3,
                    "migration_required": False,
                    "pros": ["立即可用", "無需遷移", "靈活"],
                    "cons": ["查詢效能較低", "無法建立索引"],
                    "implementation_time": "< 1 分鐘"
                },
                {
                    "option": "B",
                    "method": "New column",
                    "complexity": 3,
                    "performance": 5,
                    "migration_required": True,
                    "pros": ["查詢效能高", "可建立索引", "類型安全"],
                    "cons": ["需要資料庫遷移", "結構變更"],
                    "implementation_time": "5 分鐘"
                }
            ]
        
        elif metric_type == 'complex_tracking':
            return [
                {
                    "option": "A",
                    "method": "JSONB array in metadata",
                    "complexity": 2,
                    "performance": 3,
                    "migration_required": False,
                    "pros": ["快速實現", "靈活結構"],
                    "cons": ["查詢複雜", "效能限制"],
                    "implementation_time": "2 分鐘"
                },
                {
                    "option": "B",
                    "method": "Related table",
                    "complexity": 5,
                    "performance": 5,
                    "migration_required": True,
                    "pros": ["完整的關聯查詢", "最佳效能", "可擴展"],
                    "cons": ["實現複雜", "需要多處修改"],
                    "implementation_time": "15 分鐘"
                }
            ]
        
        elif metric_type == 'boolean_flag':
            return [
                {
                    "option": "A",
                    "method": "New boolean column",
                    "complexity": 2,
                    "performance": 5,
                    "migration_required": True,
                    "pros": ["簡單直接", "效能好", "類型安全"],
                    "cons": ["需要遷移"],
                    "implementation_time": "3 分鐘"
                }
            ]
        
        else:
            return [
                {
                    "option": "A",
                    "method": "JSONB metadata (default)",
                    "complexity": 1,
                    "performance": 3,
                    "migration_required": False,
                    "pros": ["最靈活"],
                    "cons": ["需要進一步分析"],
                    "implementation_time": "< 1 分鐘"
                }
            ]
    
    def generate_migration_sql(
        self, 
        table: str, 
        column_name: str, 
        column_type: str,
        default_value: Optional[str] = None,
        check_constraint: Optional[str] = None
    ) -> str:
        """生成 SQL 遷移腳本"""
        
        migration_id = self._get_next_migration_id()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        sql = f"""-- Migration {migration_id}: Add {column_name} to {table}
-- Generated at: {datetime.now().isoformat()}

BEGIN;

-- Add column
ALTER TABLE public.{table}
ADD COLUMN IF NOT EXISTS {column_name} {column_type}"""
        
        if default_value:
            sql += f"\nDEFAULT {default_value}"
        
        if check_constraint:
            sql += f"\nCHECK ({check_constraint})"
        
        sql += ";\n\n"
        
        # Add index if numeric
        if column_type.upper() in ['INT', 'INTEGER', 'FLOAT', 'NUMERIC']:
            sql += f"""-- Add index for better query performance
CREATE INDEX IF NOT EXISTS idx_{table}_{column_name}
ON public.{table}({column_name});

"""
        
        sql += """COMMIT;

-- Rollback script (if needed):
-- BEGIN;
-- ALTER TABLE public.{table} DROP COLUMN IF EXISTS {column_name};
-- COMMIT;
"""
        
        return sql
    
    def _get_next_migration_id(self) -> str:
        """獲取下一個遷移 ID"""
        with open(EVOLUTION_LOG_PATH, 'r', encoding='utf-8') as f:
            log = json.load(f)
        
        migrations = log.get("migrations", [])
        if not migrations:
            return "001"
        
        last_id = int(migrations[-1]["id"])
        return f"{last_id + 1:03d}"


def suggest_schema_change(user_request: str) -> Dict:
    """
    主入口：分析用戶需求並返回建議
    
    Usage:
        result = suggest_schema_change("我想追蹤睡眠品質")
        print(result)
    """
    registry = SchemaRegistry()
    suggester = MigrationSuggestion(registry)
    
    return suggester.analyze_request(user_request)


def generate_migration(
    table: str,
    column_name: str,
    column_type: str,
    **kwargs
) -> str:
    """
    生成遷移腳本
    
    Usage:
        sql = generate_migration(
            table="memories",
            column_name="sleep_quality",
            column_type="INT",
            default_value="5",
            check_constraint="sleep_quality >= 0 AND sleep_quality <= 10"
        )
        print(sql)
    """
    registry = SchemaRegistry()
    suggester = MigrationSuggestion(registry)
    
    return suggester.generate_migration_sql(table, column_name, column_type, **kwargs)


if __name__ == "__main__":
    # 測試
    print("=== Schema Evolution Assistant ===\n")
    
    # Test 1: 分析需求
    print("[Test 1] 分析用戶需求")
    result = suggest_schema_change("我想追蹤睡眠品質")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: 生成遷移腳本
    print("[Test 2] 生成遷移腳本")
    sql = generate_migration(
        table="memories",
        column_name="sleep_quality",
        column_type="INT",
        default_value="5",
        check_constraint="sleep_quality >= 0 AND sleep_quality <= 10"
    )
    print(sql)
