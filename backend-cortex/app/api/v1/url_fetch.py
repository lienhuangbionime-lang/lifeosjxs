"""
URL Fetch API - Extract content from YouTube and web pages for CortexChat
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
import re

router = APIRouter()
logger = logging.getLogger("cortex.url_fetch")


class UrlFetchRequest(BaseModel):
    url: str


class UrlFetchResponse(BaseModel):
    url: str
    type: str          # "youtube" | "webpage"
    title: str
    content: str       # Extracted text content
    summary: str       # Short preview (first 300 chars)


def is_youtube_url(url: str) -> bool:
    patterns = [
        r'youtube\.com/watch',
        r'youtu\.be/',
        r'youtube\.com/shorts/',
    ]
    return any(re.search(p, url) for p in patterns)


def extract_youtube_id(url: str) -> Optional[str]:
    patterns = [
        r'v=([a-zA-Z0-9_-]{11})',
        r'youtu\.be/([a-zA-Z0-9_-]{11})',
        r'shorts/([a-zA-Z0-9_-]{11})',
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def fetch_youtube_transcript(video_id: str) -> tuple[str, str]:
    """Returns (title, transcript_text)"""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['zh-TW', 'zh', 'en'])
        text = " ".join([t['text'] for t in transcript_list])
        title = f"YouTube Video ({video_id})"
        return title, text
    except Exception as e:
        logger.warning(f"Transcript fetch failed: {e}")
        # Next attempt: try any available transcript
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            text = " ".join([t['text'] for t in transcript_list])
            return f"YouTube Video ({video_id})", text
        except Exception as e2:
            logger.warning(f"All transcript attempts failed: {e2}")
            # Final Fallback: Fetch basic video info from page title/meta
            try:
                import requests
                from bs4 import BeautifulSoup
                url = f"https://www.youtube.com/watch?v={video_id}"
                headers = {'User-Agent': 'Mozilla/5.0'}
                resp = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(resp.text, 'html.parser')
                title = soup.title.string.replace(" - YouTube", "") if soup.title else f"YouTube Video {video_id}"
                desc = soup.find("meta", property="og:description")
                desc_text = desc.get("content", "") if desc else "No description available."
                return title, f"[No Transcript Available]\n\nDescription: {desc_text}"
            except Exception as e3:
                raise HTTPException(
                    status_code=422,
                    detail=f"Cannot fetch transcript or metadata for this video ({e3})"
                )


def fetch_webpage_content(url: str) -> tuple[str, str]:
    """Returns (title, main_text)"""
    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, 'html.parser')

        # Extract title
        title = ""
        if soup.title:
            title = soup.title.string or ""
        if not title:
            og_title = soup.find('meta', property='og:title')
            if og_title:
                title = og_title.get('content', '')

        # Remove noise elements
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript']):
            tag.decompose()

        # Try to find main content area
        main = (
            soup.find('article') or
            soup.find('main') or
            soup.find(class_=re.compile(r'post|content|article|entry|body', re.I)) or
            soup.find('body')
        )

        if main:
            text = main.get_text(separator='\n', strip=True)
        else:
            text = soup.get_text(separator='\n', strip=True)

        # Clean up excessive whitespace
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        text = '\n'.join(lines)

        # Limit to ~8000 chars to avoid token overflow
        if len(text) > 8000:
            text = text[:8000] + "\n\n[Content truncated for length...]"

        return title.strip(), text

    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Cannot fetch webpage: {e}")


@router.post("/fetch", response_model=UrlFetchResponse)
async def fetch_url(request: UrlFetchRequest):
    """
    Fetch and extract content from a URL (YouTube or webpage).
    Returns structured content ready for CortexChat discussion.
    """
    url = request.url.strip()
    logger.info(f"🔗 Fetching URL: {url}")

    if is_youtube_url(url):
        video_id = extract_youtube_id(url)
        if not video_id:
            raise HTTPException(status_code=400, detail="Cannot extract YouTube video ID")

        title, content = fetch_youtube_transcript(video_id)
        return UrlFetchResponse(
            url=url,
            type="youtube",
            title=title,
            content=content,
            summary=content[:300] + "..." if len(content) > 300 else content
        )
    else:
        title, content = fetch_webpage_content(url)
        return UrlFetchResponse(
            url=url,
            type="webpage",
            title=title or url,
            content=content,
            summary=content[:300] + "..." if len(content) > 300 else content
        )
