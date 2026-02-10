# LifeOS v3.1 - System Context
**Single Source of Truth for AI-Assisted Development**

> This document serves as the **complete context** for any AI coding assistant working on LifeOS.
> Read this FIRST before generating any code.

---

## 🎯 Project Mission
LifeOS is a **Second Brain Operating System** that enables symbiotic human-AI collaboration for life management, knowledge synthesis, and personal evolution.

**Core Philosophy**: Symbiosis > Automation. We build tools that augment human cognition, not replace it.

---

## 🏗️ Architecture Overview

### System Components
```
LifeOS v3.1
├── frontend-body/          # Next.js 14 (App Router)
│   ├── app/               # Pages & Layouts
│   ├── components/        # React Components
│   ├── lib/              # Utilities & API Clients
│   └── public/           # Static Assets
│
├── backend-cortex/        # FastAPI (Python 3.11+)
│   ├── main.py           # API Entry Point
│   ├── models/           # Pydantic Models
│   ├── routers/          # API Routes
│   └── services/         # Business Logic
│
└── database-hippocampus/  # Supabase (PostgreSQL)
    └── schema.sql        # Database Schema
```

### Data Flow
```
User Input → Frontend (Next.js) → API (FastAPI) → Database (Supabase)
                ↓
         Cortex AI (Gemini API)
                ↓
         Knowledge Graph (D3.js)
```

---

## 💻 Tech Stack

### Frontend
- **Framework**: Next.js 14 (App Router, TypeScript)
- **Styling**: Tailwind CSS (NO inline styles, NO CSS-in-JS)
- **UI Components**: Custom components (NO shadcn/ui, NO external UI libraries)
- **Animations**: Framer Motion
- **Charts**: Recharts
- **Icons**: Lucide React
- **State Management**: React Hooks (useState, useEffect, useMemo)

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Validation**: Pydantic v2
- **AI Integration**: Google Gemini API (gemini-2.0-flash-exp)
- **Async**: asyncio, httpx
- **CORS**: Enabled for localhost:3000

### Database
- **Primary**: Supabase (PostgreSQL)
- **ORM**: Direct SQL queries (NO SQLAlchemy)
- **Schema**: See `database-hippocampus/schema.sql`

### AI Models
- **Primary**: Gemini 2.0 Flash Experimental
- **Embedding**: text-embedding-004
- **Fallback**: Gemini 1.5 Pro

---

## 📐 Coding Standards

### TypeScript/React Rules

#### 1. Component Structure
```tsx
'use client'; // ALWAYS at the top for client components

import React, { useState, useEffect } from 'react';
import { Icon } from 'lucide-react';

interface ComponentProps {
  data: any[];
  onAction: (id: string) => void;
}

export const Component = ({ data, onAction }: ComponentProps) => {
  const [state, setState] = useState<Type>(initialValue);

  useEffect(() => {
    // Side effects
  }, [dependencies]);

  return (
    <div className="tailwind-classes">
      {/* Content */}
    </div>
  );
};
```

#### 2. Styling Rules
- **ALWAYS use Tailwind CSS classes**
- **NEVER use inline styles** (`style={{}}`)
- **NEVER use CSS-in-JS** (styled-components, emotion, etc.)
- **Use responsive classes**: `sm:`, `md:`, `lg:`
- **Use custom scrollbar class**: `custom-scrollbar`
- **Color palette**: Use defined colors in `globals.css`

#### 3. File Naming
- Components: `PascalCase.tsx` (e.g., `CardStackDashboard.tsx`)
- Utilities: `camelCase.ts` (e.g., `apiClient.ts`)
- Pages: `page.tsx` (Next.js App Router convention)

#### 4. Import Order
```tsx
// 1. React & Next.js
import React from 'react';
import { useRouter } from 'next/navigation';

// 2. External libraries
import { motion } from 'framer-motion';
import { Icon } from 'lucide-react';

// 3. Internal components
import { Component } from '@/components/Component';

// 4. Utilities & types
import { api } from '@/lib/api/client';
import type { DataType } from '@/types';
```

### Python/FastAPI Rules

#### 1. API Endpoint Structure
```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

router = APIRouter(prefix="/api/v1", tags=["category"])

class RequestModel(BaseModel):
    """Clear docstring explaining the model"""
    field: str = Field(..., description="Field description")
    optional_field: Optional[int] = None

@router.post("/endpoint")
async def endpoint_name(request: RequestModel) -> dict:
    """
    Clear docstring explaining what this endpoint does.
    
    Args:
        request: Description of request
        
    Returns:
        Description of response
    """
    try:
        # Implementation
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### 2. Pydantic Models
- **ALWAYS use Pydantic v2 syntax**
- **Use Field() for validation and documentation**
- **Use descriptive docstrings**
- **Use Optional[] for nullable fields**

#### 3. Async/Await
- **ALWAYS use async/await for I/O operations**
- **Use httpx for HTTP requests** (NOT requests)
- **Use asyncio for concurrent operations**

#### 4. Error Handling
```python
try:
    # Operation
    result = await operation()
