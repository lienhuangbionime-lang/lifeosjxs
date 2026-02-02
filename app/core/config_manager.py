import os
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.system import SystemConfig
import time

class ConfigManager:
    _instance = None
    _cache = {}
    _cache_ttl = 300  # 5分鐘快取

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance

    def get_value(self, key: str, default: str) -> str:
        current_time = time.time()
        
        # 1. 檢查快取
        if key in self._cache:
            val, timestamp = self._cache[key]
            if current_time - timestamp < self._cache_ttl:
                return val

        # 2. 讀取資料庫
        db: Session = SessionLocal()
        try:
            config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
            if config:
                self._cache[key] = (config.value, current_time)
                return config.value
        except Exception as e:
            print(f"Config DB Read Error: {e}")
        finally:
            db.close()

        # 3. 回退至環境變數或預設值
        return os.getenv(key, default)

    def set_value(self, key: str, value: str):
        db: Session = SessionLocal()
        try:
            config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
            if not config:
                config = SystemConfig(key=key, value=value)
                db.add(config)
            else:
                config.value = value
            
            db.commit()
            # 更新快取
            self._cache[key] = (value, time.time())
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

config_manager = ConfigManager()
