import json
import re
import shutil
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
README = ROOT / "README.md"
CACHE = ROOT / "data" / "topic-cache.json"
START = "<!-- TOPIC-INDEX-START -->"
END = "<!-- TOPIC-INDEX-END -->"

# True = LeetHub ka apna "LeetCode Topics" block README se hata do
# (move ke baad uske links 404 dete hain; hamara index wahi kaam karta hai)
STRIP_LEETHUB_BLOCK = True
LEETHUB_BLOCK = re.compile(
    r"<!--+\s*LeetCode Topics Start\s*-->.*?<!--+\s*LeetCode Topics End\s*-->\s*",
    re.S,
)

# LeetCode ke saare tags -> topic folder. Naya/anjaan tag aaye to wo "Other" me jayega.
TAG_TO_TOPIC = {
    # Arrays
    "Array": "Arrays", "Prefix Sum": "Arrays", "Counting": "Arrays",
    "Line Sweep": "Arrays", "Enumeration": "Arrays", "Simulation": "Arrays",
    "Matrix": "Matrix",
    # Strings
    "String": "Strings", "String Matching": "Strings", "Suffix Array": "Strings",
    # Hashing
    "Hash Table": "Hashing", "Hash Function": "Hashing", "Rolling Hash": "Hashing",
    # Two pointers / sliding window
    "Two Pointers": "Two-Pointers-Sliding-Window",
    "Sliding Window": "Two-Pointers-Sliding-Window",
    # Linked list
    "Linked List": "LinkedList", "Doubly-Linked List": "LinkedList",
    # Stack / Queue
    "Stack": "Stack-Queue", "Monotonic Stack": "Stack-Queue",
    "Queue": "Stack-Queue", "Monotonic Queue": "Stack-Queue",
    # Binary search
    "Binary Search": "Binary-Search",
    # Sorting
    "Sorting": "Sorting", "Merge Sort": "Sorting", "Counting Sort": "Sorting",
    "Bucket Sort": "Sorting", "Radix Sort": "Sorting", "Quickselect": "Sorting",
    # Recursion
    "Recursion": "Recursion-Backtracking", "Backtracking": "Recursion-Backtracking",
    "Divide and Conquer": "Recursion-Backtracking",
    # Trees
    "Tree": "Trees", "Binary Tree": "Trees", "Binary Search Tree": "Trees",
    # Graphs
    "Graph": "Graphs", "Depth-First Search": "Graphs", "Breadth-First Search": "Graphs",
    "Topological Sort": "Graphs", "Union Find": "Graphs", "Shortest Path": "Graphs",
    "Minimum Spanning Tree": "Graphs", "Strongly Connected Component": "Graphs",
    "Biconnected Component": "Graphs", "Eulerian Circuit": "Graphs",
    # Heap
    "Heap (Priority Queue)": "Heap",
    # Greedy
    "Greedy": "Greedy",
    # DP
    "Dynamic Programming": "Dynamic-Programming", "Memoization": "Dynamic-Programming",
    # Math
    "Math": "Math", "Number Theory": "Math", "Combinatorics": "Math",
    "Geometry": "Math", "Probability and Statistics": "Math", "Game Theory": "Math",
    "Brainteaser": "Math", "Randomized": "Math", "Reservoir Sampling": "Math",
    "Rejection Sampling": "Math",
    # Bits
    "Bit Manipulation": "Bit-Manipulation", "Bitmask": "Bit-Manipulation",
    # Trie / advanced
    "Trie": "Trie",
    "Segment Tree": "Advanced-Data-Structures",
    "Binary Indexed Tree": "Advanced-Data-Structures",
    "Ordered Set": "Advanced-Data-Structures",
    # Design
    "Design": "Design", "Iterator": "Design", "Data Stream": "Design",
    "Concurrency": "Design",
    # Database
    "Database": "Database", "Shell": "Database",
}

# README me topics isi order me dikhenge
TOPIC_ORDER = [
    "Arrays", "Strings", "Hashing", "Two-Pointers-Sliding-Window", "LinkedList",
    "Stack-Queue", "Binary-Search", "Sorting", "Recursion-Backtracking", "Trees",
    "Graphs", "Heap", "Greedy", "Dynamic-Programming", "Matrix", "Math",
    "Bit-Manipulation", "Trie", "Advanced-Data-Structures", "Design",
    "Database", "Other",
]