except SpecificError as e:
    logger.error(f"Specific error: {e}")
    raise HTTPException(status_code=400, detail="User-friendly message")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

---

## 🗄️ Database Schema

### Core Tables

#### `memories` (Main log entries)
```sql
- id: UUID (Primary Key)
- user_id: UUID (Foreign Key)
- date: DATE (Index)
- content: TEXT (Markdown)
- markdown_body: TEXT (AI-processed)
- mood: INTEGER (1-10)
- focus: INTEGER (1-10)
- energy: INTEGER (1-10)
- habits: JSONB
- meta: JSONB
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

#### `projects` (Project management)
```sql
- id: UUID (Primary Key)
- user_id: UUID (Foreign Key)
- title: TEXT
- description: TEXT
- status: TEXT (active/archived/completed)
- meta: JSONB
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

#### `tasks` (Task management)
```sql
- id: UUID (Primary Key)
- project_id: UUID (Foreign Key)
- title: TEXT
- status: TEXT (todo/in_progress/done)
- priority: TEXT (low/medium/high)
- due_date: DATE
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

### Query Patterns
```python
# GOOD: Use parameterized queries
result = await supabase.table('memories').select('*').eq('user_id', user_id).execute()

# BAD: Never use string interpolation
result = await supabase.table('memories').select('*').eq('user_id', f'{user_id}').execute()
```

---

## 🎨 UI/UX Guidelines

### Design System

#### Colors (Neon Palette)
```typescript
NEON_PALETTE = {
  NEON_CYAN: '#00f3ff',
  NEON_PINK: '#ff006e',
  NEON_LIME: '#00ff9d',
  NEON_VIOLET: '#bc13fe',
  SLATE: '#64748b',
  primary: '#6366f1', // Indigo
}
```

#### Typography
- **Headings**: `font-black` or `font-bold`
- **Body**: `font-normal`
- **Code**: `font-mono`
- **Sizes**: Use Tailwind classes (`text-xs`, `text-sm`, `text-base`, etc.)

#### Spacing
- **Padding**: `p-4`, `p-6`, `p-8` (multiples of 4)
- **Margin**: `mb-4`, `mt-6`, `gap-3`
- **Rounded**: `rounded-xl`, `rounded-2xl`, `rounded-3xl`

#### Animations
```tsx
// Use Framer Motion for animations
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.3 }}
>
  {/* Content */}
</motion.div>
```

### Component Patterns

#### Modal/Overlay
```tsx
<AnimatePresence>
  {isOpen && (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
    >
      {/* Modal content */}
    </motion.div>
  )}
</AnimatePresence>
```

#### Card
```tsx
<div className="bg-slate-900/50 rounded-3xl p-6 border border-slate-800 backdrop-blur-sm">
  {/* Card content */}
</div>
```

#### Button
```tsx
<button className="px-6 py-3 bg-indigo-600 text-white rounded-xl font-bold hover:bg-indigo-700 transition-all">
  Action
