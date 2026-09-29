import pandas as pd

def flatten_json(obj, parent_key="", sep="."):
    items = {}
    if isinstance(obj, dict):
        for key, value in obj.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else str(key)
            if isinstance(value, dict):
                items.update(flatten_json(value, new_key, sep))
            else:
                items[new_key] = value
    else:
        return {parent_key: obj}
    return items

def _is_record_list(value):
    return isinstance(value, list) and len(value) > 0 and all(isinstance(x, dict) for x in value)

def json_to_frames(data, root_name="root"):
    frames = {}
    def walk(obj, path):
        if isinstance(obj, dict):
            for key, value in obj.items():
                current = f"{path}.{key}" if path else key
                if _is_record_list(value):
                    try:
                        frames[current] = pd.json_normalize(value, sep=".")
                    except Exception:
                        pass
                walk(value, current)
        elif isinstance(obj, list):
            if _is_record_list(obj):
                try:
                    frames[path or root_name] = pd.json_normalize(obj, sep=".")
                except Exception:
                    pass
            for i, value in enumerate(obj[:100]):
                if isinstance(value, (dict, list)):
                    walk(value, f"{path}[{i}]")
    walk(data, "")
    if not frames:
        frames[root_name] = pd.DataFrame([flatten_json(data)])
    return frames
