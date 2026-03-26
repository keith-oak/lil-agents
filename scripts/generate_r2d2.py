"""Generate a walking R2-D2 pixel art animation as individual PNG frames."""

import math
import os

from PIL import Image, ImageDraw

# --- Config ---
WIDTH, HEIGHT = 1080, 1920
TOTAL_FRAMES = 240
FPS = 24
PIXEL = 20  # pixel block size
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames_r2d2")

# Colours
WHITE_BODY = (240, 240, 245)
BLUE_PANEL = (50, 100, 200)
BLUE_PANEL_LIGHT = (80, 130, 220)
DOME_SILVER = (180, 190, 200)
DOME_HIGHLIGHT = (210, 218, 228)
EYE_RED = (220, 50, 30)
EYE_GLOW = (255, 120, 100)
LEG_SILVER = (160, 165, 175)
LEG_DARK = (130, 135, 145)
FOOT_SILVER = (140, 145, 155)
OUTLINE = (60, 60, 70)
DETAIL_DARK = (100, 110, 130)
SHADOW = (0, 0, 0, 40)


def snap(v):
    """Snap a value to the pixel grid."""
    return int(v // PIXEL) * PIXEL


def draw_rect(draw, x, y, w, h, colour, outline_col=None):
    """Draw a pixel-snapped rectangle."""
    x, y, w, h = snap(x), snap(y), snap(w), snap(h)
    if w <= 0 or h <= 0:
        return
    draw.rectangle([x, y, x + w - 1, y + h - 1], fill=colour, outline=outline_col)


def get_animation_params(frame):
    """Return (body_x_offset, body_y_offset, tilt_deg, left_leg_lift, right_leg_lift, dome_wobble)."""

    if frame < 72:
        # Idle: gentle dome wobble, slight body bob
        bob = math.sin(frame * 0.1) * 4
        dome_wobble = math.sin(frame * 0.08) * 4
        return 0, bob, 0, 0, 0, dome_wobble

    elif frame < 90:
        # Accelerate into waddle
        t = (frame - 72) / 18.0
        ease = t * t * t  # cubic ease in
        cycle = (frame - 72) * 0.2
        sc = math.sin(cycle)

        body_x = sc * 38 * ease
        tilt = sc * 12 * ease
        # Opposite leg lifts when body tilts that way
        left_lift = max(0, sc) * 38 * ease
        right_lift = max(0, -sc) * 38 * ease
        body_y = -abs(sc) * 10 * ease
        dome_wobble = math.sin(frame * 0.12) * 5 * ease
        return body_x, body_y, tilt, left_lift, right_lift, dome_wobble

    elif frame < 192:
        # Full waddle — big rocking motion
        cycle = (frame - 90) * 0.22
        sc = math.sin(cycle)

        body_x = sc * 44
        tilt = sc * 14
        left_lift = max(0, sc) * 50      # left leg lifts when leaning right
        right_lift = max(0, -sc) * 50     # right leg lifts when leaning left
        body_y = -abs(sc) * 12
        dome_wobble = math.sin(frame * 0.15 + 0.5) * 6
        return body_x, body_y, tilt, left_lift, right_lift, dome_wobble

    elif frame < 204:
        # Decelerate
        t = 1.0 - (frame - 192) / 12.0
        ease = t * t
        cycle = (frame - 192) * 0.2
        sc = math.sin(cycle)

        body_x = sc * 38 * ease
        tilt = sc * 12 * ease
        left_lift = max(0, sc) * 38 * ease
        right_lift = max(0, -sc) * 38 * ease
        body_y = -abs(sc) * 10 * ease
        dome_wobble = math.sin(frame * 0.1) * 4 * ease
        return body_x, body_y, tilt, left_lift, right_lift, dome_wobble

    else:
        # Return to idle
        t = min(1.0, (frame - 204) / 36.0)
        ease = 1.0 - t
        bob = math.sin(frame * 0.1) * 4 * ease
        dome_wobble = math.sin(frame * 0.08) * 3 * (1 - t)
        return 0, bob, 0, 0, 0, dome_wobble


def draw_r2d2(draw, frame):
    """Draw R2-D2 for the given frame number."""
    body_x_off, body_y_off, tilt_deg, left_lift, right_lift, dome_wobble = (
        get_animation_params(frame)
    )

    cx = WIDTH // 2
    base_y = 1920  # feet touch the very bottom of the canvas

    # --- Dimensions (scaled up ~1.25x for visibility) ---
    body_w = 280
    body_h = 300
    leg_w = 76
    leg_h = 226
    foot_w = 100
    foot_h = 50
    leg_spacing = 190
    centre_leg_w = 50
    centre_leg_h = 164
    centre_foot_w = 76
    centre_foot_h = 38
    dome_w = 280
    dome_h = 190

    # Key Y positions
    feet_bottom = base_y
    leg_top = feet_bottom - foot_h - leg_h
    body_top = leg_top - body_h + 62  # overlap legs slightly (scaled)
    body_bottom = body_top + body_h

    # Apply body offsets
    bcx = cx + int(body_x_off)
    body_top_anim = body_top + int(body_y_off)

    # --- Draw shadow on ground ---
    shadow_w = 380 + int(abs(body_x_off) * 0.5)
    shadow_h = 24
    sx = snap(cx - shadow_w // 2 + body_x_off * 0.3)
    sy = snap(base_y - shadow_h)  # shadow just above canvas bottom
    draw.rectangle([sx, sy, sx + shadow_w, sy + shadow_h], fill=SHADOW)

    # === LEGS (drawn first, behind body) ===
    # Legs follow the body's horizontal offset so they stay attached

    # Left leg
    ll_cx = bcx - leg_spacing
    ll_lift = int(left_lift)
    ll_top = snap(leg_top + ll_lift)
    ll_bot = snap(feet_bottom - foot_h + ll_lift)

    # Left leg column
    draw_rect(draw, ll_cx - leg_w // 2, ll_top, leg_w, leg_h, LEG_SILVER, OUTLINE)
    # Leg details
    draw_rect(draw, ll_cx - leg_w // 2 + PIXEL, ll_top + PIXEL * 2,
              leg_w - 2 * PIXEL, PIXEL, DETAIL_DARK)
    draw_rect(draw, ll_cx - leg_w // 2 + PIXEL, ll_top + leg_h - 3 * PIXEL,
              leg_w - 2 * PIXEL, PIXEL, DETAIL_DARK)
    # Left foot
    draw_rect(draw, ll_cx - foot_w // 2, ll_bot, foot_w, foot_h, FOOT_SILVER, OUTLINE)

    # Right leg
    rl_cx = bcx + leg_spacing
    rl_lift = int(right_lift)
    rl_top = snap(leg_top + rl_lift)
    rl_bot = snap(feet_bottom - foot_h + rl_lift)

    # Right leg column
    draw_rect(draw, rl_cx - leg_w // 2, rl_top, leg_w, leg_h, LEG_SILVER, OUTLINE)
    # Leg details
    draw_rect(draw, rl_cx - leg_w // 2 + PIXEL, rl_top + PIXEL * 2,
              leg_w - 2 * PIXEL, PIXEL, DETAIL_DARK)
    draw_rect(draw, rl_cx - leg_w // 2 + PIXEL, rl_top + leg_h - 3 * PIXEL,
              leg_w - 2 * PIXEL, PIXEL, DETAIL_DARK)
    # Right foot
    draw_rect(draw, rl_cx - foot_w // 2, rl_bot, foot_w, foot_h, FOOT_SILVER, OUTLINE)

    # Centre leg
    cl_top = snap(body_top_anim + body_h - 50)
    draw_rect(draw, bcx - centre_leg_w // 2, cl_top, centre_leg_w, centre_leg_h,
              LEG_DARK, OUTLINE)
    # Centre foot
    cf_top = snap(cl_top + centre_leg_h)
    draw_rect(draw, bcx - centre_foot_w // 2, cf_top, centre_foot_w, centre_foot_h,
              FOOT_SILVER, OUTLINE)

    # === BODY ===
    bx = snap(bcx - body_w // 2)
    by = snap(body_top_anim)

    # Main body rectangle
    draw_rect(draw, bx, by, body_w, body_h, WHITE_BODY, OUTLINE)

    # Rounded shoulders — cut corners
    corner_size = 2 * PIXEL
    for i in range(corner_size // PIXEL):
        cut = (corner_size - i * PIXEL)
        # Top-left corner
        draw.rectangle([bx, by + i * PIXEL, bx + cut - 1, by + (i + 1) * PIXEL - 1],
                        fill=(0, 0, 0, 0))
        # Top-right corner
        draw.rectangle([bx + body_w - cut, by + i * PIXEL,
                         bx + body_w - 1, by + (i + 1) * PIXEL - 1],
                        fill=(0, 0, 0, 0))

    # Blue front panel (large)
    panel_w = 176
    panel_h = 126
    px = snap(bcx - panel_w // 2)
    py = snap(by + 76)
    draw_rect(draw, px, py, panel_w, panel_h, BLUE_PANEL)
    # Panel border lines
    draw_rect(draw, px, py, panel_w, PIXEL, DETAIL_DARK)
    draw_rect(draw, px, py + panel_h - PIXEL, panel_w, PIXEL, DETAIL_DARK)
    draw_rect(draw, px, py, PIXEL, panel_h, DETAIL_DARK)
    draw_rect(draw, px + panel_w - PIXEL, py, PIXEL, panel_h, DETAIL_DARK)

    # Inner panel detail — lighter blue rectangle
    draw_rect(draw, px + 2 * PIXEL, py + 2 * PIXEL,
              panel_w - 4 * PIXEL, panel_h - 4 * PIXEL, BLUE_PANEL_LIGHT)

    # Lower blue accent bars
    for i, yoff in enumerate([226, 252]):
        apw = 100 if i == 0 else 126
        draw_rect(draw, snap(bcx - apw // 2), snap(by + yoff), apw, PIXEL, BLUE_PANEL)

    # Side utility panels (small blue squares on each side of body)
    for side in [-1, 1]:
        sp_x = snap(bcx + side * (body_w // 2 - 3 * PIXEL))
        draw_rect(draw, sp_x, snap(by + 100), 2 * PIXEL, 2 * PIXEL, BLUE_PANEL)
        draw_rect(draw, sp_x, snap(by + 176), 2 * PIXEL, PIXEL, DETAIL_DARK)

    # Vent lines
    for yoff in [214, 282]:
        for xoff in range(-76, 77, PIXEL):
            draw.rectangle(
                [snap(bcx + xoff), snap(by + yoff),
                 snap(bcx + xoff) + PIXEL - 1, snap(by + yoff) + 3],
                fill=DETAIL_DARK,
            )

    # === DOME ===
    dome_base_y = snap(by)
    dome_cx = bcx + int(dome_wobble * 1.2)

    # Draw dome as stacked pixel rows
    for row in range(dome_h // PIXEL):
        ry = dome_base_y - (row + 1) * PIXEL
        frac = (row + 0.5) / (dome_h / PIXEL)
        # Elliptical width
        row_half_w = int((dome_w / 2) * math.sqrt(max(0, 1 - (frac * 0.95) ** 2)))
        if row_half_w < PIXEL:
            row_half_w = PIXEL

        # Gradient from silver to highlight at top
        t = min(1.0, frac * 1.2)
        row_colour = (
            int(DOME_SILVER[0] + (DOME_HIGHLIGHT[0] - DOME_SILVER[0]) * t),
            int(DOME_SILVER[1] + (DOME_HIGHLIGHT[1] - DOME_SILVER[1]) * t),
            int(DOME_SILVER[2] + (DOME_HIGHLIGHT[2] - DOME_SILVER[2]) * t),
        )

        for px_off in range(-row_half_w, row_half_w + 1, PIXEL):
            bx2 = snap(dome_cx + px_off)
            by2 = snap(ry)
            draw.rectangle([bx2, by2, bx2 + PIXEL - 1, by2 + PIXEL - 1], fill=row_colour)

        # Outline pixels on edges
        for side_px in [-row_half_w, row_half_w]:
            ox = snap(dome_cx + side_px)
            oy = snap(ry)
            draw.rectangle([ox, oy, ox + PIXEL - 1, oy + PIXEL - 1], fill=OUTLINE)

    # Dome blue band (two rows for thickness)
    for band_row in range(2):
        band_y = snap(dome_base_y - dome_h * 0.32 - band_row * PIXEL)
        # Get the dome width at this height
        band_frac = (dome_h * 0.32 + band_row * PIXEL) / dome_h
        band_half_w = int((dome_w / 2) * math.sqrt(max(0, 1 - (band_frac * 0.95) ** 2)))
        band_half_w = min(band_half_w, int(dome_w * 0.45))
        for px_off in range(-band_half_w, band_half_w + 1, PIXEL):
            bx2 = snap(dome_cx + px_off)
            draw.rectangle([bx2, band_y, bx2 + PIXEL - 1, band_y + PIXEL - 1],
                           fill=BLUE_PANEL)

    # === EYE / LENS ===
    eye_y = snap(dome_base_y - dome_h * 0.55)
    eye_x = snap(dome_cx + int(dome_wobble * 0.8))
    eye_size = 3 * PIXEL

    # Eye housing
    draw_rect(draw, eye_x - eye_size // 2, eye_y - PIXEL, eye_size, 2 * PIXEL, (40, 40, 50))
    # Red lens (centre)
    draw_rect(draw, eye_x - PIXEL // 2, eye_y - PIXEL // 2, PIXEL, PIXEL, EYE_RED)
    # Lens highlight
    draw.rectangle(
        [eye_x - PIXEL // 2 + 4, eye_y - PIXEL // 2 + 2,
         eye_x + 2, eye_y - 2],
        fill=EYE_GLOW,
    )

    # Secondary lens (smaller, offset right)
    se_x = snap(dome_cx + 76 + int(dome_wobble * 0.4))
    se_y = snap(dome_base_y - dome_h * 0.42)
    draw_rect(draw, se_x, se_y, PIXEL, PIXEL, (50, 50, 60))

    # Third indicator light (left side)
    tl_x = snap(dome_cx - 64 + int(dome_wobble * 0.4))
    tl_y = snap(dome_base_y - dome_h * 0.38)
    draw_rect(draw, tl_x, tl_y, PIXEL, PIXEL, BLUE_PANEL_LIGHT)

    # Dome top cap (small rectangle at very top)
    cap_y = snap(dome_base_y - dome_h + PIXEL)
    cap_w = 3 * PIXEL
    draw_rect(draw, dome_cx - cap_w // 2, cap_y - PIXEL, cap_w, 2 * PIXEL, DETAIL_DARK)


def generate_frames():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for frame in range(TOTAL_FRAMES):
        img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        drw = ImageDraw.Draw(img)

        draw_r2d2(drw, frame)

        path = os.path.join(OUTPUT_DIR, f"frame_{frame:04d}.png")
        img.save(path, "PNG")

        if frame % 24 == 0:
            print(f"  Frame {frame}/{TOTAL_FRAMES} ({frame / FPS:.1f}s)")

    print(f"Done! {TOTAL_FRAMES} frames saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    generate_frames()