</button>
```

---

## 🔌 API Integration

### Frontend API Client
```typescript
// lib/api/client.ts
export const cortex = {
  async getRecentMemories(limit: number) {
    const response = await fetch(`http://localhost:8000/api/v1/memories?limit=${limit}`);
    return response.json();
  },
  
  async ingest.submit(data: IngestRequest) {
    const response = await fetch('http://localhost:8000/api/v1/ingest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return response.json();
  },
};
```

### Backend API Response Format
```python
# Success Response
{
    "status": "success",
    "data": {...},
    "model": "gemini-2.0-flash-exp",  # Optional
    "timestamp": "2026-02-10T21:38:36Z"
}

# Error Response
{
    "status": "error",
    "message": "User-friendly error message",
    "detail": "Technical details for debugging"
}
```

---

## 🚫 Forbidden Practices

### NEVER Do These:

#### Frontend
- ❌ Use inline styles (`style={{}}`)
- ❌ Use CSS-in-JS libraries
- ❌ Use external UI component libraries (shadcn/ui, MUI, etc.)
- ❌ Use class components (always use functional components)
- ❌ Use `any` type without a good reason
- ❌ Hardcode API URLs (use environment variables)

#### Backend
- ❌ Use synchronous I/O in async functions
- ❌ Use `requests` library (use `httpx`)
- ❌ Use string interpolation for SQL queries
- ❌ Return raw exceptions to the client
- ❌ Use global state (use dependency injection)

#### General
- ❌ Commit sensitive data (API keys, passwords)
- ❌ Use `console.log` in production (use proper logging)
- ❌ Ignore TypeScript/Pydantic errors
- ❌ Write code without error handling

---

## 🔄 Git Workflow

### Branch Naming
- `feature/description` - New features
- `fix/description` - Bug fixes
- `refactor/description` - Code refactoring
- `docs/description` - Documentation updates

### Commit Messages
```
feat: Add card stack dashboard with swipe navigation
fix: Resolve mobile drag issue in NeuralGraph
refactor: Extract AI chat to floating component
docs: Update SYSTEM_CONTEXT with new guidelines
```

---

## 🧪 Testing Guidelines

### Frontend Testing
- Test user interactions (click, swipe, input)
- Test responsive design (mobile, tablet, desktop)
- Test error states and loading states
- Test accessibility (keyboard navigation, screen readers)

### Backend Testing
- Test API endpoints with valid/invalid data
- Test error handling and edge cases
- Test database queries and transactions
- Test AI integration and fallbacks

---

## 📦 Dependencies Management

### Frontend (package.json)
```json
{
  "dependencies": {
    "next": "14.x",
    "react": "18.x",
    "framer-motion": "^11.x",
    "recharts": "^2.x",
    "lucide-react": "^0.x",
    "react-markdown": "^9.x"
  }
}
```

### Backend (requirements.txt)
```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.5.0
httpx>=0.26.0
google-generativeai>=0.3.0
supabase>=2.3.0
```

---

## 🎯 AI Integration Guidelines

### Gemini API Usage
```python
import google.generativeai as genai

# Configure API
genai.configure(api_key=settings.GEMINI_API_KEY)

# Use streaming for real-time responses
model = genai.GenerativeModel('gemini-2.0-flash-exp')
response = model.generate_content(prompt, stream=True)

for chunk in response:
    yield chunk.text
```

### Prompt Engineering
- **Be specific**: Include context, constraints, and expected output format
- **Use examples**: Show the AI what you want
- **Set boundaries**: Define what NOT to do
- **Iterate**: Refine prompts based on results

---

## 📝 Documentation Standards

### Code Comments
```typescript
// GOOD: Explain WHY, not WHAT
// Use debounce to prevent excessive API calls during typing
const debouncedSearch = useMemo(() => debounce(search, 300), []);

// BAD: State the obvious
// Set the value to true
setIsOpen(true);
```

### Function Documentation
```python
async def process_memory(content: str, user_id: str) -> Memory:
    """
    Process raw memory content with AI and store in database.
    
    This function:
    1. Sends content to Gemini API for analysis
    2. Extracts metrics (mood, focus, energy)
    3. Generates markdown body
    4. Stores in Supabase
    
    Args:
        content: Raw user input (markdown supported)
        user_id: UUID of the user
        
    Returns:
        Memory object with AI-processed data
        
    Raises:
        HTTPException: If AI processing fails or database error occurs
    """
```

---

## 🔐 Security Guidelines

### Environment Variables
```bash
# .env.local (Frontend)
NEXT_PUBLIC_SUPABASE_URL=your_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_key

# .env (Backend)
GEMINI_API_KEY=your_key
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
```

### API Security
- **ALWAYS validate input** with Pydantic
- **ALWAYS use HTTPS** in production
- **NEVER expose API keys** in frontend code
- **ALWAYS sanitize user input** before database queries

---

## 🚀 Deployment

### Frontend (Vercel)
- Build command: `npm run build`
- Output directory: `.next`
- Environment variables: Set in Vercel dashboard

### Backend (Railway/Render)
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Environment variables: Set in platform dashboard

---

## 📚 Key Files Reference

### Must-Read Files
1. `SYSTEM_CONTEXT.md` (this file) - Complete context
2. `database-hippocampus/schema.sql` - Database structure
3. `frontend-body/lib/ai/core.ts` - Core engine logic
4. `backend-cortex/main.py` - API entry point

### Configuration Files
- `.cursorrules` - Cursor AI rules
- `tsconfig.json` - TypeScript configuration
- `tailwind.config.ts` - Tailwind configuration
- `next.config.js` - Next.js configuration

---

## 🎓 Learning Resources

### Internal Documentation
- `MOBILE_DRAG_FIX.md` - Mobile optimization guide
- `CARD_STACK_DASHBOARD.md` - Card stack implementation
- `AI_FLOATING_ASSISTANT_UPDATE.md` - AI assistant design

### External Resources
- [Next.js Docs](https://nextjs.org/docs)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [Gemini API Docs](https://ai.google.dev/docs)

---

## 🔄 Iteration Protocol

When AI generates incorrect code:

1. **Identify the root cause** (missing context, unclear instruction, etc.)
2. **Update this document** with the correct pattern
3. **Add to "Forbidden Practices"** if it's a common mistake
4. **Regenerate the code** with updated context

**Remember**: Every mistake is an opportunity to improve the system context.

---

## 💡 Philosophy

> "The goal is not to make AI write perfect code on the first try.
> The goal is to build a system where AI consistently writes code that aligns with our architecture, style, and philosophy."

**Core Principles**:
1. **Clarity > Cleverness**: Write obvious code, not clever code
2. **Consistency > Flexibility**: Follow patterns, even if there are "better" ways
3. **Context > Prompts**: Good context beats good prompts
4. **Evolution > Perfection**: Iterate and improve continuously

---

**Last Updated**: 2026-02-10  
**Version**: 3.1.0  
**Maintained By**: Commander 蒼禾 + Cortex AI

---

*This document is a living system. Update it whenever you discover new patterns, constraints, or best practices.*
