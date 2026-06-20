from typing import List, Dict, Any

def parse_trace(file_content: str) -> List[Dict[str, Any]]:
    """Parse a plaintext trace file into a list of structured operations.
    
    Args:
        file_content: The raw text of the trace file containing commands
            like 'R 0x1000' or 'W 0x2000 APPLE'.
            
    Returns:
        A list of dictionaries representing the operations. Each dict has:
            - op (str): 'R' or 'W'
            - key (str): The target key
            - val (Optional[str]): The value to write (None if read)
            - raw (str): The original line from the file for logging
            
    Raises:
        ValueError: If a line is malformed or contains an unknown operation.
    """
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
        
        addr_hex = parts[1]
        try:
            addr_val = int(addr_hex, 0)
        except ValueError:
            raise ValueError(f"Line {i+1}: Invalid address '{addr_hex}' in line: '{line}'")
        
        val = None
        if op == "W":
            if len(parts) >= 3:
                val = parts[2]
            else:
                val = f"data_{addr_hex}" # Default value if not provided
        
        ops.append({"op": op, "addr_hex": addr_hex, "addr_val": addr_val, "val": val, "raw": line})
    return ops
