# Nomad List Style Dashboard - Design Spec
**極簡、數據驅動、全球視野**

---

## 🎯 設計哲學

### Nomad List 的核心特質
1. **數據密度高**：在有限空間展示最多有用信息
2. **視覺層次清晰**：重要數據突出，次要數據淡化
3. **全球化視角**：地圖、時區、位置優先
4. **極簡美學**：去除一切裝飾，只留本質

### 應用到 LifeOS
- **時間軸視圖**：橫向滾動的日記卡片
- **地圖視圖**：顯示記憶的地理分佈
- **統計面板**：緊湊的數據儀表板
- **媒體畫廊**：網格式多媒體展示

---

## 📊 核心組件設計

### 1. Timeline Card (時間軸卡片)

#### 視覺設計
```
┌─────────────────────────────────────┐
│ 📍 Taipei, Taiwan      🕐 14:30 UTC+8│
├─────────────────────────────────────┤
│                                      │
│ Today I worked on LifeOS Context    │
│ Engineering system...                │
│                                      │
│ 😊 8  🎯 9  ⚡ 7                    │
│                                      │
│ [🎤 2m] [📹 5m] [📷 3]              │
│                                      │
│ #coding #productivity #taipei        │
└─────────────────────────────────────┘
```

#### 數據結構映射
```typescript
interface TimelineCard {
  date: string;              // DiaryMarker.date_yyyymmdd
  location: {
    city: string;
    country: string;
    timezone: string;        // DiaryMarker.timezone_offset
  };
  text: string;              // From text_offset/text_len
  metrics: {
    mood: number;            // DiaryMarker.mood
    focus: number;           // DiaryMarker.focus
    energy: number;          // DiaryMarker.energy
  };
  media: MediaItem[];        // From media_head_ptr
  tags: string[];            // Extracted from text
}
```

### 2. Map View (地圖視圖)

#### 視覺設計
```
┌─────────────────────────────────────┐
│          🗺️ Life Map                │
├─────────────────────────────────────┤
│                                      │
│     [Interactive World Map]          │
│                                      │
│  📍 Markers:                         │
│  • Taipei (125 days)                 │
│  • Tokyo (45 days)                   │
│  • New York (30 days)                │
│                                      │
│  Heat map: Darker = More time        │
└─────────────────────────────────────┘
```

#### 數據來源
```typescript
interface LocationData {
  city: string;              // LocationRef.city_code
  country: string;           // LocationRef.country_code
  lat: number;               // LocationRef.latitude
  lng: number;               // LocationRef.longitude
  days_count: number;        // Aggregated
  entries: DiaryEntry[];     // All entries at this location
}
```

### 3. Stats Panel (統計面板)

#### 視覺設計
```
┌──────────────────────────────────────┐
│ 📊 2026 Stats                        │
├──────────────────────────────────────┤
│                                       │
│ 📝 365 entries    🎤 1,234 recordings│
│ 📹 456 videos     📷 2,345 photos    │
│                                       │
│ 🌍 12 cities      🛫 45 flights      │
│ 🏠 Taipei (125d)  🗾 Tokyo (45d)     │
│                                       │
│ 😊 Avg Mood: 7.8  🎯 Avg Focus: 8.2 │
│ ⚡ Avg Energy: 7.5 💤 Avg Sleep: 7.2h│
│                                       │
│ 🔥 Streak: 127 days                  │
└──────────────────────────────────────┘
```

#### 數據聚合
```typescript
interface YearStats {
  total_entries: number;
  media_counts: {
    audio: number;           // Count TYPE_AUDIO
    video: number;           // Count TYPE_VIDEO
    image: number;           // Count TYPE_IMAGE
  };
  locations: {
    cities: number;
    top_city: string;
    days_per_city: Map<string, number>;
  };
  metrics: {
    avg_mood: number;
    avg_focus: number;
    avg_energy: number;
    avg_sleep: number;       // From BiometricRef
  };
  streak: number;            // Consecutive days
}
```

### 4. Media Gallery (媒體畫廊)

#### 視覺設計
```
┌─────────────────────────────────────┐
│ 🎬 Media Gallery                    │
├─────────────────────────────────────┤
│                                      │
│ [📷] [📷] [📹] [🎤]                 │
│ [📹] [📷] [📷] [📷]                 │
│ [🎤] [📹] [📷] [📷]                 │
│                                      │
│ Filter: [All] [Photos] [Videos]     │
│         [Audio] [VR]                 │
│                                      │
│ Sort: [Date] [Type] [Size]           │
└─────────────────────────────────────┘
```

