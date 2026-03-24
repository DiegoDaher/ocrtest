from __future__ import annotations

import cv2
import numpy as np


def detect_document_regions(
    image: np.ndarray,
    min_area_ratio: float = 0.008,
    max_regions: int = 3,
    margin: int = 24,
) -> list[tuple[str, np.ndarray]]:
    height, width = image.shape[:2]
    page_area = float(height * width)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Detect non-white content blocks (typical when cards are centered on a white PDF page).
    _, mask = cv2.threshold(gray, 242, 255, cv2.THRESH_BINARY_INV)
    kernel = np.ones((15, 15), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes: list[tuple[int, int, int, int, int]] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        if area < int(page_area * min_area_ratio):
            continue
        boxes.append((x, y, w, h, area))

    if not boxes:
        return [("full", image)]

    boxes.sort(key=lambda item: item[4], reverse=True)
    regions: list[tuple[str, np.ndarray]] = []
    for idx, (x, y, w, h, _) in enumerate(boxes[:max_regions], start=1):
        x0 = max(0, x - margin)
        y0 = max(0, y - margin)
        x1 = min(width, x + w + margin)
        y1 = min(height, y + h + margin)
        crop = image[y0:y1, x0:x1]
        if crop.size == 0:
            continue
        regions.append((f"region_{idx}", crop))

    return regions or [("full", image)]


def resize_for_ocr(gray: np.ndarray, min_width: int = 1800) -> np.ndarray:
    height, width = gray.shape[:2]
    if width >= min_width:
        return gray

    scale = min_width / float(width)
    resized = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    return resized


def deskew(gray: np.ndarray) -> np.ndarray:
    _, threshold = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    points = np.column_stack(np.where(threshold > 0))
    if points.size == 0:
        return gray

    angle = cv2.minAreaRect(points)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    if abs(angle) < 0.3:
        return gray

    height, width = gray.shape[:2]
    center = (width // 2, height // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(
        gray,
        matrix,
        (width, height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )


def preprocess_variants(image: np.ndarray) -> dict[str, np.ndarray]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    resized = resize_for_ocr(gray)
    contrast = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(resized)
    denoised = cv2.bilateralFilter(contrast, d=9, sigmaColor=75, sigmaSpace=75)
    deskewed = deskew(denoised)
    blur = cv2.GaussianBlur(deskewed, (3, 3), 0)

    _, otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    adaptive = cv2.adaptiveThreshold(
        blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        35,
        15,
    )
    inverted = cv2.bitwise_not(otsu)

    variants: dict[str, np.ndarray] = {
        "gray": blur,
        "otsu": otsu,
        "adaptive": adaptive,
        "inverted": inverted,
    }

    # Card-focused variants: for INE-like crops, boost lower/detail area where CURP and address are usually printed.
    height, width = image.shape[:2]
    aspect_ratio = (width / float(height)) if height else 0.0
    if 1.2 <= aspect_ratio <= 2.2 and width >= 350 and height >= 220:
        y0 = int(height * 0.18)
        y1 = int(height * 0.95)
        x0 = int(width * 0.08)
        x1 = int(width * 0.95)
        focus = image[y0:y1, x0:x1]
        if focus.size > 0:
            focus_gray = cv2.cvtColor(focus, cv2.COLOR_BGR2GRAY)
            for scale in (2.0, 3.0):
                upscaled = cv2.resize(focus_gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
                clahe_focus = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(upscaled)
                _, otsu_focus = cv2.threshold(clahe_focus, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                variants[f"focus_clahe_x{int(scale * 10)}"] = clahe_focus
                variants[f"focus_otsu_x{int(scale * 10)}"] = otsu_focus

    return variants

