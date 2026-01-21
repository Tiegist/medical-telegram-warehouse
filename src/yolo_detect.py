import argparse
from pathlib import Path

import pandas as pd
from ultralytics import YOLO

from src.config import settings


PRODUCT_CLASSES = {
    "bottle",
    "cup",
    "bowl",
    "box",
    "cell phone",
    "book",
    "toothbrush",
    "remote",
}


def _categorize(has_person: bool, has_product: bool) -> str:
    if has_person and has_product:
        return "promotional"
    if has_person and not has_product:
        return "lifestyle"
    if has_product and not has_person:
        return "product_display"
    return "other"


def run_detection(image_dir: Path, output_csv: Path):
    model = YOLO(settings.yolo_model)
    rows = []

    for image_path in image_dir.rglob("*.jpg"):
        result = model(str(image_path), verbose=False)[0]
        names = result.names
        classes = [names[int(c)] for c in result.boxes.cls.tolist()] if result.boxes else []
        confs = result.boxes.conf.tolist() if result.boxes else []

        has_person = "person" in classes
        has_product = any(cls in PRODUCT_CLASSES for cls in classes)
        image_category = _categorize(has_person, has_product)

        message_id = image_path.stem
        channel_name = image_path.parent.name

        if not classes:
            rows.append(
                {
                    "message_id": message_id,
                    "channel_name": channel_name,
                    "image_path": str(image_path),
                    "detected_class": None,
                    "confidence_score": None,
                    "image_category": image_category,
                }
            )
            continue

        for detected_class, confidence_score in zip(classes, confs):
            rows.append(
                {
                    "message_id": message_id,
                    "channel_name": channel_name,
                    "image_path": str(image_path),
                    "detected_class": detected_class,
                    "confidence_score": float(confidence_score),
                    "image_category": image_category,
                }
            )

    df = pd.DataFrame(rows)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    print(f"Wrote {len(df)} detections to {output_csv}")


def main():
    parser = argparse.ArgumentParser(description="Run YOLO detection on scraped images.")
    parser.add_argument("--image-dir", default="data/raw/images")
    parser.add_argument("--output-csv", default="data/processed/yolo_detections.csv")
    args = parser.parse_args()

    run_detection(Path(args.image_dir), Path(args.output_csv))


if __name__ == "__main__":
    main()


