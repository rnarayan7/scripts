import os
import json

def main():
    for filename in os.listdir(os.path.join(os.path.dirname(__file__), "data")):
        if filename.endswith(".json"):
            fpath = os.path.join(os.path.dirname(__file__), "data", filename)
            with open(fpath, "r") as f:
                data = json.load(f)
            new_data = {"date": data["date"], "activities": data["activities"]["activities"]}
            with open(fpath, "w") as f:
                json.dump(new_data, f, indent=4)

if __name__ == "__main__":
    main()