import os

def find_controller_files(base_dir="routers"):
    controller_files = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".py"):
                controller_files.append(os.path.join(root, file))
    return controller_files

if __name__ == "__main__":
    files = find_controller_files()
    print("Detected controller files:")
    for f in files:
        print(f)
