# 📜 Pixar Project: Development Guidelines

## 1. Modularity First
- **NO HARDCODED STRINGS**: All UI text must go to `assets/languages.json`.
- **NO HARDCODED CONSTANTS**: All numbers, limits, and technical values must go to `src/core/constants.py`.
- **NO HARDCODED STYLES**: All colors, fonts, and dimensions must be referenced from `constants.py` or a dedicated StyleManager.

## 2. Directory Structure
- `src/core/`: Business logic and rendering engine.
- `src/utils/`: Independent helper modules (Language, Resource Monitor, etc.).
- `assets/`: Non-code resources (Images, JSON translations).
- `models/`: Weights and AI components.

## 3. UI Implementation
- Every new feature must include a 'Help' (?) icon with translations in the JSON.
- UI must be responsive and respect the theme tokens in `constants.py`.



---
*Note: This document must be read at the start of every session to ensure architecture consistency.*
