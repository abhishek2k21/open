# Logo brief and generation prompts

## What the icon must say

The Actor answers one question: **which of my subdomains is about to break or be taken over?** The icon therefore shows a radar scope with one host out of many flagged. It is a security instrument, not a "hacker" cliché: no padlocks, no hoodies, no Matrix rain, no browser windows.

Shipped assets (all generated from this brief, no AI required):

| File | Use |
|---|---|
| `logo.svg` | Vector source, 512×512 viewBox, transparent background |
| `logo-512.png` | **Upload this one** to Console → Publishing → Display information |
| `logo-256.png` | Docs, README embeds |
| `logo-64.png` | Small-size legibility check (this is roughly how the Store renders it) |
| `logo-tile-512.png` | Dark rounded tile for slides, X/LinkedIn posts, blog headers |

Regenerate after any palette change:

```bash
pip install pillow
python assets/render_logo.py
```

## Palette (and why each colour exists)

The palette is derived from the Actor's own severity vocabulary, so the icon, the dataset and the Store page speak the same language.

| Role | Hex | Where it appears |
|---|---|---|
| Base ink | `#0F1B2E` | Hexagon body. Dark enough to read on Apify's white Store card, not pure black |
| Radar cyan | `#22D3EE` | Rim, range rings, sweep. Means "scanning, live, telemetry" |
| Healthy green | `#22C55E` | Hosts with `severity: info` |
| Warning amber | `#F59E0B` | `severity: medium` - the common real finding, `certificate_expiring` |
| Critical red | `#EF4444` | `severity: high/critical` - `subdomain_takeover`, `certificate_expired`. Reserved for docs and diagrams; deliberately kept out of the icon so the Store card does not look like an error state |
| Core white | `#E2E8F0` | Scanner origin |
| Tile ink | `#0B1220` | Background of `logo-tile-512.png` |

Rules: flat vector, two weights of stroke, no gradients except the single sweep fade, no more than five colours, no text (the Store prints the title beside the icon).

## AI generation prompt (primary)

Paste into Midjourney v6+, Ideogram, Flux, GPT-image or Gemini. The prompt is written to avoid rendered text and to survive 40px downscaling.

```
Minimal flat vector app icon, square 1:1, transparent background, centered.

Subject: a hexagonal security badge whose face is a radar scope. Two concentric cyan range rings and one soft cyan sweep wedge radiate from a small white center dot. Four circular host markers sit inside: three emerald green and one amber with a thin amber warning ring around it - the single risky host among healthy ones. Faint crosshair lines behind the rings.

Colors, use exactly these: badge fill #0F1B2E, radar lines and badge rim #22D3EE, healthy markers #22C55E, warning marker #F59E0B, center dot #E2E8F0. No other hues.

Style: geometric, crisp, flat 2D vector, uniform stroke weights, hard edges, generous negative space, reads clearly at 40x40 pixels, professional security-tool branding, no perspective, no bevel, no inner shadow, no texture.

Output: single centered icon filling about 80 percent of the frame, transparent margins, high resolution 1024x1024, no text, no letters, no numbers, no watermark, no background scene.
```

Midjourney parameters to append: `--ar 1:1 --style raw --v 6.1 --no text, letters, watermark, mockup, 3d, glossy, drop shadow, window, browser`.

### Negative prompt (use verbatim where the tool accepts one)

```
text, letters, words, numbers, watermark, signature, logo mockup, business card, laptop, hand, person, padlock, lock, key, hoodie, skull, bug, virus, binary code, matrix rain, browser window, mouse cursor, checkmark shield, globe with grid, gradient mesh, neon glow overload, 3d render, bevel, emboss, glossy highlight, drop shadow, cluttered detail, tiny elements, photographic, textured paper
```

## Alternative directions (same palette)

**A. Sweep-only** - drop the rings entirely: hexagon badge, one bold cyan wedge from the center, four host dots. Best small-size legibility, weakest storytelling.
```
Flat vector hexagon badge, fill #0F1B2E, rim #22D3EE, one bold cyan (#22D3EE) radar wedge from a white center dot to the upper right, four small host dots inside (#22C55E x3, #F59E0B x1 with a thin amber ring), transparent background, geometric, no text, 1024x1024, icon design
```

**B. Broken link** - a chain link splitting apart inside the hexagon, cyan chain, one amber end. Communicates takeover more literally.
```
Minimal flat vector icon: hexagonal badge #0F1B2E with a cyan #22D3EE rim; inside, a chain link breaking in two, the right half amber #F59E0B and slightly displaced, small cyan spark at the break, transparent background, 2-color flat vector, no text, 1024x1024
```

**C. Certificate edge** - a document silhouette with a clipped corner and an amber countdown arc.
```
Minimal flat vector icon: a dark navy #0F1B2E document shape with a clipped top-right corner inside a cyan #22D3EE hexagonal rim, an amber #F59E0B arc sweeping around the bottom like a countdown dial, transparent background, geometric flat design, no text, 1024x1024
```

## Export and upload checklist

1. Generate at 1024×1024, then downscale to **512×512** so you are not shipping a blurry upscale.
2. macOS downscale: `sips -z 512 512 input.png --out logo-512.png`
3. Export PNG-24 with alpha (no JPG, no white matte), under 200 KB.
4. Keep the artwork inside an 80% safe area; the Store crops to a circle in some placements.
5. View it at 64px and 40px before uploading. If the amber marker disappears, the icon fails the only job it has.
6. Upload: Console → Actor → **Publishing** → **Display information** → logo area. Drag the PNG onto the dashed upload box and wait for the spinner to finish before editing other fields.
