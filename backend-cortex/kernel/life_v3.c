/*
 * LifeOS v3.1 - C Kernel
 * 
 * 設計理念：
 * - Append-Only: 只能追加，不能修改
 * - Immutable: 歷史不可篡改
 * - Fixed-Size: 固定大小結構，可預測性能
 * - Time-Invariant: content_hash 永恆不變
 * 
 * 這是「數位原版」，Supabase 只是「工作副本」
 */

#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <stdlib.h>

// ============================================================================
// Type Definitions
// ============================================================================

#define TYPE_TEXT     0x01
#define TYPE_AUDIO    0x02
#define TYPE_VIDEO    0x04
#define TYPE_IMAGE    0x08
#define TYPE_VR       0x10
#define TYPE_LOCATION 0x20
#define TYPE_BIOMETRIC 0x40

#define ATTR_LOCKED   0x80
#define ATTR_ENCRYPTED 0x40
#define ATTR_SHARED   0x20
#define ATTR_ARCHIVED 0x10

// ============================================================================
// Core Structures
// ============================================================================

// 媒體參考結構 (64 bytes)
typedef struct {
    uint8_t  content_hash[16];    // UUID (永恆的鑰匙)
    uint8_t  media_type;          // 類型
    uint8_t  storage_class;       // 儲存位置
    uint16_t duration_sec;        // 長度（秒）
    uint32_t file_size_kb;        // 檔案大小
    uint64_t timestamp;           // 時間戳
    char     storage_path[16];    // 儲存路徑
    uint32_t compression_ratio;   // 壓縮率 (1000 = 1.0x)
    uint16_t width;               // 寬度
    uint16_t height;              // 高度
    uint32_t next_media_ptr;      // 下一個媒體（偏移量）
    uint32_t prev_media_ptr;      // 上一個媒體（偏移量）
} MediaRef;

// 日記標記結構 (32 bytes)
typedef struct {
    uint32_t text_offset;         // 文字在 content track 的位置
    uint32_t text_len;            // 文字長度
    uint64_t created_at;          // 創建時間（Unix timestamp）
    uint8_t  mood;                // 心情 (0-10)
    uint8_t  focus;               // 專注度 (0-10)
    uint8_t  energy;              // 能量 (0-10)
    uint8_t  flags;               // 類型標記
    uint32_t word_count;          // 字數
    uint32_t media_head_ptr;      // 第一個媒體（偏移量）
    uint32_t media_count;         // 媒體數量
    uint32_t date_yyyymmdd;       // 日期 (YYYYMMDD)
} DiaryMarker;

// ============================================================================
// Core Functions
// ============================================================================

/**
 * 寫入日記條目（Append-Only）
 * 
 * @param idx_path 索引檔案路徑
 * @param txt_path 文字檔案路徑
 * @param day_offset 天數偏移（從 2026-01-01 開始）
 * @param text 文字內容
 * @param mood 心情 (0-10)
 * @param focus 專注度 (0-10)
 * @param energy 能量 (0-10)
 * @return 1=成功, 0=已存在（不可變）, -1=錯誤
 */
int log_entry(
    const char* idx_path, 
    const char* txt_path, 
    uint32_t day_offset, 
    const char* text, 
    uint8_t mood,
    uint8_t focus,
    uint8_t energy
) {
    // 1. 寫入文字內容（Append）
    FILE *ft = fopen(txt_path, "ab");
    if (!ft) {
        perror("Failed to open text file");
        return -1;
    }
    
    fseek(ft, 0, SEEK_END);
    uint32_t offset = ftell(ft);
    
    size_t text_len = strlen(text);
    fwrite(text, 1, text_len, ft);
    fclose(ft);
    
    // 2. 檢查索引是否已存在（Immutability Check）
    FILE *fi = fopen(idx_path, "rb+");
    if (!fi) {
        // 檔案不存在，創建新檔案
        fi = fopen(idx_path, "wb+");
        if (!fi) {
            perror("Failed to create index file");
            return -1;
        }
    }
    
    // 檢查該天是否已有記錄
    DiaryMarker existing;
    fseek(fi, day_offset * sizeof(DiaryMarker), SEEK_SET);
    size_t read_count = fread(&existing, sizeof(DiaryMarker), 1, fi);
    
    if (read_count == 1 && existing.text_len > 0) {
        // 已存在記錄，拒絕覆蓋（Immutable）
        fclose(fi);
        fprintf(stderr, "⚠️ Kernel Warning: Day %u is locked. Immutable.\n", day_offset);
        return 0;
    }
    
    // 3. 寫入索引
    DiaryMarker marker = {
        .text_offset = offset,
        .text_len = (uint32_t)text_len,
        .created_at = (uint64_t)time(NULL),
        .mood = mood,
        .focus = focus,
        .energy = energy,
        .flags = TYPE_TEXT,
        .word_count = 0,  // TODO: 計算字數
        .media_head_ptr = 0,
        .media_count = 0,
        .date_yyyymmdd = 0  // TODO: 從 day_offset 計算
    };
    
    fseek(fi, day_offset * sizeof(DiaryMarker), SEEK_SET);
    fwrite(&marker, sizeof(DiaryMarker), 1, fi);
    fclose(fi);
    
    printf("✅ Kernel: Day %u locked successfully.\n", day_offset);
    return 1;
}