#### 數據查詢
```typescript
interface MediaGallery {
  items: MediaItem[];
  filters: {
    type: MediaType[];       // TYPE_* flags
    storage: StorageClass[]; // STORAGE_*
    date_range: [Date, Date];
  };
  sort: 'date' | 'type' | 'size';
}

interface MediaItem {
  hash: string;              // MediaRef.content_hash
  type: MediaType;           // MediaRef.media_type
  url: string;               // Constructed from storage_path
  thumbnail: string;         // Generated thumbnail URL
  duration: number;          // MediaRef.duration_sec
  size_kb: number;           // MediaRef.file_size_kb
  date: string;              // From parent DiaryMarker
}
```

---

## 🎨 視覺風格指南

### Color Palette (Nomad List Inspired)
```css
:root {
  /* Primary Colors */
  --nomad-blue: #3b82f6;      /* Links, accents */
  --nomad-green: #10b981;     /* Success, positive */
  --nomad-orange: #f59e0b;    /* Warning, attention */
  --nomad-red: #ef4444;       /* Error, negative */
  
  /* Neutral Colors */
  --nomad-gray-50: #f9fafb;   /* Background */
  --nomad-gray-100: #f3f4f6;  /* Card background */
  --nomad-gray-200: #e5e7eb;  /* Border */
  --nomad-gray-600: #4b5563;  /* Secondary text */
  --nomad-gray-900: #111827;  /* Primary text */
  
  /* Data Visualization */
  --mood-low: #ef4444;        /* Mood 0-3 */
  --mood-mid: #f59e0b;        /* Mood 4-7 */
  --mood-high: #10b981;       /* Mood 8-10 */
}
```

### Typography
```css
/* Nomad List uses system fonts for speed */
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", 
             Roboto, "Helvetica Neue", Arial, sans-serif;

/* Sizes */
--text-xs: 0.75rem;    /* 12px - Labels */
--text-sm: 0.875rem;   /* 14px - Body */
--text-base: 1rem;     /* 16px - Default */
--text-lg: 1.125rem;   /* 18px - Headings */
--text-xl: 1.25rem;    /* 20px - Large headings */
```

### Spacing (8px Grid)
```css
--space-1: 0.25rem;  /* 4px */
--space-2: 0.5rem;   /* 8px */
--space-3: 0.75rem;  /* 12px */
--space-4: 1rem;     /* 16px */
--space-6: 1.5rem;   /* 24px */
--space-8: 2rem;     /* 32px */
```

---

## 📱 組件實現

### TimelineCard Component
```tsx
interface TimelineCardProps {
  entry: DiaryEntry;
  onMediaClick: (media: MediaItem) => void;
}

export const TimelineCard = ({ entry, onMediaClick }: TimelineCardProps) => {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm hover:shadow-md transition-shadow">
      {/* Location & Time */}
      <div className="flex justify-between items-center mb-3 text-sm text-gray-600">
        <div className="flex items-center gap-2">
          <MapPin size={14} />
          <span>{entry.location.city}, {entry.location.country}</span>
        </div>
        <div className="flex items-center gap-2">
          <Clock size={14} />
          <span>{entry.time} {entry.location.timezone}</span>
        </div>
      </div>

      {/* Text Content */}
      <p className="text-gray-900 mb-3 leading-relaxed">
        {entry.text}
      </p>

      {/* Metrics */}
      <div className="flex gap-4 mb-3 text-sm">
        <div className="flex items-center gap-1">
          <span>😊</span>
          <span className="font-medium">{entry.metrics.mood}</span>
        </div>
        <div className="flex items-center gap-1">
          <span>🎯</span>
          <span className="font-medium">{entry.metrics.focus}</span>
        </div>
        <div className="flex items-center gap-1">
          <span>⚡</span>
          <span className="font-medium">{entry.metrics.energy}</span>
        </div>
      </div>

      {/* Media Pills */}
      {entry.media.length > 0 && (
        <div className="flex gap-2 mb-3">
          {entry.media.map(media => (
            <button
              key={media.hash}
              onClick={() => onMediaClick(media)}
              className="px-2 py-1 bg-gray-100 rounded text-xs text-gray-700 hover:bg-gray-200 transition-colors"
            >
              {getMediaIcon(media.type)} {formatDuration(media.duration)}
            </button>
          ))}
        </div>
      )}

      {/* Tags */}
      <div className="flex flex-wrap gap-2">
        {entry.tags.map(tag => (
          <span key={tag} className="text-xs text-blue-600">
            #{tag}
          </span>
        ))}
      </div>
    </div>
  );
};
```

