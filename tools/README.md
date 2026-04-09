# Tools

## present.py — Presenterm Image Zoom Wrapper

Wraps [presenterm](https://github.com/mfontanini/presenterm) to add fullscreen image zoom during presentations. Images in terminal slides can be small — this lets you pop them open in macOS Preview on demand.

### Usage

```bash
# From the repo root
python3 tools/present.py vector_storage_at_scale.md

# With presenterm flags
python3 tools/present.py vector_storage_at_scale.md --present --theme dark
```

### Keys (in addition to normal presenterm keys)

| Key | Action |
|-----|--------|
| `z` | Toggle zoom — opens current slide's image in Preview / closes it |
| `[` | Nudge slide counter back (if tracking drifts) |
| `]` | Nudge slide counter forward (if tracking drifts) |

All other keys (arrows, hjkl, Space, gg, G, etc.) work exactly as in presenterm.

### Debug Mode

```bash
PRESENT_DEBUG=1 python3 tools/present.py vector_storage_at_scale.md

# In another terminal:
tail -f /tmp/present_debug.log
```

### Requirements

- macOS (uses Preview.app and AppleScript for image display)
- Python 3 (no external dependencies)
- [presenterm](https://github.com/mfontanini/presenterm) installed
