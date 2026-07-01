#!/usr/bin/env python3

import json
import random
import shutil
from pathlib import Path
from collections import Counter

import numpy as np


INPUT_DIR = Path("/home/bo/amr_ws/datasets/warehouse_3d_training/gg6")
OUTPUT_DIR = Path("/home/bo/amr_ws/datasets/warehouse_openpcdet/person_run_gg6")

# CVAT label names allowed.
# Output class will always be "person".
CLASS_ALIASES = {
    "person": "person",
    "human": "person",
}

TRAIN_RATIO = 0.8
RANDOM_SEED = 42


def read_pcd_ascii_xyz(path):
    points = []
    data_started = False

    with open(path, "r") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            if data_started:
                parts = line.split()

                if len(parts) < 3:
                    continue

                try:
                    x = float(parts[0])
                    y = float(parts[1])
                    z = float(parts[2])

                    if not np.isfinite([x, y, z]).all():
                        continue

                    # OpenPCDet custom dataset expects:
                    # x, y, z, intensity
                    points.append([x, y, z, 0.0])

                except ValueError:
                    continue

            if line.startswith("DATA"):
                if "ascii" not in line:
                    raise RuntimeError(f"Only ASCII PCD is supported: {path}")

                data_started = True

    return np.asarray(points, dtype=np.float32)


def get_label_names(data):
    labels = data["categories"]["label"]["labels"]

    id_to_name = {}

    for i, item in enumerate(labels):
        if isinstance(item, dict):
            id_to_name[i] = item["name"]
        else:
            id_to_name[i] = str(item)

    return id_to_name


def get_class_name(ann, id_to_name):
    label_id = ann.get("label_id", ann.get("label", None))

    if isinstance(label_id, str):
        raw_name = label_id.lower()
    else:
        raw_name = id_to_name.get(label_id, str(label_id)).lower()

    return CLASS_ALIASES.get(raw_name, None)


def find_pcd_for_item(item, input_dir):
    frame_id = item["id"]

    # Normal CVAT Datumaro 3D path
    p1 = input_dir / "point_clouds" / "default" / f"{frame_id}.pcd"
    if p1.exists():
        return p1

    # If item id already includes .pcd
    p2 = input_dir / "point_clouds" / "default" / frame_id
    if p2.exists():
        return p2

    # Sometimes Datumaro stores point cloud path inside item
    pc = item.get("point_cloud", None)
    if isinstance(pc, dict):
        rel = pc.get("path", None)
        if rel:
            p3 = input_dir / rel
            if p3.exists():
                return p3

    # Fallback search
    matches = list(input_dir.glob(f"**/{frame_id}.pcd"))
    if matches:
        return matches[0]

    matches = list(input_dir.glob(f"**/{frame_id}"))
    if matches:
        return matches[0]

    raise FileNotFoundError(f"Could not find PCD for frame id: {frame_id}")


def main():
    ann_path = INPUT_DIR / "annotations" / "default.json"

    if not ann_path.exists():
        raise FileNotFoundError(f"Missing annotation file: {ann_path}")

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)

    points_out = OUTPUT_DIR / "points"
    labels_out = OUTPUT_DIR / "labels"
    imagesets_out = OUTPUT_DIR / "ImageSets"

    points_out.mkdir(parents=True, exist_ok=True)
    labels_out.mkdir(parents=True, exist_ok=True)
    imagesets_out.mkdir(parents=True, exist_ok=True)

    with open(ann_path, "r") as f:
        data = json.load(f)

    id_to_name = get_label_names(data)

    frame_ids = []
    class_counter = Counter()
    empty_frames = 0

    for item in data["items"]:
        frame_id = item["id"]
        pcd_path = find_pcd_for_item(item, INPUT_DIR)

        points = read_pcd_ascii_xyz(pcd_path)

        if points.shape[0] < 100:
            print(f"Skipping {frame_id}: too few points")
            continue

        # np.save(points_out / f"{frame_id}.npy", points)

        label_lines = []

        for ann in item.get("annotations", []):
            if ann.get("type") != "cuboid_3d":
                continue

            cls = get_class_name(ann, id_to_name)

            if cls is None:
                continue

            pos = ann["position"]
            scale = ann["scale"]
            rot = ann.get("rotation", [0.0, 0.0, 0.0])

            x = float(pos[0])
            y = float(pos[1])
            z = float(pos[2])

            l = float(scale[0])
            w = float(scale[1])
            h = float(scale[2])

            yaw = float(rot[2]) if len(rot) >= 3 else 0.0

            values = [x, y, z, l, w, h, yaw]

            if not np.all(np.isfinite(values)):
                continue

            if l <= 0 or w <= 0 or h <= 0:
                continue

            # OpenPCDet custom label format:
            # x y z length width height yaw class
            label_lines.append(
                f"{x:.6f} {y:.6f} {z:.6f} "
                f"{l:.6f} {w:.6f} {h:.6f} "
                f"{yaw:.6f} {cls}"
            )

            class_counter[cls] += 1

        if len(label_lines) == 0:
            empty_frames += 1
            continue

        np.save(points_out / f"{frame_id}.npy", points)

        with open(labels_out / f"{frame_id}.txt", "w") as f:
            f.write("\n".join(label_lines))
            f.write("\n")

        frame_ids.append(frame_id)



    random.seed(RANDOM_SEED)
    random.shuffle(frame_ids)

    n_train = int(len(frame_ids) * TRAIN_RATIO)

    train_ids = sorted(frame_ids[:n_train])
    val_ids = sorted(frame_ids[n_train:])
    trainval_ids = sorted(frame_ids)

    (imagesets_out / "train.txt").write_text("\n".join(train_ids) + "\n")
    (imagesets_out / "val.txt").write_text("\n".join(val_ids) + "\n")
    (imagesets_out / "trainval.txt").write_text("\n".join(trainval_ids) + "\n")

    print("Done.")
    print("Input:", INPUT_DIR)
    print("Output:", OUTPUT_DIR)
    print("Frames:", len(frame_ids))
    print("Train:", len(train_ids))
    print("Val:", len(val_ids))
    print("Empty label frames:", empty_frames)
    print("Class counts:", dict(class_counter))


if __name__ == "__main__":
    main()