import os
import re
import json

def find_controller_files(base_dir="routers"):
    controller_files = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                controller_files.append(os.path.join(root, file))
    return controller_files

def extract_endpoints(file_path):
    endpoints = []
    pattern = re.compile(r'@router\.(get|post|put|delete)\("([^"]+)"')
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            match = pattern.search(line)
            if match:
                method, path = match.groups()
                endpoints.append({
                    "method": method.upper(),
                    "path": path,
                    "file": file_path
                })
    return endpoints

if __name__ == "__main__":
    files = find_controller_files()
    all_endpoints = []

    for f in files:
        endpoints = extract_endpoints(f)
        all_endpoints.extend(endpoints)

    # Print to console
    print("Detected endpoints:")
    for ep in all_endpoints:
        print(f"- {ep['method']} {ep['path']} (from {ep['file']})")

    # Save to JSON file
    with open("detected_endpoints.json", "w", encoding="utf-8") as f:
        json.dump(all_endpoints, f, indent=2)

    print("\nEndpoints saved to detected_endpoints.json")
