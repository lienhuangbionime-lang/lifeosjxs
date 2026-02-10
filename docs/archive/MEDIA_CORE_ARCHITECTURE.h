/**
 * LifeOS Media Core - Nomad List Style Data Architecture
 * 
 * Philosophy:
 * - Minimal & Predictable: Fixed-size structures for performance
 * - Time-Invariant: Content hash as eternal identifier
 * - Future-Proof: Reserved bits for VR/AR/Spatial computing
 * - Global-Ready: Multi-storage class support (local/cloud/IPFS)
 * 
 * Inspired by: Nomad List's data-driven minimalism
 * Version: 3.1.0
 */

// ============================================================================
// Type Definitions - What makes this day special?
// ============================================================================

// Media Type Flags (Bitwise OR for combinations)
#define TYPE_TEXT     0x01  // Plain text/markdown
#define TYPE_AUDIO    0x02  // Voice recording
#define TYPE_VIDEO    0x04  // Video capture
#define TYPE_IMAGE    0x08  // Photo/screenshot
#define TYPE_VR       0x10  // VR/AR/Spatial (future)
#define TYPE_LOCATION 0x20  // GPS coordinates (Nomad List style)
#define TYPE_BIOMETRIC 0x40 // Health data (Apple Health, etc.)

// Attribute Flags
#define ATTR_LOCKED   0x80  // Protected from deletion
#define ATTR_ENCRYPTED 0x40 // End-to-end encrypted
#define ATTR_SHARED   0x20  // Shared with others
#define ATTR_ARCHIVED 0x10  // Moved to cold storage

// Storage Class (Where is the data?)
typedef enum {
    STORAGE_LOCAL = 0,      // Device storage
    STORAGE_S3 = 1,         // AWS S3 / Cloud
    STORAGE_IPFS = 2,       // Decentralized (IPFS/Filecoin)
    STORAGE_COLD = 3,       // Glacier / Long-term archive
    STORAGE_EDGE = 4,       // Edge CDN (Cloudflare R2)
    STORAGE_P2P = 5,        // Peer-to-peer sync (Syncthing)
} StorageClass;

// ============================================================================
// Media Reference - The Bridge Between Past & Future
// ============================================================================

/**
 * MediaRef: Fixed 64-byte structure (cache-line aligned)
 * 
 * Design Rationale:
 * - 64 bytes = 1 cache line on modern CPUs (optimal performance)
 * - Fixed size = predictable memory layout
 * - Linked list = unlimited media per day
 * - Content hash = eternal identifier (never changes)
 */
typedef struct MediaRef {
    // === Core Metadata (16 bytes) ===
    uint8_t  media_type;        // TYPE_* flags (bitwise OR)
    uint8_t  storage_class;     // StorageClass enum
    uint16_t duration_sec;      // Duration (0 for images)
    uint32_t file_size_kb;      // File size in KB
    uint64_t timestamp_unix;    // Creation timestamp (Unix epoch)
    
    // === Eternal Identifier (16 bytes) ===
    uint8_t  content_hash[16];  // UUID v4 or SHA-256 truncated
                                // This is the ETERNAL KEY - never changes
    
    // === Storage Location (16 bytes) ===
    char     storage_path[16];  // Relative path or S3 key prefix
                                // e.g., "2026/02/10/" or "s3://bucket/"
    
    // === Extended Metadata (8 bytes) ===
    uint32_t compression_ratio; // Compression ratio (1000 = 1.0x)
    uint16_t width;             // Image/video width (0 for audio)
    uint16_t height;            // Image/video height (0 for audio)
    
    // === Linked List (8 bytes) ===
    uint32_t next_media_ptr;    // Pointer to next MediaRef (0 = end)
    uint32_t prev_media_ptr;    // Pointer to previous (doubly-linked)
    
} MediaRef;  // Total: 64 bytes

// ============================================================================
// Diary Marker - The Core Entry Point
// ============================================================================

/**
 * DiaryMarker: Fixed 32-byte structure
 * 
 * Design Rationale:
 * - Minimal footprint for fast scanning
 * - Text content stored separately (content track)
 * - Media references stored in linked list
 * - Mood/flags for quick filtering
 */
typedef struct DiaryMarker {
    // === Text Content Reference (8 bytes) ===
    uint32_t text_offset;       // Offset in content track
    uint32_t text_len;          // Length in bytes
    
    // === Metrics (8 bytes) ===
    uint8_t  mood;              // 0-10 scale
    uint8_t  focus;             // 0-10 scale
    uint8_t  energy;            // 0-10 scale
    uint8_t  flags;             // TYPE_* flags (what's in this day?)
    uint32_t word_count;        // Text word count
    
    // === Media References (8 bytes) ===
    uint32_t media_head_ptr;    // First MediaRef (0 = no media)
    uint32_t media_count;       // Total media items
    
    // === Temporal Context (8 bytes) ===
    uint32_t date_yyyymmdd;     // e.g., 20260210
    uint32_t timezone_offset;   // Seconds from UTC (Nomad List style)
    
} DiaryMarker;  // Total: 32 bytes

