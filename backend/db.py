"""
数据库模块 - PostgreSQL 持久化存储
用于 Render 部署时持久化用户配置
"""

import os
import json
from typing import Optional, Dict, Any

# 数据库 URL（从环境变量获取，Render 会自动注入）
DATABASE_URL = os.environ.get('DATABASE_URL')


def get_db_connection():
    """获取数据库连接"""
    if not DATABASE_URL:
        return None
    
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    except Exception as e:
        print(f"Database connection error: {e}")
        return None


def init_db():
    """初始化数据库表"""
    conn = get_db_connection()
    if not conn:
        print("No database connection, skipping init")
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS user_configs (
                    user_id TEXT PRIMARY KEY,
                    config JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        conn.commit()
        print("Database initialized successfully")
        return True
    except Exception as e:
        print(f"Database init error: {e}")
        return False
    finally:
        conn.close()


def load_user_config_from_db(user_id: str) -> Optional[Dict[str, Any]]:
    """从数据库加载用户配置"""
    if not user_id:
        return None
    
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT config FROM user_configs WHERE user_id = %s",
                (user_id,)
            )
            row = cur.fetchone()
            if row:
                return row['config'] if isinstance(row['config'], dict) else json.loads(row['config'])
        return None
    except Exception as e:
        print(f"Load config error: {e}")
        return None
    finally:
        conn.close()


def save_user_config_to_db(user_id: str, config: Dict[str, Any]) -> bool:
    """保存用户配置到数据库"""
    if not user_id:
        print("DB save: no user_id provided")
        return False
    
    conn = get_db_connection()
    if not conn:
        print("DB save: no connection available")
        return False
    
    try:
        config_json = json.dumps(config, ensure_ascii=False)
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO user_configs (user_id, config, updated_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) 
                DO UPDATE SET config = %s, updated_at = CURRENT_TIMESTAMP
            ''', (user_id, config_json, config_json))
        conn.commit()
        # 验证保存是否成功
        poe_key = config.get('poe_api_key', '')
        print(f"DB save success: user={user_id}, poe_key={'已配置' if poe_key else '未配置'}, config_size={len(config_json)}")
        return True
    except Exception as e:
        print(f"DB save error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()


def is_db_available() -> bool:
    """检查数据库是否可用"""
    return DATABASE_URL is not None and get_db_connection() is not None
