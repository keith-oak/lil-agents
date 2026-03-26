"""Generate a walking BB-8 pixel art animation as individual PNG frames."""

import math
import os

from PIL import Image, ImageDraw

# --- Config ---
WIDTH, HEIGHT = 1080, 1920
TOTAL_FRAMES = 240
FPS = 24
PIXEL = 20  # pixel block size
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames_bb8")

# Colours
BALL_WHITE = (240, 240, 242)
BALL_ORANGE = (235, 130, 40)
BALL_ORANGE_DARK = (200, 100, 25)
HEAD_WHITE = (235, 235, 240)
HEAD_SILVER = (200, 205, 215)
EYE_BLACK = (30, 30, 35)
EYE_HIGHLIGHT = (80, 80, 90)
OUTLINE = (60, 60, 70)
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
    """Return (body_x_offset, body_y_offset, roll_phase, head_tilt, bounce)."""

    if frame < 72:
        # Idle: gentle sway and wobble
        sway = math.sin(frame * 0.08) * 6
        head_tilt = math.sin(frame * 0.06) * 3
        bounce = math.sin(frame * 0.12) * 2
        roll_phase = math.sin(frame * 0.04) * 0.3  # very subtle roll
        return sway, bounce, roll_phase, head_tilt, 0

    elif frame < 90:
        # Accelerate into rolling
        t = (frame - 72) / 18.0
        ease = t * t * t  # cubic ease in
        roll_speed = 0.15 * ease
        roll_phase = (frame - 72) * roll_speed
        sway = math.sin(frame * 0.12) * 10 * ease
        head_tilt = math.sin(frame * 0.1) * 5 * ease
        bounce = abs(math.sin(frame * 0.18)) * 8 * ease
        return sway, bounce, roll_phase, head_tilt, ease

    elif frame < 192:
        # Full roll
        # Accumulate roll phase from acceleration + full speed
        accel_phase = sum(0.15 * ((f - 72) / 18.0) ** 3 for f in range(72, 90))
        roll_phase = accel_phase + (frame - 90) * 0.15
        sway = math.sin(frame * 0.14) * 14
        head_tilt = math.sin(frame * 0.1 + 0.5) * 5
        bounce = abs(math.sin(frame * 0.22)) * 10
        return sway, bounce, roll_phase, head_tilt, 1.0

    elif frame < 204:
        # Decelerate
        t = 1.0 - (frame - 192) / 12.0
        ease = t * t
        accel_phase = sum(0.15 * ((f - 72) / 18.0) ** 3 for f in range(72, 90))
        full_phase = accel_phase + (192 - 90) * 0.15
        roll_phase = full_phase + (frame - 192) * 0.15 * ease
        sway = math.sin(frame * 0.12) * 10 * ease
        head_tilt = math.sin(frame * 0.1) * 4 * ease
        bounce = abs(math.sin(frame * 0.18)) * 8 * ease
        return sway, bounce, roll_phase, head_tilt, ease

    else:
        # Return to idle
        t = min(1.0, (frame - 204) / 36.0)
        sway = math.sin(frame * 0.08) * 6 * (1 - t) + math.sin(frame * 0.06) * 3 * t
        head_tilt = math.sin(frame * 0.06) * 3
        bounce = math.sin(frame * 0.1) * 2 * (1 - t)
        roll_phase = math.sin(frame * 0.04) * 0.2 * (1 - t)
        return sway, bounce, roll_phase, head_tilt, 0


