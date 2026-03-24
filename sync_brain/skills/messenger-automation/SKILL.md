---
name: messenger-automation
description: "Use when managing automation flows for external messengers like Messenger or WhatsApp. Handles Page Access Tokens and webhook responses."
---

# Skill: Messenger & WhatsApp Automation

## Overview
Manages the bridge between LifeOS and external communication platforms. Uses the Omni-Gateway protocol.

## 🕒 使用時機 (Usage Timing)
- **TOKEN REFRESH**: When Meta API tokens expire.
- **WEBHOOK RESPONSE**: When receiving a message from a shop or user.
- **AUTO-REPLY**: When certain keywords trigger a programmed response.

## 🛠️ Workflow

### 1. Token Persistence
- Page Access Tokens are stored in Render environment variables.
- AI must NOT store these in the filesystem.

### 2. Message Parsing
- Use **Gemma** to parse the raw webhook JSON.
- Identify intent and route to the correct `action_handler`.

### 3. Reply Proxy
- Send the generated response back to the platform via Graph API v25.0.

## 🛑 Rules
- Use only `127.0.0.1` for local proxy testing.
