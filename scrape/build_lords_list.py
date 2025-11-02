from pathlib import Path
from common import get_json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "lords_list.txt"

# Gerekirse kategoriyi değiştir: örn. "Category:Bannerlord_characters"
CATEGORY = "Category:Bannerlord_characters"

def fetch_all_members(category: str) -> list[str]:
    titles = []
    cont = None
    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category,
            "cmtype": "page",
            "cmlimit": "500"
        }
        if cont:
            params["cmcontinue"] = cont
        data = get_json(params, sleep=0.6)
        titles.extend(m["title"] for m in data["query"]["categorymembers"])
        cont = data.get("continue", {}).get("cmcontinue")
        if not cont:
            break
    return titles

def clean_titles(titles: list[str]) -> list[str]:
    blocked = ("Category:", "Template:", "File:", "User:", "Talk:", "Help:")
    out = []
    for t in titles:
        if t.startswith(blocked):
            continue
        t = t.strip()
        if t and t not in out:
            out.append(t)
    return sorted(out)

def main():
    titles = fetch_all_members(CATEGORY)
    titles = clean_titles(titles)
    OUT.write_text("\n".join(titles), encoding="utf-8")
    print(f"Saved {len(titles)} titles → {OUT}")

if __name__ == "__main__":
    main()
