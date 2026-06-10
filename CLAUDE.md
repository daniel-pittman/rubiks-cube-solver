# CLAUDE.md - Important Project Directions

## ⚠️ CRITICAL INSTRUCTIONS TO NEVER FORGET ⚠️
1. **USE PROVEN APPROACHES** - Use matrix transformations like magiccube reference; don't reinvent working solutions
2. **DOCUMENT EVERY MESSAGE** - Add all user prompts and responses to conversation_summary/ files immediately - this is a critical directive that can never be ignored
3. **NO EXTRA FILES** - Don't create debug scripts, test files, or redundant docs unless explicitly requested
4. **STAY FOCUSED** - Don't go in directions user didn't ask for
5. **PRESERVE VERBATIM QUOTES** - Keep complete user prompts and critical guidance moments; don't over-summarize
6. **REFERENCE EXISTING WORK** - When solving problems, check if you already solved it in earlier phases (web → desktop pattern)

## Automated Review Policy

The PR review workflow enforces two rules the automated reviewer applies on every pull request:

- **Tests ship with code.** If a PR changes application or library source code in a way that warrants tests (new or changed behavior, bug fixes, new branches or edge cases) and does not add or update corresponding tests, the reviewer flags it as a HIGH-severity finding. Docs-only, README, comments, formatting, and pure-configuration changes (CI YAML, lockfile bumps, asset-only, version bumps) are exempt.
- **Security findings inform the review.** A free, token-free security scan runs before the Claude review and posts its findings as a single sticky PR comment, which the reviewer folds into its analysis. Semgrep (OSS) scans with the `p/python`, `p/javascript`, `p/bash`, `p/secrets`, and `p/ci` rule packs for the Python solver, the Three.js web frontend, the shell scripts, committed secrets, and CI misconfig. `pylint` remains the Python static analyzer in CI.

## Project Overview
**Rubik's Cube 3D Visualization App** - A comprehensive learning project for Claude Code best practices.

## Critical Requirements
1. **ALL CODE** must go in `solver/` folder
2. **INCREMENTAL DEVELOPMENT**: Don't move to next phase until current is 100% complete
3. **TESTING**: Achieve >95% code coverage with meaningful unit tests
4. **LINTING**: Must pass all formatters in `run_python_formatters.sh` with pylint score ≥ 9.0

## Development Phases (All Complete)
1. **Core Cube Implementation** ✅ **PRODUCTION READY** - Matrix transformations, all moves validated
2. **Solver Integration** ✅ **PRODUCTION READY** - Plugin system with IDDFS
3. **CLI Interface** ✅ **PRODUCTION READY** - Interactive terminal with colored output
4. **Web Interface** ✅ **PRODUCTION READY** - 3D visualization with hybrid interaction, mobile support
5. **Desktop App** ✅ **PRODUCTION READY** - PySide6/OpenGL with background solver thread

## Key Technical Details
- **Reference**: https://github.com/trincaog/magiccube for cube representation
- **Linters**: black, autoflake, isort (--profile=black), pylint
- **Dependencies**: flask, numpy, pytest (no external solver dependencies)
- **Git**: Use pre-commit hooks, document everything
- **Solver**: Plugin-based architecture with IDDFS algorithm implementation

## File Structure
```
solver/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── cube.py          # Core cube implementation (505 lines) ✅
│   ├── solver.py        # Main CubeSolver interface (186 lines) ✅
│   ├── solvers/         # Plugin-based solver system ✅
│   │   ├── __init__.py          # Plugin initialization (124 lines)
│   │   ├── base_solver.py       # Abstract classes & registry (232 lines)
│   │   └── iddfs_solver.py      # IDDFS implementation (246 lines)
│   └── tests/
│       ├── test_cube.py           # Basic unit tests (32 tests) ✅
│       └── test_cube_comprehensive.py # Comprehensive test suite (41 tests) ✅
├── cli/             # CLI interface package ✅
│   ├── __init__.py          # CLI package initialization (13 lines)
│   ├── __main__.py          # Module entry point (10 lines)
│   └── cli_app.py           # Complete CLI implementation (650+ lines)
├── cli_app.py       # Backward compatibility wrapper ✅
├── flask_app.py     # Web interface (complete) ✅
├── web/             # Web interface assets ✅
│   ├── static/
│   │   ├── css/styles.css       # Complete responsive styling
│   │   └── js/
│   │       ├── cube3d.js        # Three.js 3D cube visualization
│   │       ├── socket-client.js # Real-time communication
│   │       ├── ui-controls.js   # Interactive controls
│   │       ├── move-log.js      # Move history tracking
│   │       └── app.js           # Main application
│   └── templates/
│       └── index.html           # Complete web interface
├── desktop/                  # Desktop application ✅
│   ├── cube_gl_widget.py    # OpenGL 3D widget
│   └── __init__.py
├── desktop_app.py           # PySide6 main window ✅
└── tests/           # Integration tests ✅
    └── test_solver_integration.py  # Solver integration tests (236 lines)
```