// ============================================================================
// Nomad List Style Extensions
// ============================================================================

/**
 * LocationRef: GPS coordinates for digital nomads
 * Inspired by Nomad List's location tracking
 */
typedef struct LocationRef {
    float    latitude;          // -90 to 90
    float    longitude;         // -180 to 180
    uint16_t altitude_m;        // Altitude in meters
    uint8_t  accuracy_m;        // GPS accuracy
    uint8_t  location_type;     // 0=home, 1=work, 2=travel, 3=cafe
    char     city_code[8];      // e.g., "TPE", "NYC", "TYO"
    char     country_code[4];   // ISO 3166-1 alpha-3
    uint32_t place_id;          // Google Places ID or custom
} LocationRef;  // Total: 32 bytes

/**
 * BiometricRef: Health data integration
 * For Apple Health, Fitbit, Oura Ring, etc.
 */
typedef struct BiometricRef {
    uint16_t heart_rate_avg;    // Average BPM
    uint16_t heart_rate_max;    // Max BPM
    uint16_t steps;             // Daily steps
    uint16_t calories;          // Calories burned
    uint8_t  sleep_hours;       // Hours of sleep
    uint8_t  sleep_quality;     // 0-10 scale
    uint16_t hrv_ms;            // Heart rate variability
    uint8_t  stress_level;      // 0-10 scale
    uint8_t  reserved[5];       // Future use
} BiometricRef;  // Total: 20 bytes

// ============================================================================
// API Interface (TypeScript/Python Bridge)
// ============================================================================

/**
 * JSON representation for API communication
 * This is what the frontend/backend exchange
 */
/*
{
  "date": "2026-02-10",
  "text": "Today I worked on LifeOS...",
  "metrics": {
    "mood": 8,
    "focus": 9,
    "energy": 7
  },
  "media": [
    {
      "type": "audio",
      "storage": "s3",
      "duration": 120,
      "size_kb": 1024,
      "hash": "550e8400-e29b-41d4-a716-446655440000",
      "url": "s3://lifeos/2026/02/10/audio_001.m4a"
    },
    {
      "type": "video",
      "storage": "local",
      "duration": 300,
      "size_kb": 15360,
      "hash": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "url": "file:///media/2026/02/10/video_001.mp4",
      "width": 1920,
      "height": 1080
    }
  ],
  "location": {
    "city": "Taipei",
    "country": "Taiwan",
    "lat": 25.0330,
    "lng": 121.5654
  },
  "biometrics": {
    "steps": 8432,
    "sleep_hours": 7.5,
    "hrv": 65
  }
}
*/

// ============================================================================
// Performance Characteristics
// ============================================================================

/*
Memory Layout:
- DiaryMarker: 32 bytes × 365 days = 11.7 KB/year
- MediaRef: 64 bytes × 10 media/day × 365 = 234 KB/year
- Total metadata: ~250 KB/year (extremely efficient!)

Cache Efficiency:
- DiaryMarker fits in 1 cache line (64 bytes)
- MediaRef fits in 1 cache line (64 bytes)
- Sequential scanning is cache-friendly

Scalability:
- 10 years of data = 2.5 MB metadata
- Can fit entirely in L3 cache on modern CPUs
- Sub-millisecond query performance
*/

// ============================================================================
// Implementation Notes
// ============================================================================

/*
1. Content Hash Generation:
   - Use UUID v4 for simplicity
   - Or SHA-256 truncated to 128 bits for content-addressing
   - Store in big-endian for cross-platform compatibility

2. Storage Path Convention:
   - Local: "YYYY/MM/DD/type_NNN.ext"
   - S3: "s3://bucket/user_id/YYYY/MM/DD/hash.ext"
   - IPFS: "ipfs://QmXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

3. Linked List Management:
   - Use memory pool for MediaRef allocation
   - Free list for deleted items
   - Defragmentation on background thread

4. Nomad List Integration:
   - Sync location data from Google Timeline
   - Import biometrics from Apple Health API
   - Export to Nomad List format for sharing
*/

// ============================================================================
// Future Extensions
// ============================================================================

/*
Planned Features:
1. VR/AR Support:
   - Spatial audio metadata
   - 360° video support
   - Apple Vision Pro integration

2. AI Integration:
   - Embedding vectors (512-dim) stored separately
   - Semantic search via vector DB
   - Auto-tagging from content

3. Blockchain:
   - Store content_hash on blockchain for proof-of-existence
   - NFT minting for special memories
   - Decentralized backup via Filecoin

4. Social:
   - Shared memories with friends
   - Public/private visibility control
   - Nomad List style "life map"
*/

#endif // LIFEOS_MEDIA_CORE_H
