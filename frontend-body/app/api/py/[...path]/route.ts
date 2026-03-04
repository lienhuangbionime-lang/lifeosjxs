import { NextRequest, NextResponse } from 'next/server';

/**
 * [FIX] Server-side proxy for all /api/py/... requests.
 *
 * Why this exists:
 * - Next.js rewrites() in next.config.js use `localhost` which on Windows
 *   can resolve to IPv6 (::1) while uvicorn listens on IPv4, causing hangs.
 * - Direct browser cross-origin calls with custom headers (X-Supabase-Key etc.)
 *   fail CORS preflight in owner mode.
 *
 * This route handler runs on the Next.js server (Node.js), which:
 * 1. Is same-origin from the browser's perspective (no CORS issues)
 * 2. Uses Node.js HTTP which properly resolves 127.0.0.1 without IPv6 issues
 * 3. Forwards all user API key headers to the backend transparently
 */

const FALLBACK_PROD_URL = 'https://lifeosjxs.onrender.com';

const BACKEND_URL = (process.env.NODE_ENV === 'production'
    ? (process.env.NEXT_PUBLIC_PYTHON_API_URL || FALLBACK_PROD_URL)
    : 'http://127.0.0.1:8000').replace(/\/$/, ""); // Strip trailing slash

if (process.env.NODE_ENV === 'production' && !process.env.NEXT_PUBLIC_PYTHON_API_URL) {
    console.warn(`[Proxy] NEXT_PUBLIC_PYTHON_API_URL is missing. Falling back to default: ${FALLBACK_PROD_URL}`);
}

// Headers that should not be forwarded to the backend
const HOP_BY_HOP_HEADERS = new Set([
    'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization',
    'te', 'trailers', 'transfer-encoding', 'upgrade', 'host',
]);

async function proxyRequest(request: NextRequest, path: string[]) {
    const pathStr = path.join('/');
    const search = request.nextUrl.search;
    const targetUrl = `${BACKEND_URL}/api/v1/${pathStr}${search}`;

    // Forward all headers except hop-by-hop
    const forwardHeaders: Record<string, string> = {};
    request.headers.forEach((value, key) => {
        if (!HOP_BY_HOP_HEADERS.has(key.toLowerCase())) {
            forwardHeaders[key] = value;
        }
    });

    const body = ['GET', 'HEAD'].includes(request.method) ? undefined : await request.text();

    try {
        const backendRes = await fetch(targetUrl, {
            method: request.method,
            headers: forwardHeaders,
            body,
        });

        const responseBody = await backendRes.text();

        return new NextResponse(responseBody, {
            status: backendRes.status,
            headers: {
                'Content-Type': backendRes.headers.get('Content-Type') || 'application/json',
            },
        });
    } catch (err: any) {
        console.error(`[Proxy] Failed to reach backend at ${targetUrl}:`, err.message);
        return NextResponse.json(
            { error: 'Backend unreachable', detail: err.message },
            { status: 502 }
        );
    }
}

// [Next.js 15] params is a Promise — must be awaited
type RouteContext = { params: Promise<{ path: string[] }> };

export async function GET(request: NextRequest, context: RouteContext) {
    const { path } = await context.params;
    return proxyRequest(request, path);
}

export async function POST(request: NextRequest, context: RouteContext) {
    const { path } = await context.params;
    return proxyRequest(request, path);
}

export async function PUT(request: NextRequest, context: RouteContext) {
    const { path } = await context.params;
    return proxyRequest(request, path);
}

export async function PATCH(request: NextRequest, context: RouteContext) {
    const { path } = await context.params;
    return proxyRequest(request, path);
}

export async function DELETE(request: NextRequest, context: RouteContext) {
    const { path } = await context.params;
    return proxyRequest(request, path);
}

export async function OPTIONS(request: NextRequest, context: RouteContext) {
    // Next.js handles CORS preflight locally to allow browser custom headers
    return new NextResponse(null, {
        status: 204,
        headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, x-gemini-key, x-supabase-url, x-supabase-key, X-Gemini-Key, X-Supabase-URL, X-Supabase-Key',
            'Access-Control-Max-Age': '86400',
        },
    });
}