def draw_bb8(draw, frame):
    """Draw BB-8 for the given frame number."""
    sway, bounce, roll_phase, head_tilt, intensity = get_animation_params(frame)

    cx = WIDTH // 2
    base_y = 1920  # bottom of canvas

    # --- Dimensions ---
    ball_radius = 220  # radius in pixels of the ball
    ball_diameter = ball_radius * 2
    head_w = 160
    head_h = 100
    neck_gap = 10  # small gap between head and ball top

    # The ball bottom sits at the very bottom of the canvas
    ball_cy = base_y - ball_radius  # centre of the ball
    ball_top = ball_cy - ball_radius

    # Apply animation offsets
    bcx = cx + int(sway)
    bcy = ball_cy - int(bounce)

    # --- Draw shadow on ground ---
    shadow_w = 500 + int(abs(sway) * 0.5)
    shadow_h = 24
    sx = snap(cx - shadow_w // 2 + sway * 0.3)
    sy = snap(base_y - shadow_h)
    draw.rectangle([sx, sy, sx + shadow_w, sy + shadow_h], fill=SHADOW)

    # === BALL (spherical body) ===
    # Draw as stacked pixel rows forming a circle
    # We'll track which pixels are part of the ball for the panel overlay
    ball_pixels = []

    for row in range(ball_diameter // PIXEL + 1):
        py = snap(bcy - ball_radius + row * PIXEL)
        # Distance from centre (normalised -1 to 1)
        dy = (py + PIXEL // 2 - bcy) / ball_radius
        if abs(dy) > 1.0:
            continue

        # Circle width at this row
        row_half_w = int(ball_radius * math.sqrt(1 - dy * dy))
        if row_half_w < PIXEL:
            continue

        for col_off in range(-row_half_w, row_half_w + 1, PIXEL):
            px = snap(bcx + col_off)
            # Check if this pixel is within the circle
            dx = (px + PIXEL // 2 - bcx) / ball_radius
            dist_sq = dx * dx + dy * dy
            if dist_sq > 1.0:
                continue

            ball_pixels.append((px, py, dx, dy))
            draw.rectangle([px, py, px + PIXEL - 1, py + PIXEL - 1], fill=BALL_WHITE)

    # === BALL ORANGE PANELS ===
    # Create the rolling pattern by shifting with roll_phase
    # BB-8 has circular band patterns — we simulate with horizontal bands
    # that shift vertically to create rolling illusion

    roll_offset = roll_phase * ball_radius * 2  # convert phase to pixel offset

    for px, py, dx, dy in ball_pixels:
        # Map to spherical coordinates for panel pattern
        # theta = angle from top (0 at top, pi at bottom)
        theta = math.acos(max(-1, min(1, -dy)))
        # phi = angle around (using dx and a wrap)
        phi = math.atan2(dx, max(0.01, math.sqrt(max(0, 1 - dx * dx - dy * dy))))

        # Shift theta by roll to animate
        theta_shifted = theta + roll_offset * 0.02

        # Create band pattern
        band_val = math.sin(theta_shifted * 4.0)
        cross_val = math.sin(phi * 3.0 + theta_shifted * 2.0)

        is_orange = False

        # Main equatorial band (thick)
        equator_dist = abs(dy)
        if equator_dist < 0.12:
            is_orange = True

        # Upper and lower circular bands
        band_pos = math.sin(theta_shifted * 3.5)
        if abs(band_pos) < 0.18 and abs(dy) > 0.15:
            is_orange = True

        # Circular accent patches
        if abs(band_val) < 0.22 and abs(cross_val) > 0.7:
            is_orange = True

        # Large circular panel near front-top
        panel_dist = math.sqrt((dy + 0.35) ** 2 + dx * dx)
        if panel_dist < 0.25:
            is_orange = True

        # Large circular panel near front-bottom
        panel_dist2 = math.sqrt((dy - 0.4) ** 2 + dx * dx)
        if panel_dist2 < 0.2:
            is_orange = True

        if is_orange:
            # Darken pixels near edges for depth
            edge_factor = math.sqrt(dx * dx + dy * dy)
            if edge_factor > 0.8:
                colour = BALL_ORANGE_DARK
            else:
                colour = BALL_ORANGE
            draw.rectangle([px, py, px + PIXEL - 1, py + PIXEL - 1], fill=colour)

    # === BALL EQUATOR SEAM ===
    seam_y = snap(bcy)
    for col_off in range(-ball_radius, ball_radius + 1, PIXEL):
        px = snap(bcx + col_off)
        dx = col_off / ball_radius
        if abs(dx) > 0.95:
            continue
        row_half_w = ball_radius * math.sqrt(1 - dx * dx)
        if abs(col_off) <= row_half_w:
            draw.rectangle([px, seam_y, px + PIXEL - 1, seam_y + 1], fill=OUTLINE)

    # === BALL OUTLINE ===
    # Draw outline pixels at the edge of the circle
    for row in range(ball_diameter // PIXEL + 2):
        py = snap(bcy - ball_radius + row * PIXEL)
        dy = (py + PIXEL // 2 - bcy) / ball_radius
        if abs(dy) > 1.0:
            continue

        row_half_w = int(ball_radius * math.sqrt(1 - dy * dy))
        # Left and right edge outlines
        for side in [-1, 1]:
            ox = snap(bcx + side * row_half_w)
            # Verify it's roughly on the circle edge
            if row_half_w >= PIXEL:
                draw.rectangle([ox, py, ox + PIXEL - 1, py + PIXEL - 1], fill=OUTLINE)

    # Top and bottom outline rows
    for is_top in [True, False]:
        oy = snap(bcy - ball_radius) if is_top else snap(bcy + ball_radius - PIXEL)
        dy = -1.0 if is_top else 1.0
        # Only draw a few pixels at the very top/bottom
        for col_off in range(-3 * PIXEL, 4 * PIXEL, PIXEL):
            px = snap(bcx + col_off)
            draw.rectangle([px, oy, px + PIXEL - 1, oy + PIXEL - 1], fill=OUTLINE)

    # === HEAD (dome) ===
    head_base_y = snap(bcy - ball_radius - neck_gap)
    head_cx = bcx + int(head_tilt * 1.5)

    # Draw head dome as stacked pixel rows (half-ellipse)
    for row in range(head_h // PIXEL + 1):
        hy = snap(head_base_y - row * PIXEL)
        frac = row / (head_h / PIXEL)

        # Elliptical width — wider at base, narrow at top
        row_half_w = int((head_w / 2) * math.sqrt(max(0, 1 - frac * frac)))
        if row_half_w < PIXEL:
            row_half_w = PIXEL

        # Gradient from silver at base to white at top
        t = min(1.0, frac * 1.3)
        row_colour = (
            int(HEAD_SILVER[0] + (HEAD_WHITE[0] - HEAD_SILVER[0]) * t),
            int(HEAD_SILVER[1] + (HEAD_WHITE[1] - HEAD_SILVER[1]) * t),
            int(HEAD_SILVER[2] + (HEAD_WHITE[2] - HEAD_SILVER[2]) * t),
        )

        for px_off in range(-row_half_w, row_half_w + 1, PIXEL):
            hx = snap(head_cx + px_off)
            draw.rectangle([hx, hy, hx + PIXEL - 1, hy + PIXEL - 1], fill=row_colour)

        # Outline on edges
        for side_px in [-row_half_w, row_half_w]:
            ox = snap(head_cx + side_px)
            draw.rectangle([ox, hy, ox + PIXEL - 1, hy + PIXEL - 1], fill=OUTLINE)

    # Head bottom outline
    for px_off in range(-head_w // 2, head_w // 2 + 1, PIXEL):
        hx = snap(head_cx + px_off)
        draw.rectangle([hx, head_base_y, hx + PIXEL - 1, head_base_y + PIXEL - 1],
                       fill=OUTLINE)

    # Head top outline (thin cap)
    top_y = snap(head_base_y - head_h + PIXEL)
    for px_off in range(-2 * PIXEL, 3 * PIXEL, PIXEL):
        hx = snap(head_cx + px_off)
        draw.rectangle([hx, top_y, hx + PIXEL - 1, top_y + PIXEL - 1], fill=OUTLINE)

    # === HEAD ORANGE BAND ===
    band_y = snap(head_base_y - head_h * 0.35)
    band_frac = 0.35
    band_half_w = int((head_w / 2) * math.sqrt(max(0, 1 - band_frac * band_frac)))
    for band_row in range(2):
        by = snap(band_y - band_row * PIXEL)
        for px_off in range(-band_half_w, band_half_w + 1, PIXEL):
            hx = snap(head_cx + px_off)
            draw.rectangle([hx, by, hx + PIXEL - 1, by + PIXEL - 1], fill=BALL_ORANGE)

    # === EYE / LENS ===
    eye_y = snap(head_base_y - head_h * 0.55)
    eye_x = snap(head_cx - PIXEL + int(head_tilt * 0.6))
    eye_size = 3 * PIXEL

    # Eye housing (dark circle)
    for er in range(-1, 2):
        for ec in range(-1, 2):
            if er * er + ec * ec <= 1:
                ex = snap(eye_x + ec * PIXEL)
                ey = snap(eye_y + er * PIXEL)
                draw.rectangle([ex, ey, ex + PIXEL - 1, ey + PIXEL - 1], fill=EYE_BLACK)

    # Eye lens centre (slightly lighter)
    draw.rectangle([eye_x, eye_y, eye_x + PIXEL - 1, eye_y + PIXEL - 1],
                   fill=EYE_HIGHLIGHT)

    # Small highlight dot
    draw.rectangle([eye_x + 2, eye_y + 2, eye_x + 6, eye_y + 6],
                   fill=(120, 120, 130))

    # === ANTENNA (small nub on top of head) ===
    ant_x = snap(head_cx + 2 * PIXEL)
    ant_base = snap(head_base_y - head_h + 2 * PIXEL)
    draw_rect(draw, ant_x, ant_base - 3 * PIXEL, PIXEL, 3 * PIXEL, HEAD_SILVER)
    # Antenna tip
    draw.rectangle([ant_x, ant_base - 3 * PIXEL,
                    ant_x + PIXEL - 1, ant_base - 3 * PIXEL + PIXEL - 1],
                   fill=OUTLINE)


def generate_frames():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for frame in range(TOTAL_FRAMES):
        img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        drw = ImageDraw.Draw(img)

        draw_bb8(drw, frame)

        path = os.path.join(OUTPUT_DIR, f"frame_{frame:04d}.png")
        img.save(path, "PNG")

        if frame % 24 == 0:
            print(f"  Frame {frame}/{TOTAL_FRAMES} ({frame / FPS:.1f}s)")

    print(f"Done! {TOTAL_FRAMES} frames saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    generate_frames()
