# Phase 4 — Project Structure & Entry Point Mapping

## Top-Level Layout
<tree summary, 2-3 levels deep>

## Entry Points
- **Main app:** <path> — <responsibility> — <commit-pinned URL>
- **CLI:** <path> — <responsibility> — <URL>
- **Worker / Job:** <path> — <responsibility> — <URL>
- **Frontend:** <path> — <responsibility> — <URL>

## Layers / Folders
- **Controllers/Handlers:** <path(s)>
- **Services/Use cases:** <path(s)>
- **Models/Entities:** <path(s)>
- **Persistence:** <path(s)>
- **Config:** <path(s)>
- **Scripts:** <path(s)>
- **Infrastructure:** <path(s)>

## Recommended Reading Path (new dev week 1)
1. README + CONTRIBUTING
2. Entry point
3. Routing / config layer
4. One vertical slice (controller → service → repo → db)
5. Tests for that slice
6. CI / Docker / deploy
