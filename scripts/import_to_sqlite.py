import csv, sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
DB   = ROOT / "bannerlord.db"

def run():
    con = sqlite3.connect(DB)
    cur = con.cursor()

    cur.executescript("""
    PRAGMA foreign_keys = OFF;

    DROP TABLE IF EXISTS lord_skills;
    DROP TABLE IF EXISTS lord_traits;
    DROP TABLE IF EXISTS lords;

    CREATE TABLE lords (
      lord_id     INTEGER PRIMARY KEY AUTOINCREMENT,
      ext_id      TEXT UNIQUE,
      clan_id     INTEGER,
      name        TEXT NOT NULL,
      gender      TEXT,
      age         INTEGER,
      culture_id  INTEGER,
      level       INTEGER,
      sp_per_lvl  INTEGER,
      sum_stats   INTEGER,
      traits      TEXT,
      source_url  TEXT NOT NULL
    );

    CREATE TABLE lord_traits (
      lord_id INTEGER NOT NULL,
      trait   TEXT NOT NULL,
      PRIMARY KEY (lord_id, trait),
      FOREIGN KEY (lord_id) REFERENCES lords(lord_id)
    );

    CREATE TABLE lord_skills (
      lord_id  INTEGER NOT NULL,
      skill_id INTEGER NOT NULL,
      value    INTEGER,
      PRIMARY KEY (lord_id, skill_id),
      FOREIGN KEY (lord_id) REFERENCES lords(lord_id)
    );

    CREATE UNIQUE INDEX IF NOT EXISTS ux_lords_ext ON lords(ext_id);
    """)

    # lords.csv
    ext2id = {}
    with open(PROC/"lords.csv", encoding="utf-8") as f:
        r = csv.DictReader(f)
        rows = []
        for row in r:
            rows.append((
                row["ext_id"],
                None,                               # clan_id
                row["name"],
                row.get("gender") or None,
                int(row["age"]) if row.get("age") else None,
                None,                               # culture_id
                int(row["level"]) if row.get("level") else None,
                None, None,
                row.get("traits") or None,
                row["source_url"]
            ))
        cur.executemany("""
        INSERT INTO lords
        (ext_id,clan_id,name,gender,age,culture_id,level,sp_per_lvl,sum_stats,traits,source_url)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, rows)

    for ext_id, lid in cur.execute("SELECT ext_id, lord_id FROM lords"):
        ext2id[ext_id] = lid

    # lord_traits.csv
    p = PROC/"lord_traits.csv"
    if p.exists():
        with open(p, encoding="utf-8") as f:
            r = csv.DictReader(f)
            rows = []
            for row in r:
                lid = ext2id.get(row["ext_id"])
                if lid:
                    rows.append((lid, row["trait"]))
            cur.executemany("INSERT OR IGNORE INTO lord_traits(lord_id, trait) VALUES (?,?)", rows)

    # lord_skills.csv
    p = PROC/"lord_skills.csv"
    if p.exists():
        with open(p, encoding="utf-8") as f:
            r = csv.DictReader(f)
            rows = []
            for row in r:
                lid = ext2id.get(row["ext_id"])
                if not lid:
                    continue
                sk = (row["skill_key"] or "").strip().lower()
                if not sk:
                    continue
                skill_id = abs(hash(sk)) % (10**9)   # temp mapping
                val = int(row["value"]) if row.get("value") else None
                rows.append((lid, skill_id, val))
            cur.executemany("INSERT OR IGNORE INTO lord_skills(lord_id, skill_id, value) VALUES (?,?,?)", rows)

    con.commit()
    con.close()
    print(f"OK → {DB}")

if __name__ == "__main__":
    run()
