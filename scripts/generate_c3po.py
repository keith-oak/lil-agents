"""Generate a walking C-3PO pixel art animation as individual PNG frames."""

import math
import os

from PIL import Image, ImageDraw

# --- Config ---
WIDTH, HEIGHT = 1080, 1920
TOTAL_FRAMES = 240
FPS = 24
PIXEL = 18  # pixel block size
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames_c3po")

# Colours (gold/brass palette)
GOLD_MAIN = (210, 175, 55)
GOLD_LIGHT = (235, 205, 95)
GOLD_DARK = (165, 130, 35)
EYE_AMBER = (255, 200, 50)
JOINT_DARK = (120, 95, 30)
MOUTH_DARK = (100, 80, 25)
OUTLINE = (80, 65, 20)
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


def draw_ellipse(draw, cx, cy, rx, ry, colour):
    """Draw an ellipse centred at (cx, cy) with radii rx, ry."""
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=colour)


def get_animation_params(frame):
    """Return animation parameters for C-3PO's stiff walking style.

    Returns: (body_x_offset, body_y_offset, left_leg_angle, right_leg_angle,
              left_arm_angle, right_arm_angle, head_tilt, torso_twist)
    """
    if frame < 93:
        # Idle: subtle swaying/breathing
        breathe = math.sin(frame * 0.08) * 3
        sway = math.sin(frame * 0.05) * 2
        return sway, breathe, 0, 0, 0, 0, math.sin(frame * 0.04) * 1.5, 0

    elif frame < 108:
        # Start walking — stiff shuffle begins
        t = (frame - 93) / 15.0
        ease = t * t  # quadratic ease in
        cycle = (frame - 93) * 0.25
        sc = math.sin(cycle)

        leg_amp = 18 * ease
        arm_amp = 10 * ease
        body_bob = -abs(sc) * 6 * ease
        body_sway = sc * 8 * ease

        return (
            body_sway,
            body_bob,
            sc * leg_amp,        # left leg
            -sc * leg_amp,       # right leg (opposite)
            -sc * arm_amp,       # left arm (opposite to left leg)
            sc * arm_amp,        # right arm (opposite to right leg)
            math.sin(frame * 0.06) * 1.5,
            sc * 3 * ease,       # torso twist
        )

    elif frame < 192:
        # Full walk cycle — classic C-3PO stiff-legged walk
        cycle = (frame - 108) * 0.18
        sc = math.sin(cycle)

        leg_amp = 22
        arm_amp = 14
        body_bob = -abs(sc) * 8
        body_sway = sc * 12

        return (
            body_sway,
            body_bob,
            sc * leg_amp,
            -sc * leg_amp,
            -sc * arm_amp,
            sc * arm_amp,
            math.sin(frame * 0.06) * 1.0,
            sc * 4,
        )

    elif frame < 210:
        # Decelerate
        t = 1.0 - (frame - 192) / 18.0
        ease = t * t
        cycle = (frame - 192) * 0.18
        sc = math.sin(cycle)

        leg_amp = 22 * ease
        arm_amp = 14 * ease
        body_bob = -abs(sc) * 8 * ease
        body_sway = sc * 12 * ease

        return (
            body_sway,
            body_bob,
            sc * leg_amp,
            -sc * leg_amp,
            -sc * arm_amp,
            sc * arm_amp,
            math.sin(frame * 0.06) * 1.5 * ease,
            sc * 4 * ease,
        )

    else:
        # Return to idle
        t = min(1.0, (frame - 210) / 30.0)
        breathe = math.sin(frame * 0.08) * 3
        sway = math.sin(frame * 0.05) * 2 * t
        return sway, breathe, 0, 0, 0, 0, math.sin(frame * 0.04) * 1.5 * t, 0


