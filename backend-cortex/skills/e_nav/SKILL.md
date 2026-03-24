# Skill: E-Nav Nomad

This skill manages the "Nomad" entities (stores/restaurants) and their digitized menus within the LifeOS ecosystem.

## Features
- **Ingestion**: Scrapes external food maps (e.g., Siktung Tainan) and converts them into `NomadEntity` objects.
- **Digitization**: Uses Gemini 3.0 Flash to convert menu images into structured JSON.
- **Logistics**: Generates deep links for navigation and provides price/ETA comparisons for delivery platforms.

## Core Modules
- `schema.py`: Pydantic v2 data models.
- `perception.py`: Data ingestion and scraping logic.
- `vision_engine.py`: AI-powered menu processing.
- `executor.py`: Action fulfillment (navigation, ordering).
