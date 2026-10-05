# Edit and assembly

No intro or outro: the [HOOK] beat is the first scene, the [SABAK] beat the last.

`assemble_episode.py` renders each scene with Ken Burns zoompan (duration extended to the next beat's start so `-shortest` never truncates the ending), concatenates, mixes the voice with the ambience layer (no music), masters loudness, builds and burns captions (`ass` filter, complex shaping; skipped gracefully if `word_timings.json` is missing), and muxes to `07_edit/mafia-of-business-<slug>.mp4` plus a `captions.srt` sidecar.

Export: 1920x1080, 30 fps, H.264, AAC, CRF 22 with a 6 Mbps cap. Target runtime 600 s; `stitch_audio.py` and `finalize_episode.py` enforce 480-720 s. A 10-minute render takes several times longer than the old 4-minute one; let it run. `LOW_MEM_RENDER=1` renders at ~60% scale, a local-only workaround. `--no-ambience` gives an A/B render without the ambience layer.

`run_episode.py` then builds the thumbnail and runs `finalize_episode.py`, which copies the package to `output/<slug>/`.
