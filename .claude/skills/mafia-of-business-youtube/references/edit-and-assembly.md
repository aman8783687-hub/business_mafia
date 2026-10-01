# Edit and assembly

No intro or outro: the cold-open beat is the first scene, the aftermath beat the last.

`assemble_episode.py` renders each scene with Ken Burns zoompan (duration extended to the next beat's start so `-shortest` never truncates the ending), concatenates, mixes the voice with the ambience layer (no music), masters loudness, builds and burns captions (libass `subtitles`; skipped gracefully if `word_timings.json` is missing), and muxes to `07_edit/redhat-engineer-<slug>-episode.mp4` (the only copy of the render) plus a `captions.srt` sidecar.

Export: 1920x1080, 30 fps, H.264, AAC. `LOW_MEM_RENDER=1` renders at ~60% scale, a local-only workaround. `--no-ambience` gives an A/B render without the ambience layer.

Flat whiteboard art compresses far below the bitrate cap; if a file is ever too large for Content Lab's single-upload limit, lower the render bitrate and re-run assembly.
