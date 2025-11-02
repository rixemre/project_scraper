import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB   = ROOT / "bannerlord.db"
OUT  = ROOT / "dataset.sql"

def main():
    con = sqlite3.connect(DB)
    with open(OUT, "w", encoding="utf-8") as f:
        for line in con.iterdump():
            f.write(f"{line}\n")
    con.close()
    print(f"Wrote {OUT}")

if __name__ == "__main__":
    main()
