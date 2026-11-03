import json
import re
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
README = ROOT / "README.md"
CACHE = ROOT / "data" / "topic-cache.json"
START = "<!-- TOPIC-INDEX-START -->"
END = "<!-- TOPIC-INDEX-END -->"

# LeetCode tag -> tumhare README ka topic
TAG_TO_TOPIC = {
    "Array": "Arrays",
    "String": "Strings",
    "Hash Table": "Hashing",
    "Linked List": "LinkedList",
    "Stack": "Stack-Queue",
    "Monotonic Stack": "Stack-Queue",
    "Queue": "Stack-Queue",
    "Monotonic Queue": "Stack-Queue",
    "Binary Search": "Binary-Search",
    "Recursion": "Recursion-Backtracking",
    "Backtracking": "Recursion-Backtracking",
    "Tree": "Trees",
    "Binary Tree": "Trees",
    "Binary Search Tree": "Trees",
    "Graph": "Graphs",
    "Topological Sort": "Graphs",
    "Union Find": "Graphs",
    "Shortest Path": "Graphs",
    "Greedy": "Greedy",
    "Dynamic Programming": "Dynamic-Programming",
    "Heap (Priority Queue)": "Heap",
}
TOPIC_ORDER = [
    "Arrays", "Strings", "Hashing", "LinkedList", "Stack-Queue",
    "Binary-Search", "Recursion-Backtracking", "Trees", "Graphs",
    "Heap", "Greedy", "Dynamic-Programming", "Other",
]

QUERY = """
query q($slug: String!) {
  question(titleSlug: $slug) {
    questionFrontendId
    title
    difficulty
    topicTags { name }
  }
}
"""


def fetch_problem(slug):
    body = json.dumps({"query": QUERY, "variables": {"slug": slug}}).encode()
    req = urllib.request.Request(
        "https://leetcode.com/graphql",
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://leetcode.com",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.load(resp)
    q = data["data"]["question"]
    return {
        "id": q["questionFrontendId"],
        "title": q["title"],
        "difficulty": q["difficulty"],
        "tags": [t["name"] for t in q["topicTags"]],
    }


def load_cache():
    if CACHE.exists():
        return json.loads(CACHE.read_text(encoding="utf-8"))
    return {}


def save_cache(cache):
    CACHE.parent.mkdir(exist_ok=True)
    CACHE.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def find_problem_folders():
    # LeetHub folders: 0021-merge-two-sorted-lists
    pattern = re.compile(r"^(\d+)-(.+)$")
    folders = []
    for p in ROOT.iterdir():
        m = p.is_dir() and pattern.match(p.name)
        if m:
            folders.append((p.name, m.group(2)))
    return sorted(folders)


def build_index(folders, cache):
    groups = defaultdict(list)
    for folder, slug in folders:
        info = cache.get(slug)
        if info:
            topics = {TAG_TO_TOPIC[t] for t in info["tags"] if t in TAG_TO_TOPIC}
            title = f'{info["id"].zfill(4)} {info["title"]}'
            diff = f' ({info["difficulty"]})'
        else:
            topics = set()
            title = folder
            diff = ""
        for topic in topics or {"Other"}:
            groups[topic].append(f"- [{title}](./{folder}){diff}")

    lines = []
    for topic in TOPIC_ORDER:
        if topic in groups:
            lines.append(f"### {topic} ({len(groups[topic])})")
            lines.extend(sorted(groups[topic]))
            lines.append("")
    return "\n".join(lines).strip()


def update_readme(index_text):
    text = README.read_text(encoding="utf-8")
    if START not in text or END not in text:
        print("README me markers nahi mile. Pehle START/END comments add karo.")
        return
    before = text.split(START)[0]
    after = text.split(END)[1]
    new_text = f"{before}{START}\n\n{index_text}\n\n{END}{after}"
    if new_text != text:
        README.write_text(new_text, encoding="utf-8")
        print("README updated.")
    else:
        print("README me koi change nahi.")


def main():
    cache = load_cache()
    folders = find_problem_folders()

    for folder, slug in folders:
        if slug in cache:
            continue
        try:
            cache[slug] = fetch_problem(slug)
            print(f"Fetched: {slug}")
            time.sleep(0.5)  # API pe load kam rakhne ke liye
        except Exception as e:
            # cache me save nahi karte, agli baar dobara try hoga
            print(f"Skip {slug}: {e}")

    save_cache(cache)
    update_readme(build_index(folders, cache))


if __name__ == "__main__":
    main()
