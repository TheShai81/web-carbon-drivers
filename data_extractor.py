import json
import pandas as pd
from glob import glob
import os


def safe_get(data, *keys, default=None):
    '''Safe JSON getter'''
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def extract_from_json(file_path):
    '''Extracts selected metrics from a Lighthouse JSON file.'''
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    audits = data.get("audits", {})
    url = data.get("requestedUrl", os.path.basename(file_path))

    total_bytes = safe_get(audits, "total-byte-weight", "numericValue")
    network_items = safe_get(audits, "network-requests", "details", "items", default=[])
    requests = len(network_items)
    third_party_items = safe_get(audits, "third-party-summary", "details", "items", default=[])
    third_party_bytes = sum(item.get("transferSize", 0) for item in third_party_items)

    fcp = safe_get(audits, "first-contentful-paint", "numericValue")
    lcp = safe_get(audits, "largest-contentful-paint", "numericValue")
    tbt = safe_get(audits, "total-blocking-time", "numericValue")
    speed_index = safe_get(audits, "speed-index", "numericValue")
    cls = safe_get(audits, "cumulative-layout-shift", "numericValue")

    # bytes to MB
    total_mb = total_bytes / (1024 ** 2) if total_bytes else None
    third_party_mb = third_party_bytes / (1024 ** 2) if third_party_bytes else None

    resource_items = safe_get(audits, "resource-summary", "details", "items", default=[])

    js_bytes = css_bytes = img_bytes = font_bytes = html_bytes = other_bytes = 0
    js_count = css_count = img_count = font_count = html_count = other_count = 0

    for item in resource_items:
        rtype = item.get("resourceType", "").lower()
        size = item.get("transferSize", 0)
        count = item.get("requestCount", 0)

        if rtype == "script":
            js_bytes += size
            js_count += count
        elif rtype == "image":
            img_bytes += size
            img_count += count
        elif rtype == "stylesheet":
            css_bytes += size
            css_count += count
        elif rtype == "font":
            font_bytes += size
            font_count += count
        elif rtype == "document":
            html_bytes += size
            html_count += count
        else:
            other_bytes += size
            other_count += count

    dom_items = safe_get(audits, "dom-size", "details", "items", default=[])
    dom_size = dom_items[0].get("nodeCount") if dom_items else None

    return {
        "url": url,
        # main metrics
        "total_bytes": total_bytes,
        "total_mb": total_mb,
        "requests": requests,
        "third_party_bytes": third_party_bytes,
        "third_party_mb": third_party_mb,
        # performnance metrics
        "fcp_ms": fcp,
        "lcp_ms": lcp,
        "tbt_ms": tbt,
        "speed_index": speed_index,
        "cls": cls,
        # resource summary
        "js_bytes": js_bytes,
        "css_bytes": css_bytes,
        "img_bytes": img_bytes,
        "font_bytes": font_bytes,
        "html_bytes": html_bytes,
        "other_bytes": other_bytes,
        "js_count": js_count,
        "css_count": css_count,
        "img_count": img_count,
        "font_count": font_count,
        "html_count": html_count,
        "other_count": other_count,
        "dom_size": dom_size
    }

def main(input_folder="reports", output_csv="lighthouse_summary.csv"):
    '''Reads all JSONs in a folder, extracts metrics, saves to CSV.'''
    files = glob(os.path.join(input_folder, "*.json"))

    if not files:
        print(f"No JSON files found in {input_folder}")
        return

    data = [extract_from_json(f) for f in files]
    df = pd.DataFrame(data)
    df.to_csv(output_csv, index=False)

    print(f"Extracted data from {len(df)} files.")
    print(f"Saved summary to: {output_csv}")
    print(df.head())


if __name__ == "__main__":
    main()
