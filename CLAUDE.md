# claude_video_edits

Video edits built with the HeyGen HyperFrames skills (`.agents/skills/`, symlinked into `.claude/skills/`).

## Conventions

- Each project lives in `videos/<project-name>/` (talking-head-recut layout: `public/index.html`, `public/cards/`, `transcript.json`, `storyboard.json`).
- **Always commit and push the finished renders** (`output.mp4` full quality and `output-share.mp4` compressed preview) so they can be downloaded from GitHub. Keep each file under GitHub's 100 MB limit.
- Source footage, extracted audio and render scratch dirs stay gitignored.
- The user communicates in Hungarian; reply in Hungarian.
