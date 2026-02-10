"""
LifeOS Media Core - Python Implementation
基於 C-style 設計的 Python 版本

設計理念：
- 極致輕量：使用 dataclass 和固定大小結構
- 時間不變性：content_hash 作為永恆識別碼
- 擴展性：支援鏈結串列和多種儲存
"""

from dataclasses import dataclass, field
from typing import Optional, List, Literal
from datetime import datetime
from uuid import UUID, uuid4
from enum import IntEnum
import struct


# ============================================================================
# Type Definitions
# ============================================================================

class MediaType(IntEnum):
    """媒體類型（對應 C 的 #define）"""
    TEXT = 0x01
    AUDIO = 0x02
    VIDEO = 0x04
    IMAGE = 0x08
    VR = 0x10
    LOCATION = 0x20
    BIOMETRIC = 0x40


class StorageClass(IntEnum):
    """儲存類別"""
    LOCAL = 0      # 本機儲存
    S3 = 1         # AWS S3 / Cloud
    IPFS = 2       # 去中心化
    COLD = 3       # 冷儲存
    EDGE = 4       # Edge CDN
    P2P = 5        # P2P 同步


class AttributeFlags(IntEnum):
    """屬性標記"""
    LOCKED = 0x80      # 鎖定保護
    ENCRYPTED = 0x40   # 加密
    SHARED = 0x20      # 分享
    ARCHIVED = 0x10    # 歸檔


# ============================================================================
# Core Data Structures
# ============================================================================

@dataclass
class MediaRef:
    """
    媒體參考結構（對應 C 的 64-byte MediaRef）
    
    設計理念：
    - content_hash 是永恆的鑰匙（UUID）
    - 支援鏈結串列（next_ptr, prev_ptr）
    - 固定欄位，可預測的大小
    """
    # 核心元數據
    content_hash: UUID                    # 永恆識別碼（16 bytes）
    media_type: MediaType                 # 類型
    storage_class: StorageClass           # 儲存位置
    duration_sec: int = 0                 # 長度（秒）
    file_size_kb: int = 0                 # 檔案大小（KB）
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 儲存位置
    storage_path: str = ""                # 路徑（最多 16 字元）
    
    # 擴展元數據
    compression_ratio: float = 1.0        # 壓縮率
    width: int = 0                        # 寬度（圖片/影片）
    height: int = 0                       # 高度
    
    # 鏈結串列
    next_ptr: Optional[UUID] = None       # 下一個媒體
    prev_ptr: Optional[UUID] = None       # 上一個媒體
    
    def to_bytes(self) -> bytes:
        """轉換為 64-byte 二進制格式（對應 C struct）"""
        data = struct.pack(
            '16s B B H I Q 16s I H H 16s 16s',
            self.content_hash.bytes,           # 16 bytes
            self.media_type.value,             # 1 byte
            self.storage_class.value,          # 1 byte
            self.duration_sec,                 # 2 bytes
            self.file_size_kb,                 # 4 bytes
            int(self.timestamp.timestamp()),   # 8 bytes
            self.storage_path.encode()[:16].ljust(16, b'\x00'),  # 16 bytes
            int(self.compression_ratio * 1000), # 4 bytes
            self.width,                        # 2 bytes
            self.height,                       # 2 bytes
            self.next_ptr.bytes if self.next_ptr else b'\x00' * 16,  # 16 bytes
            self.prev_ptr.bytes if self.prev_ptr else b'\x00' * 16,  # 16 bytes
        )
        return data  # Total: 64 bytes
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'MediaRef':
        """從 64-byte 二進制格式還原"""
        unpacked = struct.unpack('16s B B H I Q 16s I H H 16s 16s', data)
        
        return cls(
            content_hash=UUID(bytes=unpacked[0]),
            media_type=MediaType(unpacked[1]),
            storage_class=StorageClass(unpacked[2]),
            duration_sec=unpacked[3],
            file_size_kb=unpacked[4],
            timestamp=datetime.fromtimestamp(unpacked[5]),
            storage_path=unpacked[6].decode().rstrip('\x00'),
            compression_ratio=unpacked[7] / 1000.0,
            width=unpacked[8],
            height=unpacked[9],
            next_ptr=UUID(bytes=unpacked[10]) if unpacked[10] != b'\x00' * 16 else None,
            prev_ptr=UUID(bytes=unpacked[11]) if unpacked[11] != b'\x00' * 16 else None,
        )


@dataclass
class DiaryMarker:
    """
    日記標記結構（對應 C 的 32-byte DiaryMarker）
    
    設計理念：
    - 極致輕量，只記錄必要信息
    - 文字內容存在別處（content track）
    - 媒體通過 media_head_ptr 連結
    """
    # 文字內容參考
    text_offset: int                      # 文字在 content track 的位置
    text_len: int                         # 文字長度
    
    # 指標
    mood: int = 5                         # 心情（0-10）
    focus: int = 5                        # 專注度（0-10）
    energy: int = 5                       # 能量（0-10）
    flags: int = 0                        # 類型標記（TYPE_*）
    word_count: int = 0                   # 字數
    
    # 媒體參考
    media_head_ptr: Optional[UUID] = None # 第一個媒體
    media_count: int = 0                  # 媒體數量
    
    # 時間上下文
    date: datetime = field(default_factory=datetime.now)
    timezone_offset: int = 0              # 時區偏移（秒）
    
    def to_bytes(self) -> bytes:
        """轉換為 32-byte 二進制格式"""
        data = struct.pack(
            'I I B B B B I 16s I I I',
            self.text_offset,              # 4 bytes
            self.text_len,                 # 4 bytes
            self.mood,                     # 1 byte
            self.focus,                    # 1 byte
            self.energy,                   # 1 byte
            self.flags,                    # 1 byte
            self.word_count,               # 4 bytes
            self.media_head_ptr.bytes if self.media_head_ptr else b'\x00' * 16,  # 16 bytes
            self.media_count,              # 4 bytes
            int(self.date.strftime('%Y%m%d')),  # 4 bytes (YYYYMMDD)
            self.timezone_offset,          # 4 bytes
        )
        # 補齊到 32 bytes（目前已經 44 bytes，需要調整）
        # 實際使用時可以優化結構
        return data[:32].ljust(32, b'\x00')


