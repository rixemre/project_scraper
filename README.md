# Bannerlord Scraper
Collects **Lords** data for *Mount & Blade II: Bannerlord* from the public Fandom (MediaWiki) API.  
Produces clean **CSV**s and optional **SQLite DB** (`bannerlord.db`) + **SQL dump** (`dataset.sql`) for downstream use.

## 🛠️ How to use

### 1) Setup

#### Create Python virtual environment and activate
**Windows (PowerShell):**
```powershell
python -m venv .venv
# If scripts are blocked:
# Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
. .\.venv\Scripts\Activate.ps1
#macOS/Linux
python -m venv .venv
source .venv/bin/activate
#Install requirements
python -m pip install -r requirements.txt
# 1) Discover all target pages from Fandom category (auto-fills lords_list.txt)
python scrape/build_lords_list.py

# 2) Scrape pages and produce CSVs
python scrape/scrape_lords.py

# 3) (Optional) Build SQLite DB from CSVs
python scripts/import_to_sqlite.py   # → bannerlord.db

# 4) (Optional) Export full SQL dump
python scripts/dump_sqlite.py        # → dataset.sql