### MapView Component
```tsx
import { MapContainer, TileLayer, Marker, Popup, HeatmapLayer } from 'react-leaflet';

interface MapViewProps {
  locations: LocationData[];
  onLocationClick: (location: LocationData) => void;
}

export const MapView = ({ locations, onLocationClick }: MapViewProps) => {
  return (
    <div className="w-full h-[600px] rounded-lg overflow-hidden border border-gray-200">
      <MapContainer
        center={[25.0330, 121.5654]} // Default to Taipei
        zoom={2}
        className="w-full h-full"
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap contributors'
        />
        
        {/* Markers */}
        {locations.map(loc => (
          <Marker
            key={loc.city}
            position={[loc.lat, loc.lng]}
            eventHandlers={{
              click: () => onLocationClick(loc)
            }}
          >
            <Popup>
              <div className="text-sm">
                <div className="font-bold">{loc.city}</div>
                <div className="text-gray-600">{loc.days_count} days</div>
              </div>
            </Popup>
          </Marker>
        ))}
        
        {/* Heatmap */}
        <HeatmapLayer
          points={locations.map(loc => ({
            lat: loc.lat,
            lng: loc.lng,
            intensity: loc.days_count
          }))}
          options={{
            radius: 25,
            blur: 15,
            maxZoom: 10
          }}
        />
      </MapContainer>
    </div>
  );
};
```

---

## 🔄 數據流程

### 從 C Struct 到 React Component

```
1. Backend (Python/FastAPI)
   ↓
   Read DiaryMarker from binary file
   ↓
   Follow media_head_ptr to load MediaRef chain
   ↓
   Construct JSON response
   
2. API Layer
   ↓
   GET /api/v1/timeline?month=2026-02
   ↓
   Return: { entries: [...] }
   
3. Frontend (React)
   ↓
   Fetch data from API
   ↓
   Transform to component props
   ↓
   Render TimelineCard components
```

### 性能優化

```typescript
// 虛擬滾動 (只渲染可見的卡片)
import { useVirtualizer } from '@tanstack/react-virtual';

const Timeline = ({ entries }: { entries: DiaryEntry[] }) => {
  const parentRef = useRef<HTMLDivElement>(null);
  
  const virtualizer = useVirtualizer({
    count: entries.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 200, // 估計卡片高度
    overscan: 5, // 預渲染 5 個卡片
  });

  return (
    <div ref={parentRef} className="h-screen overflow-auto">
      <div style={{ height: `${virtualizer.getTotalSize()}px` }}>
        {virtualizer.getVirtualItems().map(virtualRow => (
          <div
            key={virtualRow.index}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              transform: `translateY(${virtualRow.start}px)`,
            }}
          >
            <TimelineCard entry={entries[virtualRow.index]} />
          </div>
        ))}
      </div>
    </div>
  );
};
```

---

## 🎯 實現優先級

### Phase 1: MVP (2 週)
- ✅ TimelineCard 組件
- ✅ 基礎統計面板
- ✅ 媒體縮圖顯示

### Phase 2: 增強 (1 個月)
- ✅ 地圖視圖
- ✅ 虛擬滾動優化
- ✅ 媒體畫廊

### Phase 3: 進階 (2 個月)
- ✅ 生物識別數據可視化
- ✅ VR/AR 內容支持
- ✅ 社交分享功能

---

## 📚 參考資源

### Nomad List 設計分析
- 極簡的卡片設計
- 高密度的數據展示
- 清晰的視覺層次
- 全球化的視角

### 技術棧
- React + TypeScript
- Tailwind CSS
- Framer Motion (動畫)
- React Leaflet (地圖)
- Recharts (圖表)

---

**這就是 Nomad List 風格遇上 LifeOS 的結晶！** 🌍✨
