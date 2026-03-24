---
name: smart-ingest
description: "Use when processing incoming files, messages, or images. Automatically classifies and routes data into either the 'memories' (Diary) or 'documents' (Knowledge) store."
---

# Skill: Smart Ingest & Routing

## Overview
Ensures that the AI brain remains organized by following a strict classification logic for all ingested data.

## 🕒 使用時機 (Usage Timing)
- **FILE UPLOAD**: When a user uploads a PDF or image in chat.
- **WEBHOOK**: Incoming signals from WhatsApp or OpenClaw.
- **CLIPPER**: When the user saves a web snippet.

## 🛠️ Workflow

### 1. Classification
Identify the nature of the content:
- **Event-Based/Reflective**: Route to `memories` table.
- **Factual/Technical/Instructional**: Route to `documents` table.

### 2. Extraction
Call the `Crystallizer` service to extract nodes and edges for the graph.

### 3. Verification
Confirm ingestion success and report the `doc_id` to the user.

## 🛑 Guardrails
- **DO NOT** mix personal memories into the public documentation store.
