from __future__ import annotations
import csv, re
from pathlib import Path
from bs4 import BeautifulSoup
from common import get_page_html, ROOT

PROC = ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)

LORDS_CSV = PROC / "lords.csv"
TRAITS_CSV = PROC / "lord_traits.csv"
SKILLS_CSV = PROC / "lord_skills.csv"

def slugify(title: str) -> str:
    return title.replace(" ", "_")

def parse_infobox(html: str) -> dict:
    """
    Tries to parse infobox-like structures (portable-infobox or classic table).
    Returns dict with name/age/gender/level if found.
    """
    soup = BeautifulSoup(html, "lxml")

    # Try portable infobox
    ib = soup.select_one(".portable-infobox")
    if not ib:
        # fallback: classic infobox table
        ib = soup.select_one("table.infobox")

    result = {"name": None, "age": None, "gender": None, "level": None}
    if not ib:
        # sometimes title is in first heading
        h1 = soup.select_one("h1") or soup.select_one("#firstHeading")
        if h1:
            result["name"] = h1.get_text(strip=True)
        return result

    # Prefer title from page heading if present
    heading = soup.select_one("#firstHeading") or soup.select_one("h1")
    if heading:
        result["name"] = heading.get_text(strip=True)

    # portable-infobox: data items are often in <div data-source="Age"> etc.
    for node in ib.select("[data-source]"):
        label = (node.get("data-source") or "").strip().lower()
        val = node.get_text(" ", strip=True)
        if not val:
            continue
        if label == "age":
            m = re.search(r"\d+", val)
            result["age"] = int(m.group()) if m else None
        elif label in ("gender", "sex"):
            result["gender"] = val
        elif label in ("level",):
            m = re.search(r"\d+", val)
            result["level"] = int(m.group()) if m else None

    # fallback classic table: rows <tr><th>Label</th><td>Value</td>
    if result["age"] is None or result["gender"] is None or result["level"] is None:
        for tr in ib.select("tr"):
            th = tr.find("th")
            td = tr.find("td")
            if not th or not td:
                continue
            label = th.get_text(" ", strip=True).lower()
            val = td.get_text(" ", strip=True)
            if "age" in label and result["age"] is None:
                m = re.search(r"\d+", val)
                result["age"] = int(m.group()) if m else None
            elif "gender" in label and result["gender"] is None:
                result["gender"] = val
            elif "level" in label and result["level"] is None:
                m = re.search(r"\d+", val)
                result["level"] = int(m.group()) if m else None

    return result

def extract_traits(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    traits = []

    # Look for headers named "Traits"
    for hdr in soup.find_all(["h2", "h3", "h4"]):
        text = hdr.get_text(" ", strip=True).lower()
        if "trait" in text:
            # grab following lists or paragraphs until next header
            for sib in hdr.find_all_next():
                if sib.name in ("h2", "h3"):
                    break
                if sib.name in ("ul", "ol"):
                    for li in sib.find_all("li"):
                        t = li.get_text(" ", strip=True)
                        if t:
                            traits.append(t)
                if sib.name == "p":
                    t = sib.get_text(" ", strip=True)
                    if t and len(t.split()) < 10:
                        traits.append(t)
            break

    # de-dup, clean
    clean = []
    for t in traits:
        t = re.sub(r"\s+", " ", t).strip(" •;,-")
        if t and t not in clean:
            clean.append(t)
    return clean

def extract_skills(html: str) -> dict:
    """
    Find a table likely containing skills; return {skill_key: value}.
    Heuristic: search for tables where headers mention 'skill' or
    where cells look like "Skill | Value".
    """
    soup = BeautifulSoup(html, "lxml")
    skills = {}

    tables = soup.find_all("table")
    for tbl in tables:
        headers = [th.get_text(" ", strip=True).lower() for th in tbl.find_all("th")]
        if not headers:
            continue
        if any("skill" in h for h in headers) or any("value" in h for h in headers):
            for tr in tbl.find_all("tr"):
                tds = tr.find_all(["td", "th"])
                if len(tds) < 2:
                    continue
                k = tds[0].get_text(" ", strip=True)
                v = tds[1].get_text(" ", strip=True)
                if not k:
                    continue
                # normalize key & parse value
                key = re.sub(r"\s+", "_", k.strip().lower())
                m = re.search(r"-?\d+", v)
                val = int(m.group()) if m else None
                if key not in ("skill", "name"):
                    skills[key] = val
    return skills

def main():
    lst_path = ROOT / "lords_list.txt"
    if not lst_path.exists():
        print("lords_list.txt not found. Run: python scrape/build_lords_list.py")
        return

    lords = []
    traits_rows = []
    skills_rows = []

    for title in lst_path.read_text(encoding="utf-8").splitlines():
        title = title.strip()
        if not title:
            continue

        html = get_page_html(title)
        info = parse_infobox(html)
        traits = extract_traits(html)
        skills = extract_skills(html)

        ext_id = slugify(title)
        name = info.get("name") or title
        age = info.get("age")
        gender = info.get("gender")
        level = info.get("level")
        source_url = f"https://bannerlord.fandom.com/wiki/{ext_id}"

        lords.append({
            "ext_id": ext_id,
            "name": name,
            "gender": gender or "",
            "age": age if age is not None else "",
            "culture_id": "",     # reserved
            "level": level if level is not None else "",
            "sp_per_lvl": "",
            "sum_stats": "",
            "traits": "; ".join(traits) if traits else "",
            "source_url": source_url
        })

        for t in traits:
            traits_rows.append({"ext_id": ext_id, "trait": t})

        for k, v in skills.items():
            skills_rows.append({"ext_id": ext_id, "skill_key": k, "value": v if v is not None else ""})

        print(f"OK: {title}")

    # write CSVs
    LORDS_CSV.write_text("", encoding="utf-8")  # ensure recreate
    with LORDS_CSV.open("w", newline="", encoding="utf-8") as f:
        fieldnames = ["ext_id","name","gender","age","culture_id","level","sp_per_lvl","sum_stats","traits","source_url"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(lords)

    with TRAITS_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["ext_id","trait"])
        w.writeheader()
        w.writerows(traits_rows)

    with SKILLS_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["ext_id","skill_key","value"])
        w.writeheader()
        w.writerows(skills_rows)

    print(f"\nSaved:\n- {LORDS_CSV}\n- {TRAITS_CSV}\n- {SKILLS_CSV}")

if __name__ == "__main__":
    main()
