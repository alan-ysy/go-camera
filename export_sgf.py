"""
SGF Exporter
- Loads board_state.npy and exports it as an SGF file
- SGF uses AB[] for black stones and AW[] for white stones
- Board coordinate system: columns a-s, rows a-s (top-left = aa)
"""

import numpy as np
import sys
from datetime import datetime

BOARD_SIZE = 19

def board_to_sgf(board, board_size=19, filename="output.sgf"):
    """Convert a board state array to SGF format."""
    black_stones = []
    white_stones = []

    for r in range(board_size):
        for c in range(board_size):
            if board[r, c] == 1:
                # SGF coords: column letter + row letter, both a-s
                coord = chr(ord('a') + c) + chr(ord('a') + r)
                black_stones.append(coord)
            elif board[r, c] == 2:
                coord = chr(ord('a') + c) + chr(ord('a') + r)
                white_stones.append(coord)

    # Build SGF
    lines = []
    lines.append("(;")
    lines.append(f"GM[1]")          # Game type: Go
    lines.append(f"FF[4]")          # File format version
    lines.append(f"SZ[{board_size}]")
    lines.append(f"DT[{datetime.now().strftime('%Y-%m-%d')}]")
    lines.append(f"AP[GoBoardVision:1.0]")
    lines.append(f"CA[UTF-8]")

    if black_stones:
        ab = "AB" + "".join(f"[{s}]" for s in black_stones)
        lines.append(ab)
    if white_stones:
        aw = "AW" + "".join(f"[{s}]" for s in white_stones)
        lines.append(aw)

    lines.append(")")

    sgf_text = "\n".join(lines)

    with open(filename, "w") as f:
        f.write(sgf_text)

    print(f"Exported {len(black_stones)} black and {len(white_stones)} white stones")
    print(f"Saved to {filename}")
    return sgf_text

def main():
    state_path = sys.argv[1] if len(sys.argv) > 1 else "board_state.npy"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "output.sgf"

    board = np.load(state_path)
    sgf = board_to_sgf(board, BOARD_SIZE, output_path)
    print(f"\n{sgf}")

if __name__ == "__main__":
    main()