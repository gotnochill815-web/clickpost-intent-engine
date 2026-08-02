import json
import os


def save_extraction(output_dir, source_name, data):
    os.makedirs(output_dir, exist_ok=True)

    with open(
        os.path.join(output_dir, f"{source_name}.json"),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(data, f, indent=2, ensure_ascii=False)