## Documentation Files
- `conversation_summary/`: Complete conversation history organized by development phase
  - `phase1_core_cube.md`: Initial implementation and critical rewrite
  - `phase2_solver.md`: Kociemba failures, IDDFS pivot
  - `phase3_cli.md`: CLI development and UX iterations
  - `phase4_web.md`: Web interface, Western color scheme, hybrid interaction
  - `phase5_desktop.md`: Desktop app and final documentation
- `README.md`: Project overview emphasizing human-AI collaboration story
- `DEVELOPMENT_JOURNAL.md`: Claude's retrospective with technical architecture and lessons learned
- `CLAUDE.md`: This file - critical instructions and project directions

## Testing Strategy
- Unit tests for every function/method
- Integration tests for cube operations
- 100% pass rate required before phase completion
- Use pytest framework with comprehensive coverage

## 🎯 CRITICAL BUG FIXES COMPLETED

### Cube Move Implementation Fixed (September 28-30, 2025)
**Issue**: Initial implementation had incorrect edge cycling for 5/6 moves
**Resolution**: Rewrote all cube moves with proper edge cycling following standard Rubik's cube mechanics
**Validation**: All moves now pass comprehensive tests including scramble sequences

### Phase 4 Achievements ✅ PRODUCTION READY
- **Web Interface**: Complete 3D visualization with Three.js
- **Hybrid Interaction Mode**: Seamless face clicking + camera dragging
  - Left-click face: Clockwise rotation
  - Right-click face: Counter-clockwise rotation
  - Ctrl/Cmd+Click face: Double rotation (180°)
  - Drag background: Rotate camera view
  - Smart drag detection using OrbitControls events (0.3 unit movement OR 8 change events threshold)
- **Mobile Touch Support**: Full mobile responsiveness
  - Single tap: Clockwise rotation
  - Double-tap: Counter-clockwise rotation (300ms delay pattern)
  - Touch-optimized UI with full-width tooltips
  - Fixed CSS Grid overflow with minmax(0, 1fr)
- **Real-time Synchronization**: WebSocket updates with proper animation callbacks
- **Solution Replay**: State save/restore for solution playback
- **Move Logging**: Comprehensive move history tracking with dark-themed panel
- **Visual Polish**: Responsive controls, professional styling, intuitive UX

### Key Technical Innovations
1. **OrbitControls Event-Based Drag Detection**: Uses 'start', 'change', and 'end' events to track camera movement, avoiding unreliable mousedown position checks
2. **Animation Callback Synchronization**: Colors update exactly when animation completes via callback parameter
3. **Hybrid Mode Design**: No mode toggle needed - system intelligently handles both face clicks and camera drags simultaneously

### Phase 5 Achievements ✅ PRODUCTION READY
- **Desktop Application**: PySide6 with hardware-accelerated OpenGL rendering
- **Background Solver Thread**: QThread with Signal/Slot to prevent UI freezing during solve
- **Face Click Detection**: Ray-casting with proper OpenGL context (glReadPixels in paintGL)
- **Solution Dialog**: Manual playback controls (Play/Pause/Stop/Reset)
- **Reused Solutions**: Copied working coordinate mapping formulas from web version (user directive: "you already solved all this with the flask app")
- **Accessibility**: WCAG AA contrast compliance, fixed tooltip sizing
- **Default Updates**: Scramble depth 5, solver max_depth 5 (appropriate for IDDFS)

## Key Lessons Learned
1. **Always fix bugs at the lowest level** - Don't mask issues at higher levels
2. **Test behavioral correctness, not just mathematical properties** - R⁴ = identity doesn't mean R is correct
3. **Reference your own working code** - Don't reinvent solutions from earlier phases
4. **Documentation discipline** - Update conversation logs immediately, don't batch
5. **Phase completion criteria** - 100% working before moving on prevents cascading failures
6. **Human guidance critical for** - Architecture, UX decisions, debugging, knowing when to restart vs iterate