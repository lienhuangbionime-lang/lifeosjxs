
import os
import subprocess
import sys

# --- CORTEX KERNEL SOURCE CODE (Embedded) ---
# 這就是 LifeOS v3.3 的完整原始碼 (含 Header, Base Year, Append Logic)
C_SOURCE_CODE = r"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

// --- CONFIGURATION ---
#define INDEX_FILE "backend-cortex/kernel/storage/life.index"
#define TEXT_FILE  "backend-cortex/kernel/storage/life.text"

// --- HEADER STRUCTURE ---
typedef struct {
    char     magic[4];     // "LIFE"
    uint32_t version;      // 3
    uint32_t base_year;    // Genesis Year
    uint32_t reserved[4];  
} LifeHeader;

// --- DATA STRUCTURE ---
typedef struct {
    uint32_t text_offset;
    uint32_t text_len;
    uint8_t  mood;
    uint8_t  flags;
    uint32_t media_head_ptr;
    uint8_t  padding[16];
} DiaryMarker;

int is_leap(int year) {
    return (year % 4 == 0 && year % 100 != 0) || (year % 400 == 0);
}

int days_in_month(int year, int month) {
    int days[] = {0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
    if (is_leap(year) && month == 2) return 29;
    return days[month];
}

long calculate_offset(int base_year, int year, int month, int day) {
    if (year < base_year) return -1;
    long total_days = 0;
    for (int y = base_year; y < year; y++) total_days += is_leap(y) ? 366 : 365;
    for (int m = 1; m < month; m++) total_days += days_in_month(year, m);
    total_days += (day - 1);
    return total_days;
}

int get_or_create_header(FILE *fi, LifeHeader *header, int current_write_year) {
    fseek(fi, 0, SEEK_END);
    if (ftell(fi) == 0) {
        int genesis_year = current_write_year;
        printf("✨ Cortex: Initializing User Timeline (Genesis: %d).\n", genesis_year);
        memset(header, 0, sizeof(LifeHeader));
        memcpy(header->magic, "LIFE", 4);
        header->version = 3;
        header->base_year = genesis_year; 
        fseek(fi, 0, SEEK_SET);
        fwrite(header, sizeof(LifeHeader), 1, fi);
        return 1;
    } else {
        fseek(fi, 0, SEEK_SET);
        if (fread(header, sizeof(LifeHeader), 1, fi) != 1) return 0;
        if (strncmp(header->magic, "LIFE", 4) != 0) return 0;
        return 1;
    }
}

int write_entry(int year, int month, int day, char* content, int mood, int flags) {
    // Ensure directories exist handled by Python wrapper but good to be safe
    // In C, standard library doesn't easily create dirs recursively without OS specific calls.
    // Assuming Python wrapper created them.

    FILE *fi = fopen(INDEX_FILE, "r+b");
    if (!fi) { fi = fopen(INDEX_FILE, "wb"); fclose(fi); fi = fopen(INDEX_FILE, "r+b"); }
    
    LifeHeader header;
    if (!get_or_create_header(fi, &header, year)) { fclose(fi); return 0; }
    if (year < header.base_year) { fclose(fi); return 0; }

    long day_idx = calculate_offset(header.base_year, year, month, day);
    long idx_offset = sizeof(LifeHeader) + (day_idx * sizeof(DiaryMarker));

    fseek(fi, 0, SEEK_END);
    while (ftell(fi) < idx_offset) {
        DiaryMarker empty = {0};
        fwrite(&empty, sizeof(DiaryMarker), 1, fi);
    }

    FILE *ft = fopen(TEXT_FILE, "r+b");
    if (!ft) { ft = fopen(TEXT_FILE, "wb"); fclose(ft); ft = fopen(TEXT_FILE, "r+b"); }
    
    fseek(ft, 0, SEEK_END);
    uint32_t new_pos = (uint32_t)ftell(ft);
    uint32_t len = (uint32_t)strlen(content);
    
    fwrite(content, 1, len, ft);
    fwrite("\n", 1, 1, ft); 
    fclose(ft);

    DiaryMarker marker = {0};
    marker.text_offset = new_pos;
    marker.text_len = len;
    marker.mood = mood;
    marker.flags = flags;

    fseek(fi, idx_offset, SEEK_SET);
    fwrite(&marker, sizeof(DiaryMarker), 1, fi);
    printf("✅ Secured: %d-%02d-%02d (Mood: %d, Flags: %d)\n", year, month, day, mood, flags);
    fclose(fi);
    return 1;
}

void read_entry(int year, int month, int day) {
    FILE *fi = fopen(INDEX_FILE, "rb");
    if (!fi) return;
    LifeHeader header;
    if (fread(&header, sizeof(LifeHeader), 1, fi) != 1) return;
    if (year < header.base_year) { fclose(fi); return; }

    long day_idx = calculate_offset(header.base_year, year, month, day);
    long idx_offset = sizeof(LifeHeader) + (day_idx * sizeof(DiaryMarker));

    fseek(fi, 0, SEEK_END);
    if (ftell(fi) <= idx_offset) { fclose(fi); return; }

    fseek(fi, idx_offset, SEEK_SET);
    DiaryMarker marker;
    fread(&marker, sizeof(DiaryMarker), 1, fi);
    fclose(fi);

    if (marker.text_len == 0) { printf("📭 No entry.\n"); return; }

    FILE *ft = fopen(TEXT_FILE, "rb");
    char *buffer = malloc(marker.text_len + 1);
    
    // Check for null or invalid read
    if (!buffer) return;
    
    fseek(ft, marker.text_offset, SEEK_SET);
    fread(buffer, 1, marker.text_len, ft);
    buffer[marker.text_len] = '\0';
    
    printf("📝 Content: %s\n", buffer);  // Simple output for python parser
    free(buffer);
    fclose(ft);
}

int main(int argc, char *argv[]) {
    if (argc < 2) return 1;
    if (strcmp(argv[1], "write") == 0) {
        write_entry(atoi(argv[2]), atoi(argv[3]), atoi(argv[4]), argv[5], (argc>6)?atoi(argv[6]):5, (argc>7)?atoi(argv[7]):1);
    } else if (strcmp(argv[1], "read") == 0) {
        read_entry(atoi(argv[2]), atoi(argv[3]), atoi(argv[4]));
    }
    return 0;
}
"""

def build_kernel():
    print("[Cortex Builder] Initializing...")

    # 1. 建立目錄
    dirs = ["bin", "backend-cortex/kernel_source", "backend-cortex/kernel/storage"]
    for d in dirs:
        if not os.path.exists(d):
            try:
                os.makedirs(d)
                print(f"Created directory: {d}")
            except OSError as e:
                print(f"Error creating directory {d}: {e}")

    # 2. 寫入原始碼
    source_path = "backend-cortex/kernel_source/life_v3.c"
    try:
        with open(source_path, "w", encoding="utf-8") as f:
            f.write(C_SOURCE_CODE)
        print(f"Source code written to: {source_path}")
    except Exception as e:
        print(f"Failed to write source code: {e}")
        return

    # 3. 編譯
    output_path = "bin/life_win64.exe"
    print("Compiling with GCC...")
    
    try:
        # -O2 優化編譯
        subprocess.run(["gcc", source_path, "-O2", "-o", output_path], check=True)
        print(f"SUCCESS: Binary created at {output_path}")
        print("You can now use 'kernel_driver.py' directly!")
    except FileNotFoundError:
        print("ERROR: 'gcc' not found. Please install MinGW or TDM-GCC.")
    except subprocess.CalledProcessError:
        print("ERROR: Compilation failed.")

if __name__ == "__main__":
    build_kernel()
