def parse_trace(file_content):
    lines = file_content.strip().split("\n")
    ops = []
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            raise ValueError(f"Line {i+1}: Malformed line (too short): '{line}'")
        
        op = parts[0].upper()
        if op not in ("R", "W"):
            raise ValueError(f"Line {i+1}: Unknown operation '{op}' in line: '{line}'")
        
        key = parts[1]
        val = None
        if op == "W":
            if len(parts) >= 3:
                val = parts[2]
            else:
                val = f"data_{key}" # Default value if not provided
        
        ops.append({"op": op, "key": key, "val": val, "raw": line})
    return ops
