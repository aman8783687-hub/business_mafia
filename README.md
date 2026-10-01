# RedHat Engineer on GitHub Actions

Makes one RedHat Engineer episode per run (the story and mysteries behind
technological innovation, as a 5-7 minute stickman explainer) and uploads it
to the Content Lab website. Nothing is posted to any social platform; you
download the video from Content Lab and post it by hand.

Each run: an opencode agent picks a technology-story topic, researches it,
writes the script and metadata; edge-tts records a female narration; FLUX.2
klein on Cloudflare Workers AI draws the scenes with the red-fedora host as a
reference image; ffmpeg renders a 1920x1080 video with synthesized ambience
(no music) and burned-in captions; a thumbnail is built from the hook scene;
the video is uploaded to Content Lab; and the episode's audio/scenes/render
are deleted so nothing piles up. The thumbnail and metadata are attached to
the run as an artifact (Content Lab has no thumbnail field).

The repo was forked from an Indian-history mystery channel ("Imagine Error")
and converted on 2026-09-30; the `MafiaOfBusiness/` directory name is left over
from that. See `MafiaOfBusiness/reports/changelog.md`.

## Setup

1. Push the contents of this folder to a new GitHub repository.
2. Repo **Settings > Secrets and variables > Actions > Secrets**, add:

   | Secret | Where the value comes from |
   |---|---|
   | `CONTENT_LAB_URL` | Base URL of your Content Lab site |
   | `CONTENT_LAB_API_KEY` | The Content Lab API key |
   | `CLOUDFLARE_API_TOKEN` | A Cloudflare API token with Workers AI permissions |
   | `CLOUDFLARE_ACCOUNT_ID` | Your Cloudflare account ID |
   | `MONGODB_URI` | Atlas connection string |
   | `RAPHAEL_COOKIE` | Optional, currently no use: a signed-in free account is blocked by a captcha check (see changelog 2026-09-30) |

3. Optional **Variables**: `IMAGE_BACKEND` (`flux`, the default, keeps the
   host on-model; `raphael` and `cloudflare` are text-only fallbacks that
   cannot), `CLOUDFLARE_IMAGE_MODEL` (`flux-2-klein-9b` default;
   `flux-2-klein-4b` is cheaper against the free quota but follows the
   red/black/white style less well), `OPENCODE_MODEL`, `MAX_ATTEMPTS`
   (default 4), `MAX_SLOT_FAILURES` (default 3).
4. **MongoDB Atlas > Network Access**: allow `0.0.0.0/0`.

**Free-quota warning.** Cloudflare's free tier is 10,000 neurons a day. A
50-scene episode on the 9B model can exceed that; `generate_scenes.py` skips
finished beats, so a run that stops at the quota can simply be re-run after
the reset. This is the reason the repo briefly defaulted to raphael.app on
2026-09-30; raphael cannot take the host reference image, so it is not a
drop-in substitute.

## Running

`.github/workflows/redhat-engineer.yml` only has a `workflow_dispatch`
trigger: run it from the Actions tab. Add an `on: schedule:` cron block
yourself once a cadence is chosen. `./make-video` runs one cycle locally.

## Storage and state

Nothing is committed back to the repo, and no audio, images or video are
ever stored. State lives in MongoDB (database `imagine_error_pipeline`, name
kept from the fork so counters and topic history carry over; override with
`MONGODB_DB`): `topics`, `episodes`, `state` collections. `pull` takes only
`counters`, `baselines` and `active_experiment` from MongoDB; all other
config in `channel_state.json` comes from git.