def draw_c3po(draw, frame):
    """Draw C-3PO for the given frame number."""
    (body_x_off, body_y_off, left_leg_ang, right_leg_ang,
     left_arm_ang, right_arm_ang, head_tilt, torso_twist) = get_animation_params(frame)

    cx = WIDTH // 2
    base_y = HEIGHT  # feet at the very bottom of the canvas (y=1920)

    # --- Character dimensions (scaled up ~1.56x for ~900px tall) ---
    head_w = 218
    head_h = 203
    neck_w = 94
    neck_h = 78
    torso_w = 312
    torso_h = 312
    upper_arm_w = 78
    upper_arm_h = 203
    lower_arm_w = 70
    lower_arm_h = 187
    upper_leg_w = 94
    upper_leg_h = 218
    lower_leg_w = 86
    lower_leg_h = 203
    foot_w = 125
    foot_h = 56
    hip_spacing = 86
    shoulder_spacing = 172

    # Character total height ~900px
    total_h = head_h + neck_h + torso_h + upper_leg_h + lower_leg_h + foot_h - 94
    _ = total_h  # ~903px

    # Key Y positions (from bottom up)
    feet_y = base_y
    lower_leg_top = feet_y - foot_h - lower_leg_h
    upper_leg_top = lower_leg_top - upper_leg_h + 20  # overlap at knee
    torso_top = upper_leg_top - torso_h + 30  # overlap at hips
    neck_top = torso_top - neck_h + 15
    head_top = neck_top - head_h + 15

    # Apply offsets
    bcx = cx + int(body_x_off)
    body_y_shift = int(body_y_off)

    # --- Draw shadow ---
    shadow_w = 280 + int(abs(body_x_off) * 0.5)
    shadow_h = 18
    sx = snap(cx - shadow_w // 2 + body_x_off * 0.3)
    sy = snap(base_y + 8)
    draw.rectangle([sx, sy, sx + shadow_w, sy + shadow_h], fill=SHADOW)

    # === LEGS ===
    for side in [-1, 1]:
        if side == -1:
            leg_ang = left_leg_ang
        else:
            leg_ang = right_leg_ang

        hip_x = bcx + side * hip_spacing

        # Upper leg
        leg_offset_x = math.sin(math.radians(leg_ang)) * upper_leg_h * 0.3
        leg_offset_y = (1 - math.cos(math.radians(leg_ang))) * 8

        ul_x = snap(hip_x - upper_leg_w // 2 + leg_offset_x * 0.5)
        ul_y = snap(upper_leg_top + body_y_shift + leg_offset_y)

        # Upper leg
        draw_rect(draw, ul_x, ul_y, upper_leg_w, upper_leg_h, GOLD_MAIN, OUTLINE)
        # Upper leg highlight
        draw_rect(draw, ul_x + PIXEL, ul_y + PIXEL, upper_leg_w - 3 * PIXEL,
                  upper_leg_h - 2 * PIXEL, GOLD_LIGHT)
        # Upper leg shadow strip
        draw_rect(draw, ul_x + upper_leg_w - 2 * PIXEL, ul_y + PIXEL,
                  PIXEL, upper_leg_h - 2 * PIXEL, GOLD_DARK)

        # Knee joint
        knee_y = snap(ul_y + upper_leg_h - PIXEL)
        knee_x = snap(hip_x - upper_leg_w // 2 + leg_offset_x * 0.7)
        draw_rect(draw, knee_x - PIXEL, knee_y, upper_leg_w + 2 * PIXEL,
                  3 * PIXEL, JOINT_DARK, OUTLINE)

        # Lower leg
        ll_offset_x = leg_offset_x * 0.9
        ll_x = snap(hip_x - lower_leg_w // 2 + ll_offset_x)
        ll_y = snap(lower_leg_top + body_y_shift + leg_offset_y)
        draw_rect(draw, ll_x, ll_y, lower_leg_w, lower_leg_h, GOLD_MAIN, OUTLINE)
        # Lower leg highlight
        draw_rect(draw, ll_x + PIXEL, ll_y + PIXEL, lower_leg_w - 3 * PIXEL,
                  lower_leg_h - 2 * PIXEL, GOLD_LIGHT)
        # Piston detail on lower leg
        draw_rect(draw, ll_x + PIXEL, ll_y + lower_leg_h // 2,
                  PIXEL, lower_leg_h // 3, JOINT_DARK)

        # Ankle joint
        ankle_y = snap(ll_y + lower_leg_h - PIXEL)
        draw_rect(draw, ll_x - PIXEL // 2, ankle_y, lower_leg_w + PIXEL,
                  2 * PIXEL, JOINT_DARK, OUTLINE)

        # Foot
        foot_x = snap(hip_x - foot_w // 2 + ll_offset_x * 1.1)
        foot_y_pos = snap(feet_y - foot_h + leg_offset_y * 0.3)
        # Foot lifts during walk
        foot_lift = max(0, abs(leg_ang) * 0.8)
        foot_y_pos = snap(foot_y_pos - foot_lift)
        draw_rect(draw, foot_x, foot_y_pos, foot_w, foot_h, GOLD_DARK, OUTLINE)
        # Foot top highlight
        draw_rect(draw, foot_x + PIXEL, foot_y_pos, foot_w - 2 * PIXEL, PIXEL, GOLD_MAIN)

    # === TORSO ===
    twist_offset = int(torso_twist)
    tx = snap(bcx - torso_w // 2 + twist_offset)
    ty = snap(torso_top + body_y_shift)

    # Main torso
    draw_rect(draw, tx, ty, torso_w, torso_h, GOLD_MAIN, OUTLINE)

    # Torso highlight (left side in light)
    draw_rect(draw, tx + PIXEL, ty + PIXEL, torso_w // 2 - PIXEL,
              torso_h - 2 * PIXEL, GOLD_LIGHT)

    # Torso shadow (right side)
    draw_rect(draw, tx + torso_w // 2, ty + PIXEL, torso_w // 2 - PIXEL,
              torso_h - 2 * PIXEL, GOLD_DARK)

    # Chest plate (central rectangle, slightly darker)
    cp_w = 120
    cp_h = 80
    cp_x = snap(bcx - cp_w // 2 + twist_offset)
    cp_y = snap(ty + 30)
    draw_rect(draw, cp_x, cp_y, cp_w, cp_h, GOLD_MAIN, OUTLINE)
    # Chest plate panel lines
    draw_rect(draw, cp_x + 2 * PIXEL, cp_y + PIXEL, cp_w - 4 * PIXEL, PIXEL, JOINT_DARK)
    draw_rect(draw, cp_x + 2 * PIXEL, cp_y + cp_h - 2 * PIXEL,
              cp_w - 4 * PIXEL, PIXEL, JOINT_DARK)
    # Centre vertical line
    draw_rect(draw, snap(bcx - PIXEL // 2 + twist_offset), cp_y + PIXEL,
              PIXEL, cp_h - 2 * PIXEL, JOINT_DARK)

    # Abdominal section (horizontal panel lines below chest plate)
    for i in range(3):
        ab_y = snap(cp_y + cp_h + 15 + i * (2 * PIXEL + 4))
        ab_w = torso_w - 4 * PIXEL
        draw_rect(draw, snap(bcx - ab_w // 2 + twist_offset), ab_y, ab_w, PIXEL, JOINT_DARK)

    # Hip/waist band
    waist_y = snap(ty + torso_h - 2 * PIXEL)
    draw_rect(draw, tx - PIXEL, waist_y, torso_w + 2 * PIXEL, 3 * PIXEL, GOLD_DARK, OUTLINE)

    # === ARMS ===
    for side in [-1, 1]:
        if side == -1:
            arm_ang = left_arm_ang
        else:
            arm_ang = right_arm_ang

        shoulder_x = bcx + side * shoulder_spacing + twist_offset * (0.5 if side == 1 else -0.5)
        shoulder_y = ty + 15

        # Shoulder joint
        sj_x = snap(shoulder_x - 2 * PIXEL)
        sj_y = snap(shoulder_y)
        draw_rect(draw, sj_x, sj_y, 4 * PIXEL, 3 * PIXEL, JOINT_DARK, OUTLINE)

        # Upper arm
        arm_swing_x = math.sin(math.radians(arm_ang)) * upper_arm_h * 0.25
        ua_x = snap(shoulder_x - upper_arm_w // 2 + arm_swing_x * 0.3)
        ua_y = snap(shoulder_y + 3 * PIXEL)
        draw_rect(draw, ua_x, ua_y, upper_arm_w, upper_arm_h, GOLD_MAIN, OUTLINE)
        # Arm highlight
        hl_x = ua_x + PIXEL if side == -1 else ua_x + upper_arm_w - 2 * PIXEL
        draw_rect(draw, hl_x, ua_y + PIXEL, PIXEL, upper_arm_h - 2 * PIXEL, GOLD_LIGHT)

        # Elbow joint
        elbow_x = snap(shoulder_x - upper_arm_w // 2 + arm_swing_x * 0.5)
        elbow_y = snap(ua_y + upper_arm_h)
        draw_rect(draw, elbow_x - PIXEL, elbow_y, upper_arm_w + 2 * PIXEL,
                  3 * PIXEL, JOINT_DARK, OUTLINE)

        # Lower arm (slightly bent outward in idle)
        la_bend = side * 5 + arm_swing_x * 0.7
        la_x = snap(shoulder_x - lower_arm_w // 2 + la_bend)
        la_y = snap(elbow_y + 3 * PIXEL)
        draw_rect(draw, la_x, la_y, lower_arm_w, lower_arm_h, GOLD_MAIN, OUTLINE)
        # Lower arm highlight
        hl2_x = la_x + PIXEL if side == -1 else la_x + lower_arm_w - 2 * PIXEL
        draw_rect(draw, hl2_x, la_y + PIXEL, PIXEL, lower_arm_h - 2 * PIXEL, GOLD_LIGHT)

        # Wrist joint
        wrist_y = snap(la_y + lower_arm_h)
        draw_rect(draw, la_x, wrist_y, lower_arm_w, 2 * PIXEL, JOINT_DARK, OUTLINE)

        # Hand (simple block)
        hand_w = lower_arm_w - PIXEL
        hand_h = 3 * PIXEL
        hand_x = snap(shoulder_x - hand_w // 2 + la_bend)
        hand_y = snap(wrist_y + 2 * PIXEL)
        draw_rect(draw, hand_x, hand_y, hand_w, hand_h, GOLD_DARK, OUTLINE)

    # === NECK ===
    nx = snap(bcx - neck_w // 2 + twist_offset * 0.3)
    ny = snap(neck_top + body_y_shift)
    draw_rect(draw, nx, ny, neck_w, neck_h, GOLD_DARK, OUTLINE)
    # Neck segments (horizontal lines)
    for i in range(3):
        seg_y = snap(ny + PIXEL + i * (PIXEL + 4))
        draw_rect(draw, nx + PIXEL, seg_y, neck_w - 2 * PIXEL, PIXEL // 2, JOINT_DARK)
    # Neck highlight
    draw_rect(draw, nx + PIXEL, ny + PIXEL, PIXEL, neck_h - 2 * PIXEL, GOLD_MAIN)

    # === HEAD ===
    ht = int(head_tilt)
    hx = snap(bcx - head_w // 2 + ht + twist_offset * 0.15)
    hy = snap(head_top + body_y_shift)

    # Main head shape (round-ish rectangle)
    draw_rect(draw, hx, hy, head_w, head_h, GOLD_MAIN, OUTLINE)

    # Round the top corners
    corner = 2 * PIXEL
    for i in range(corner // PIXEL):
        cut = corner - i * PIXEL
        # Top-left
        draw.rectangle([hx, hy + i * PIXEL, hx + cut - 1, hy + (i + 1) * PIXEL - 1],
                       fill=(0, 0, 0, 0))
        # Top-right
        draw.rectangle([hx + head_w - cut, hy + i * PIXEL,
                        hx + head_w - 1, hy + (i + 1) * PIXEL - 1],
                       fill=(0, 0, 0, 0))

    # Head highlight (left)
    draw_rect(draw, hx + 2 * PIXEL, hy + 2 * PIXEL,
              head_w // 2 - 2 * PIXEL, head_h - 4 * PIXEL, GOLD_LIGHT)

    # Head shadow (right)
    draw_rect(draw, hx + head_w // 2, hy + 2 * PIXEL,
              head_w // 2 - 2 * PIXEL, head_h - 4 * PIXEL, GOLD_DARK)

    # Eyes (two circular amber shapes)
    eye_y = snap(hy + head_h * 0.3)
    eye_spacing = 30
    eye_r = 2 * PIXEL

    for side in [-1, 1]:
        ex = snap(bcx + side * eye_spacing + ht + twist_offset * 0.15)
        ey = eye_y
        # Eye socket (dark circle)
        draw_ellipse(draw, ex + eye_r // 2, ey + eye_r // 2,
                     eye_r + 2, eye_r + 2, MOUTH_DARK)
        # Amber eye
        draw_ellipse(draw, ex + eye_r // 2, ey + eye_r // 2,
                     eye_r - 2, eye_r - 2, EYE_AMBER)
        # Eye highlight
        draw_ellipse(draw, ex + eye_r // 2 - 4, ey + eye_r // 2 - 4,
                     4, 4, (255, 240, 150))

    # Mouth (vertical slit with horizontal lines)
    mouth_x = snap(bcx - PIXEL + ht + twist_offset * 0.15)
    mouth_y = snap(hy + head_h * 0.6)
    mouth_w = 2 * PIXEL
    mouth_h = 4 * PIXEL
    draw_rect(draw, mouth_x, mouth_y, mouth_w, mouth_h, MOUTH_DARK, OUTLINE)
    # Horizontal slits across mouth
    for i in range(3):
        slit_y = snap(mouth_y + PIXEL * (i + 0.5))
        draw_rect(draw, mouth_x, slit_y, mouth_w, 2, JOINT_DARK)

    # Forehead plate detail
    fp_y = snap(hy + 3 * PIXEL)
    fp_w = head_w - 6 * PIXEL
    draw_rect(draw, snap(bcx - fp_w // 2 + ht), fp_y, fp_w, PIXEL, JOINT_DARK)

    # Head crest / ridge on top
    crest_w = head_w - 4 * PIXEL
    crest_y = snap(hy + PIXEL)
    draw_rect(draw, snap(bcx - crest_w // 2 + ht), crest_y, crest_w, PIXEL, GOLD_DARK)

    # Ear pieces (side of head)
    for side in [-1, 1]:
        ear_x = snap(hx + (head_w if side == 1 else -2 * PIXEL))
        ear_y = snap(hy + head_h * 0.25)
        draw_rect(draw, ear_x, ear_y, 2 * PIXEL, 5 * PIXEL, GOLD_DARK, OUTLINE)
        # Ear detail
        draw_rect(draw, ear_x + PIXEL // 2, ear_y + PIXEL, PIXEL, 3 * PIXEL, JOINT_DARK)


def generate_frames():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for frame in range(TOTAL_FRAMES):
        img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        drw = ImageDraw.Draw(img)

        draw_c3po(drw, frame)

        path = os.path.join(OUTPUT_DIR, f"frame_{frame:04d}.png")
        img.save(path, "PNG")

        if frame % 24 == 0:
            print(f"  Frame {frame}/{TOTAL_FRAMES} ({frame / FPS:.1f}s)")

    print(f"Done! {TOTAL_FRAMES} frames saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    generate_frames()