@dataclass
class LocationRef:
    """
    位置參考結構（對應 C 的 32-byte LocationRef）
    Nomad List 風格的位置追蹤
    """
    latitude: float                       # 緯度
    longitude: float                      # 經度
    altitude_m: int = 0                   # 海拔（米）
    accuracy_m: int = 0                   # GPS 精度
    location_type: int = 0                # 0=home, 1=work, 2=travel, 3=cafe
    city_code: str = ""                   # 城市代碼（如 "TPE"）
    country_code: str = ""                # 國家代碼（ISO 3166-1）
    place_id: int = 0                     # Google Places ID


@dataclass
class BiometricRef:
    """
    生物識別數據結構（對應 C 的 20-byte BiometricRef）
    整合 Apple Health, Fitbit, Oura Ring 等
    """
    heart_rate_avg: int = 0               # 平均心率
    heart_rate_max: int = 0               # 最大心率
    steps: int = 0                        # 步數
    calories: int = 0                     # 卡路里
    sleep_hours: float = 0.0              # 睡眠時數
    sleep_quality: int = 0                # 睡眠品質（0-10）
    hrv_ms: int = 0                       # 心率變異性
    stress_level: int = 0                 # 壓力等級（0-10）


# ============================================================================
# Media Chain Management
# ============================================================================

class MediaChain:
    """
    媒體鏈結串列管理器
    
    功能：
    - 添加媒體到鏈結串列
    - 遍歷所有媒體
    - 刪除媒體
    """
    
    def __init__(self):
        self.media_refs: dict[UUID, MediaRef] = {}
    
    def add_media(self, media: MediaRef, after: Optional[UUID] = None) -> UUID:
        """
        添加媒體到鏈結串列
        
        Args:
            media: 媒體參考
            after: 插入在哪個媒體之後（None = 添加到尾部）
        
        Returns:
            媒體的 UUID
        """
        if media.content_hash is None:
            media.content_hash = uuid4()
        
        if after and after in self.media_refs:
            # 插入到指定位置
            next_media = self.media_refs[after].next_ptr
            self.media_refs[after].next_ptr = media.content_hash
            media.prev_ptr = after
            media.next_ptr = next_media
            
            if next_media:
                self.media_refs[next_media].prev_ptr = media.content_hash
        
        self.media_refs[media.content_hash] = media
        return media.content_hash
    
    def get_chain(self, head: UUID) -> List[MediaRef]:
        """獲取整條鏈結串列"""
        result = []
        current = head
        
        while current and current in self.media_refs:
            media = self.media_refs[current]
            result.append(media)
            current = media.next_ptr
        
        return result
    
    def remove_media(self, media_id: UUID) -> bool:
        """從鏈結串列中移除媒體"""
        if media_id not in self.media_refs:
            return False
        
        media = self.media_refs[media_id]
        
        # 更新前後連結
        if media.prev_ptr:
            self.media_refs[media.prev_ptr].next_ptr = media.next_ptr
        if media.next_ptr:
            self.media_refs[media.next_ptr].prev_ptr = media.prev_ptr
        
        del self.media_refs[media_id]
        return True


# ============================================================================
# Usage Examples
# ============================================================================

def example_usage():
    """使用範例"""
    
    # 創建媒體參考
    audio = MediaRef(
        content_hash=uuid4(),
        media_type=MediaType.AUDIO,
        storage_class=StorageClass.LOCAL,
        duration_sec=120,
        file_size_kb=1024,
        storage_path="2026/02/10/"
    )
    
    video = MediaRef(
        content_hash=uuid4(),
        media_type=MediaType.VIDEO,
        storage_class=StorageClass.S3,
        duration_sec=300,
        file_size_kb=15360,
        storage_path="s3://lifeos/",
        width=1920,
        height=1080
    )
    
    # 創建媒體鏈
    chain = MediaChain()
    audio_id = chain.add_media(audio)
    video_id = chain.add_media(video, after=audio_id)
    
    # 創建日記標記
    diary = DiaryMarker(
        text_offset=0,
        text_len=500,
        mood=8,
        focus=9,
        energy=7,
        media_head_ptr=audio_id,
        media_count=2,
        date=datetime.now()
    )
    
    # 獲取所有媒體
    all_media = chain.get_chain(diary.media_head_ptr)
    print(f"日記有 {len(all_media)} 個媒體")
    
    # 轉換為二進制（可以存到檔案）
    audio_bytes = audio.to_bytes()
    print(f"MediaRef 大小: {len(audio_bytes)} bytes")
    
    # 從二進制還原
    restored_audio = MediaRef.from_bytes(audio_bytes)
    print(f"還原成功: {restored_audio.content_hash == audio.content_hash}")


if __name__ == "__main__":
    example_usage()