/**
 * 讀取日記條目
 * 
 * @param idx_path 索引檔案路徑
 * @param txt_path 文字檔案路徑
 * @param day_offset 天數偏移
 * @param marker 輸出：日記標記
 * @param text 輸出：文字內容（需預先分配記憶體）
 * @param max_len 文字緩衝區最大長度
 * @return 1=成功, 0=不存在, -1=錯誤
 */
int read_entry(
    const char* idx_path,
    const char* txt_path,
    uint32_t day_offset,
    DiaryMarker* marker,
    char* text,
    size_t max_len
) {
    // 1. 讀取索引
    FILE *fi = fopen(idx_path, "rb");
    if (!fi) {
        perror("Failed to open index file");
        return -1;
    }
    
    fseek(fi, day_offset * sizeof(DiaryMarker), SEEK_SET);
    size_t read_count = fread(marker, sizeof(DiaryMarker), 1, fi);
    fclose(fi);
    
    if (read_count != 1 || marker->text_len == 0) {
        // 該天沒有記錄
        return 0;
    }
    
    // 2. 讀取文字內容
    FILE *ft = fopen(txt_path, "rb");
    if (!ft) {
        perror("Failed to open text file");
        return -1;
    }
    
    fseek(ft, marker->text_offset, SEEK_SET);
    size_t to_read = marker->text_len < max_len - 1 ? marker->text_len : max_len - 1;
    fread(text, 1, to_read, ft);
    text[to_read] = '\0';  // Null-terminate
    fclose(ft);
    
    return 1;
}

/**
 * 添加媒體參考（Append-Only）
 * 
 * @param media_path 媒體索引檔案路徑
 * @param media 媒體參考結構
 * @return 媒體在檔案中的偏移量（用於鏈結串列）
 */
uint32_t add_media(const char* media_path, const MediaRef* media) {
    FILE *fm = fopen(media_path, "ab");
    if (!fm) {
        perror("Failed to open media file");
        return 0;
    }
    
    fseek(fm, 0, SEEK_END);
    uint32_t offset = ftell(fm);
    
    fwrite(media, sizeof(MediaRef), 1, fm);
    fclose(fm);
    
    printf("✅ Media added at offset %u\n", offset);
    return offset;
}

/**
 * 讀取媒體參考
 * 
 * @param media_path 媒體索引檔案路徑
 * @param offset 偏移量
 * @param media 輸出：媒體參考結構
 * @return 1=成功, 0=失敗
 */
int read_media(const char* media_path, uint32_t offset, MediaRef* media) {
    FILE *fm = fopen(media_path, "rb");
    if (!fm) {
        perror("Failed to open media file");
        return 0;
    }
    
    fseek(fm, offset, SEEK_SET);
    size_t read_count = fread(media, sizeof(MediaRef), 1, fm);
    fclose(fm);
    
    return read_count == 1 ? 1 : 0;
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * 計算天數偏移（從 2026-01-01 開始）
 */
uint32_t calculate_day_offset(int year, int month, int day) {
    struct tm start = {0};
    start.tm_year = 2026 - 1900;
    start.tm_mon = 0;  // January
    start.tm_mday = 1;
    
    struct tm target = {0};
    target.tm_year = year - 1900;
    target.tm_mon = month - 1;
    target.tm_mday = day;
    
    time_t start_time = mktime(&start);
    time_t target_time = mktime(&target);
    
    double diff_seconds = difftime(target_time, start_time);
    return (uint32_t)(diff_seconds / 86400);  // 86400 seconds per day
}

/**
 * 驗證檔案完整性（檢查是否被篡改）
 */
int verify_integrity(const char* idx_path) {
    FILE *fi = fopen(idx_path, "rb");
    if (!fi) {
        return -1;
    }
    
    // TODO: 實現 checksum 驗證
    // 可以使用 SHA-256 或 CRC32
    
    fclose(fi);
    return 1;
}

// ============================================================================
// Test Main (for development)
// ============================================================================

#ifdef TEST_MODE
int main() {
    const char* idx_path = "storage/life.index";
    const char* txt_path = "storage/life.text";
    
    // 測試寫入
    uint32_t day = calculate_day_offset(2026, 2, 10);
    int result = log_entry(
        idx_path, 
        txt_path, 
        day, 
        "今天完成了 C Kernel 的實現，這是數位原版！",
        8,  // mood
        9,  // focus
        7   // energy
    );
    
    printf("Write result: %d\n", result);
    
    // 測試讀取
    DiaryMarker marker;
    char text[1024];
    result = read_entry(idx_path, txt_path, day, &marker, text, sizeof(text));
    
    if (result == 1) {
        printf("Read success:\n");
        printf("  Mood: %d\n", marker.mood);
        printf("  Focus: %d\n", marker.focus);
        printf("  Energy: %d\n", marker.energy);
        printf("  Text: %s\n", text);
    }
    
    // 測試不可變性
    printf("\nTesting immutability...\n");
    result = log_entry(idx_path, txt_path, day, "嘗試修改", 5, 5, 5);
    printf("Second write result: %d (should be 0)\n", result);
    
    return 0;
}
#endif
