import json
import os
import pandas as pd

def is_cacheable(headers):
    """
    Determine whether a resource is cacheable based on response headers.
    """
    if not headers:
        return False

    cc = headers.get("cache-control", "") or headers.get("Cache-Control", "")
    expires = headers.get("expires", "") or headers.get("Expires", "")
    etag = headers.get("etag", "") or headers.get("ETag", "")
    last_modified = headers.get("last-modified", "") or headers.get("Last-Modified", "")

    # explicit no-cache or no-store
    if "no-cache" in cc or "no-store" in cc:
        return False

    # max-age > 0 --> cacheable
    if "max-age" in cc:
        try:
            directives = dict(
                d.split("=") if "=" in d else (d, None)
                for d in cc.replace(" ", "").split(",")
            )
            max_age = int(directives.get("max-age", -1))
            if max_age > 0:
                return True
        except Exception:
            pass

    # expires header
    if expires:
        return True  # this is an ASSUMPTION about cacheability

    # etag or last-modified --> cacheable
    if etag or last_modified:
        return True

    return False


def analyze_har_cacheability(folder_path):
    """
    Iterate through HAR files, compute cacheability ratios. Returns DataFrame.
    """

    results = []

    for filename in os.listdir(folder_path):
        if not filename.endswith(".har"):
            continue

        filepath = os.path.join(folder_path, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            har = json.load(f)

        pages = har.get("log", {}).get("pages", [])
        page_title = pages[0].get("title", filename.replace(".har", "")) if pages else filename.replace(".har", "")
        entries = har.get("log", {}).get("entries", [])

        total_bytes = 0
        cacheable_bytes = 0

        for entry in entries:
            res = entry.get("response", {})
            headers = {h["name"].lower(): h["value"] for h in res.get("headers", [])}

            # bodySize or content.size can both be the size depending on har generator
            size = res.get("bodySize", -1)
            if size == -1:
                size = res.get("content", {}).get("size", 0)

            if size < 0:
                size = 0

            total_bytes += size

            if is_cacheable(headers):
                cacheable_bytes += size

        ratio = cacheable_bytes / total_bytes if total_bytes > 0 else 0

        results.append({
            "site": page_title,
            "total_bytes": total_bytes,
            "cacheable_bytes": cacheable_bytes,
            "cacheability_ratio": ratio
        })

    return pd.DataFrame(results)

if __name__ == "__main__":
    df = analyze_har_cacheability("./har_files")
    df.to_csv("har_data.csv")