# Folder kis topic me jayega: pehla match jeetta hai.
# Specific topics pehle, generic (Strings/Arrays) sabse baad me.
PRIMARY_PRIORITY = [
    "Database", "Design", "Trie", "Advanced-Data-Structures",
    "Dynamic-Programming", "LinkedList", "Trees", "Graphs", "Heap",
    "Stack-Queue", "Binary-Search", "Two-Pointers-Sliding-Window",
    "Recursion-Backtracking", "Greedy", "Bit-Manipulation",
    "Matrix", "Math", "Hashing", "Strings", "Arrays", "Sorting",
]

PATTERN = re.compile(r"^(\d+)-(.+)$")

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


def slug_of(path):
    return PATTERN.match(path.name).group(2)


def find_problem_folders():
    """Root ke LeetHub folders + topic folders ke andar ke problem folders."""
    skip = {"data", "node_modules"}
    topic_dirs = [
        d for d in ROOT.iterdir()
        if d.is_dir() and not d.name.startswith(".") and d.name not in skip
        and not PATTERN.match(d.name)
    ]
    search_dirs = [ROOT] + topic_dirs
    found = []
    for d in search_dirs:
        for p in d.iterdir():
            if p.is_dir() and PATTERN.match(p.name):
                found.append(p)
    return sorted(found, key=lambda p: (p.name, str(p)))


def topics_of(info):
    return {TAG_TO_TOPIC[t] for t in info["tags"] if t in TAG_TO_TOPIC}


def primary_topic(info):
    topics = topics_of(info)
    for t in PRIMARY_PRIORITY:
        if t in topics:
            return t
    return "Other"


def organize_folders(folders, cache):
    """Har folder ko uske primary topic folder me le jao.
    Agar wahan pehle se hai (LeetHub ne dobara root me banaya), to merge kar do."""
    for p in folders:
        if not p.exists():
            continue
        info = cache.get(slug_of(p))
        if not info:
            continue  # tags nahi mile, jahan hai wahin rehne do
        target = ROOT / primary_topic(info) / p.name
        if p.resolve() == target.resolve():
            continue
        target.parent.mkdir(exist_ok=True)
        if target.exists():
            shutil.copytree(p, target, dirs_exist_ok=True)  # naye files overwrite
            shutil.rmtree(p)
            print(f"Merged: {p.relative_to(ROOT)} -> {target.relative_to(ROOT)}")
        else:
            shutil.move(str(p), str(target))
            print(f"Moved: {p.relative_to(ROOT)} -> {target.relative_to(ROOT)}")


def build_index(folders, cache):
    groups = defaultdict(list)
    for p in folders:
        link = "./" + p.relative_to(ROOT).as_posix()
        info = cache.get(slug_of(p))
        if info:
            topics = topics_of(info)
            title = f'{info["id"].zfill(4)} {info["title"]}'
            diff = f' ({info["difficulty"]})'
        else:
            topics = set()
            title = p.name
            diff = ""
        # ek problem ke saare topics me index entry (folder ek hi jagah rehta hai)
        for topic in topics or {"Other"}:
            groups[topic].append(f"- [{title}]({link}){diff}")

    lines = []
    for topic in TOPIC_ORDER + sorted(set(groups) - set(TOPIC_ORDER)):
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
    if STRIP_LEETHUB_BLOCK:
        new_text = LEETHUB_BLOCK.sub("", new_text)
    if new_text != text:
        README.write_text(new_text, encoding="utf-8")
        print("README updated.")
    else:
        print("README me koi change nahi.")


def ensure_topic_folders():
    """Saare topic folders (Other ko chhodkar) ek chhoti README.md ke saath banao."""
    for topic in TOPIC_ORDER:
        if topic == "Other":
            continue
        folder = ROOT / topic
        folder.mkdir(exist_ok=True)
        readme = folder / "README.md"
        if not readme.exists():
            readme.write_text(
                f"# {topic}\n\nIs folder me {topic} topic ki LeetCode problems hain.\n",
                encoding="utf-8",
            )
            print(f"Created folder: {topic}/")


def main():
    cache = load_cache()
    ensure_topic_folders()
    folders = find_problem_folders()

    for p in folders:
        slug = slug_of(p)
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
    organize_folders(folders, cache)
    folders = find_problem_folders()  # move ke baad naye paths
    update_readme(build_index(folders, cache))


if __name__ == "__main__":
    main()
