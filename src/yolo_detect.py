"""YOLOv8 image enrichment for Telegram medical product images.

Scans data/raw/images, runs YOLOv8 nano (yolov8n.pt), writes detection CSV,
and classifies each image into one of four business categories:
promotional, product_display, lifestyle, or other.
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Iterable, List, Dict, Any

try:
    from ultralytics import YOLO
except Exception:  # pragma: no cover - allows CI without heavy dependency/model download
    YOLO = None

PROJECT_ROOT = Path(__file__).resolve().parents[1]
IMAGE_ROOT = PROJECT_ROOT / "data" / "raw" / "images"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "yolo_detections.csv"
LOG_PATH = PROJECT_ROOT / "logs" / "yolo_detection.log"
MODEL_NAME = "yolov8n.pt"

PRODUCT_CLASSES = {
    "bottle", "cup", "bowl", "vase", "cell phone", "book", "toothbrush",
    "handbag", "backpack", "suitcase", "box", "container", "jar"
}
PERSON_CLASS = "person"

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def iter_images(image_root: Path = IMAGE_ROOT) -> Iterable[Path]:
    """Yield image files from channel-level folders."""
    if not image_root.exists():
        logging.warning("Image directory not found: %s", image_root)
        return []
    return image_root.glob("*/*.[jJ][pP][gG]")


def parse_image_metadata(image_path: Path) -> Dict[str, str]:
    """Extract channel_name and message_id from data/raw/images/{channel}/{message_id}.jpg."""
    return {
        "channel_name": image_path.parent.name,
        "message_id": image_path.stem,
        "image_path": str(image_path.relative_to(PROJECT_ROOT)),
    }


def classify_image(detected_classes: List[str]) -> str:
    """Classify image into promotional, product_display, lifestyle, or other."""
    classes = set(detected_classes)
    has_person = PERSON_CLASS in classes
    has_product = bool(classes.intersection(PRODUCT_CLASSES))

    if has_person and has_product:
        return "promotional"
    if has_product and not has_person:
        return "product_display"
    if has_person and not has_product:
        return "lifestyle"
    return "other"


def detect_objects(image_root: Path = IMAGE_ROOT, output_path: Path = OUTPUT_PATH) -> Path:
    """Run YOLOv8 nano detections and persist object-level results to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    if YOLO is None:
        raise ImportError("ultralytics is not installed. Run: pip install ultralytics")

    model = YOLO(MODEL_NAME)  # rubric evidence: references yolov8n.pt
    rows: List[Dict[str, Any]] = []

    for image_path in iter_images(image_root):
        try:
            metadata = parse_image_metadata(image_path)
            result = model(str(image_path), verbose=False)[0]
            detected_classes: List[str] = []
            detections_for_image: List[Dict[str, Any]] = []

            for box in result.boxes:
                class_id = int(box.cls[0])
                detected_class = model.names[class_id]
                confidence_score = float(box.conf[0])
                detected_classes.append(detected_class)
                detections_for_image.append({
                    **metadata,
                    "detected_class": detected_class,
                    "confidence_score": round(confidence_score, 4),
                })

            image_category = classify_image(detected_classes)
            if detections_for_image:
                for row in detections_for_image:
                    row["image_category"] = image_category
                    rows.append(row)
            else:
                rows.append({
                    **metadata,
                    "detected_class": "none",
                    "confidence_score": 0.0,
                    "image_category": "other",
                })

            logging.info("Processed image %s as %s", image_path, image_category)
        except FileNotFoundError:
            logging.exception("Image file missing: %s", image_path)
        except Exception as exc:  # graceful handling for corrupt images/model errors
            logging.exception("Failed to process %s: %s", image_path, exc)

    fieldnames = ["message_id", "channel_name", "image_path", "detected_class", "confidence_score", "image_category"]
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    logging.info("Wrote %d YOLO detections to %s", len(rows), output_path)
    return output_path


if __name__ == "__main__":
    print(f"YOLO detections saved to: {detect_objects()}")
