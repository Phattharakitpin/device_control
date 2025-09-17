import cv2, math, numpy as np
from ultralytics import YOLO

# =============== Config ===============

VIDEO = "congratulation.mp4"
MODEL = "yolo11n-pose.pt"

# Focus ROI (ratios 0..1) — ปรับให้ครอบตำแหน่งเข้ารับตามภาพตัวอย่าง
ROI_LEFT, ROI_RIGHT  = 0.35, 0.55   # แกน X (ซ้าย→ขวา)
ROI_TOP,  ROI_BOTTOM = 0.20, 0.98   # แกน Y (บน→ล่าง)

# Angle pass ranges (degrees) — ช่วงที่ถือว่าเหมาะสม
RANGE_ARM  = (160, 185)
RANGE_BACK = (165, 185)
RANGE_KNEE = (160, 185)

# Visualization colors (BGR)
C_SKEL = (30, 200, 255)
C_OK   = (0, 220, 0)
C_BAD  = (0, 0, 255)
C_INFO = (255, 255, 255)

# Thai text support (optional)
USE_THAI = True
FONT_PATH = "NotoSansThai-Regular.ttf"   # วางไฟล์ฟอนต์ไทยในโฟลเดอร์นี้
FONT_SIZE = 26

# =============== Text Helper (Thai-aware) ===============
try:
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
    THAI_FONT = ImageFont.truetype(FONT_PATH, FONT_SIZE) if USE_THAI else None
except Exception:
    THAI_FONT = None

def put_text(img, text_th, text_en, org, color=C_INFO, size=FONT_SIZE):
    """วาดข้อความไทยถ้ามีฟอนต์ ไม่งั้นใช้ cv2.putText(อังกฤษ)"""
    text = text_th if THAI_FONT else text_en
    if THAI_FONT:
        # Pillow expects RGB
        from PIL import Image, ImageDraw
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb)
        draw = ImageDraw.Draw(pil)
        b,g,r = color  # convert BGR->RGB
        draw.text(org, text, font=THAI_FONT.font_variant(size=size), fill=(r,g,b))
        return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    else:
        cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        return img

# =============== Geometry Helpers ===============
def angle(a, b, c):
    """Angle ABC in degrees"""
    if a is None or b is None or c is None: return None
    ax,ay=a; bx,by=b; cx,cy=c
    ba=(ax-bx, ay-by); bc=(cx-bx, cy-by)
    nba, nbc = math.hypot(*ba), math.hypot(*bc)
    if nba==0 or nbc==0: return None
    cosv = max(-1.0, min(1.0, (ba[0]*bc[0]+ba[1]*bc[1])/(nba*nbc)))
    return math.degrees(math.acos(cosv))

def kp_list(kp, conf_th=0.25):
    """(17,3) -> list[(x,y) or None]"""
    return [(int(x),int(y)) if c>conf_th else None for x,y,c in kp]

# COCO17 connections for a clean skeleton
CONNS = [(5,7),(7,9),(6,8),(8,10),(5,6),(5,11),(6,12),(11,12),(11,13),(13,15),(12,14),(14,16)]

