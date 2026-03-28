import json

def generate_openapi(endpoints_file="detected_endpoints.json", output_file="openapi_generated.json"):
    # Load the endpoints JSON created in Week 5
    with open(endpoints_file, "r", encoding="utf-8") as f:
        endpoints = json.load(f)

    # Basic OpenAPI structure
    openapi = {
        "openapi": "3.0.0",
        "info": {
            "title": "Recruitment Candidate Tracker API",
            "version": "1.0.0"
        },
        "paths": {}
    }

    # Convert endpoints into OpenAPI paths
    for ep in endpoints:
        path = ep["path"]
        method = ep["method"].lower()
        if path not in openapi["paths"]:
            openapi["paths"][path] = {}
        openapi["paths"][path][method] = {
            "summary": f"{method.upper()} {path}",
            "responses": {
                "200": {
                    "description": "Successful response"
                }
            }
        }

    # Save to file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(openapi, f, indent=2)

    print(f"OpenAPI spec saved to {output_file}")

if __name__ == "__main__":
    generate_openapi()