# =============== Main ===============
def main():
    model = YOLO(MODEL)
    cap = cv2.VideoCapture(VIDEO)
    if not cap.isOpened():
        print("Cannot open video:", VIDEO); return

    while True:
        ok, frame = cap.read()
        if not ok: break
        H,W,_ = frame.shape

        # Compute ROI in pixels
        x1, x2 = int(W*ROI_LEFT),  int(W*ROI_RIGHT)
        y1, y2 = int(H*ROI_TOP),   int(H*ROI_BOTTOM)
        roi = frame[y1:y2, x1:x2]

        # Dim outside ROI
        overlay = frame.copy()
        cv2.rectangle(overlay, (0,0), (W,H), (0,0,0), -1)
        overlay[y1:y2, x1:x2] = frame[y1:y2, x1:x2]
        frame = cv2.addWeighted(overlay, 0.35, frame, 0.65, 0)

        # Inference on ROI (tune conf/iou for robustness)
        r = model(roi, verbose=False, conf=0.25, iou=0.5)[0]

        # Guard: no detections
        if r.keypoints is None or len(r.keypoints)==0 or r.boxes is None or len(r.boxes)==0:
            msg_th = "ไม่มีคนในโซนโฟกัส"
            msg_en = "No person in focus ROI"
            #frame = put_text(frame, msg_th, msg_en, (x1+10, y1+30), C_INFO)
            cv2.imshow("Focus Pose @ Receiving", frame)
            if cv2.waitKey(1) & 0xFF == 27: break
            continue

        # Choose target person (left-most center among tall-enough boxes)
        kps   = r.keypoints.data.cpu().numpy()   # [N,17,3]
        boxes = r.boxes.xyxy.cpu().numpy()       # [N,4]
        roi_h = roi.shape[0]

        cands=[]
        for i,(xA,yA,xB,yB) in enumerate(boxes):
            h_box = yB - yA
            cx    = (xA + xB) / 2.0
            cands.append((i, cx, h_box))

        valid = [t for t in cands if t[2] >= 0.35*roi_h]
        pool  = valid if valid else cands
        if not pool:
            frame = put_text(frame, "ไม่พบโครงร่าง", "No keypoints", (x1+10, y1+30), C_INFO)
            cv2.imshow("Focus Pose @ Receiving", frame)
            if cv2.waitKey(1) & 0xFF == 27: break
            continue

        target_idx = min(pool, key=lambda t: t[1])[0]   # left-most center
        kp = kps[target_idx]

        # Convert keypoints to full-frame coords
        pts = kp_list(kp, conf_th=0.20)
        pts = [(p[0]+x1, p[1]+y1) if p else None for p in pts]

        # Draw skeleton (no boxes)
        for a,b in CONNS:
            if pts[a] and pts[b]:
                cv2.line(frame, pts[a], pts[b], C_SKEL, 1)
        for p in pts:
            if p: cv2.circle(frame, p, 3, C_SKEL, -1)

        # Right-side joints
        R_sh, R_el, R_wr = 6,8,10
        R_hp, R_kn, R_an = 12,14,16

        arm  = angle(pts[R_sh], pts[R_el], pts[R_wr])     # shoulder–elbow–wrist
        back = angle(pts[R_sh], pts[R_hp], pts[R_kn])     # shoulder–hip–knee
        knee = angle(pts[R_hp], pts[R_kn], pts[R_an])     # hip–knee–ankle

        # Toe tip ≈ ankle + α*(ankle - knee)
        toe = None
        if pts[R_an]:
            ax,ay = pts[R_an]
            if pts[R_kn]:
                kx,ky = pts[R_kn]
                alpha=0.30
                toe = (int(ax + alpha*(ax-kx)), int(ay + alpha*(ay-ky)))
            else:
                toe = (ax,ay)
            cv2.circle(frame, toe, 3, (0,255,0), -1)

        # ================== MOD: วาดข้อความที่ "ล่างซ้ายของวิดีโอ" และไฟเขียวมุมขวาบน ==================
        def ok_rng(val, rng):
            return val is not None and (rng[0] <= val <= rng[1])

        # เช็คผ่าน/ไม่ผ่านของแต่ละค่า
        arm_ok  = arm  is not None and ok_rng(arm,  RANGE_ARM)
        back_ok = back is not None and ok_rng(back, RANGE_BACK)
        knee_ok = knee is not None and ok_rng(knee, RANGE_KNEE)

        # ตำแหน่งข้อความล่างซ้าย (อิงขอบภาพ)
        line_h  = 28
        margin  = 18
        x_txt   = 10
        n_lines = sum(v is not None for v in [arm, back, knee])
        ytxt    = H - margin - n_lines*line_h  # เริ่มจากบรรทัดแรกสุด (จะไล่ลงด้านล่าง)

        if arm is not None:
            frame = put_text(
                frame,
                f"แขน: {int(arm)}°",
                f"Arm: {int(arm)}°",
                (x_txt, ytxt),
                C_OK if arm_ok else C_BAD
            )
            ytxt += line_h

        if back is not None:
            frame = put_text(
                frame,
                f"หลัง: {int(back)}°",
                f"Back: {int(back)}°",
                (x_txt, ytxt),
                C_OK if back_ok else C_BAD
            )
            ytxt += line_h

        if knee is not None:
            frame = put_text(
                frame,
                f"เข่า: {int(knee)}°",
                f"Knee: {int(knee)}°",
                (x_txt, ytxt),
                C_OK if knee_ok else C_BAD
            )

        # วงกลมเขียวมุมขวาบนเมื่อทั้ง 3 เป็นสีเขียว
        if arm_ok and back_ok and knee_ok:
            cv2.circle(frame, (W - 24, 24), 12, C_OK, -1)
        # ================== END MOD ==================

        # ==== Extra label at bottom-right (เพิ่มข้อความล่างขวาโดยไม่แตะส่วนอื่น) ====
        extra_th = "........จัดทำโดย........"
        extra_th = "นายภัทรกฤต ปิ่นแก้ว 664245013"      # เปลี่ยนเป็นชื่อคนได้ เช่น "ชื่อ: นนท์"
        extra_en = "Good performance"
        shown = extra_th if THAI_FONT else extra_en

        # คำนวณความกว้างข้อความเพื่อชิดขวา
        if THAI_FONT:
            f = THAI_FONT.font_variant(size=FONT_SIZE)
            try:
                l, t, r, b = f.getbbox(shown)     # Pillow เวอร์ชันใหม่
                text_w, text_h = (r - l), (b - t)
            except Exception:
                text_w, text_h = f.getsize(shown) # เผื่อเวอร์ชันเก่า
        else:
            (text_w, text_h), _ = cv2.getTextSize(shown, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)

        margin_r, margin_b = 12, 30
        x_extra = W - margin_r - text_w
        y_extra = H - margin_b
        frame = put_text(frame, extra_th, extra_en, (x_extra, y_extra), C_INFO)
        # ==== END extra label ====

        cv2.imshow("Focus Pose @ Receiving", frame)
        if cv2.waitKey(1) & 0xFF == 27: break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()