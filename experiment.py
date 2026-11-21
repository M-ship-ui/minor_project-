"""Demonstration experiment on a synthetic lost-and-found dataset (fixed seed)."""
import json
import random
import re
import statistics
import time

from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from matching import build_text, clean, score_all

rng = random.Random(42)

TYPES = [
    ("wallet", ["wallet", "purse"], ["black", "brown", "tan"], ["Fastrack", "Tommy", ""],
     ["with an ID card inside", "with some cash", "with a zip pocket", "with a metro card"]),
    ("water bottle", ["water bottle", "flask"], ["blue", "silver", "green", "steel"], ["Milton", "Cello", ""],
     ["with a dented cap", "with a sticker", "with a strap"]),
    ("laptop charger", ["laptop charger", "adapter"], ["black"], ["HP", "Dell", "Lenovo"],
     ["with a long cable", "with a frayed wire", "in a pouch"]),
    ("calculator", ["scientific calculator", "calculator"], ["black", "blue"], ["Casio fx-991", "Casio fx-82", ""],
     ["with a cover", "with a name written inside", "with a cracked corner"]),
    ("ID card", ["student ID card", "identity card"], ["blue", "red"], [""],
     ["with a lanyard", "in a plastic holder", "with a photo"]),
    ("umbrella", ["umbrella", "brolly"], ["black", "red", "blue", "checked"], [""],
     ["with a wooden handle", "with a broken rib", "foldable"]),
    ("earphones", ["earphones", "earbuds", "headphones"], ["black", "white", "red"], ["Boat", "Realme", "Sony"],
     ["with a case", "with a tangled wire", "wireless"]),
    ("backpack", ["backpack", "bag", "rucksack"], ["black", "grey", "blue", "red"],
     ["Wildcraft", "Skybags", "American Tourister"],
     ["with a laptop sleeve", "with a torn strap", "with a keychain"]),
    ("keys", ["keys", "key bunch"], ["silver"], [""],
     ["with a red keychain", "with a scooter key", "with a hostel room key"]),
    ("notebook", ["notebook", "lab record"], ["blue", "green", "yellow"], [""],
     ["with a name on the cover", "with circuit diagrams", "with a spiral binding"]),
    ("spectacles", ["spectacles", "glasses"], ["black", "silver", "brown"], [""],
     ["with a case", "with thick lenses", "with a cracked arm"]),
    ("power bank", ["power bank", "charging bank"], ["black", "white", "blue"], ["Mi", "Ambrane", "Realme"],
     ["with a short cable", "with a scratch", "10000 mAh"]),
    ("pen drive", ["pen drive", "USB drive"], ["black", "red", "silver"], ["SanDisk", "HP", ""],
     ["with a cap", "with a keyring", "32 GB"]),
]

COLOR_SYN = {
    "black": "dark", "blue": "navy", "silver": "grey", "steel": "metallic",
    "white": "off-white", "red": "maroon", "green": "olive", "brown": "tan",
    "tan": "light brown", "yellow": "mustard", "grey": "ash"
}
PLACES = ["library", "canteen", "Lab 3", "Block A corridor", "auditorium", "bus stop",
          "hostel gate", "sports ground", "seminar hall", "parking area", "CSE department", "workshop"]
PLACE_VAR = {p: [f"near the {p}", f"outside the {p}", f"{p} area"] for p in PLACES}
NOISE = ["handed over to the security desk", "found this morning", "please contact",
         "no owner nearby", "left on a bench", ""]


def make_item():
    t = rng.choice(TYPES)
    return {
        "type": t,
        "color": rng.choice(t[2]),
        "brand": rng.choice(t[3]),
        "mark": rng.choice(t[4]),
        "noun": rng.choice(t[1]),
        "place": rng.choice(PLACES)
    }


def lost_report(it):
    parts = ["Lost my", it["color"], it["brand"], it["noun"],
             it["mark"] if rng.random() < 0.8 else "", f"near the {it['place']}"]
    desc = " ".join(p for p in parts if p)
    return {"name": it["noun"], "category": "Lost", "description": desc, "location": it["place"]}


def found_report(it, same=True):
    noun = it["noun"] if rng.random() < 0.5 else rng.choice(it["type"][1])
    color = it["color"]
    if rng.random() < 0.25:
        color = COLOR_SYN.get(color, color)
    brand = it["brand"] if rng.random() < 0.7 else ""
    mark = it["mark"] if rng.random() < 0.7 else ""
    place = it["place"] if rng.random() < 0.6 else rng.choice(PLACES)
    loc = rng.choice(PLACE_VAR[place])
    desc = " ".join(p for p in ["Found a", color, brand, noun, mark, loc, rng.choice(NOISE)] if p)
    return {"name": noun, "category": "Found", "description": desc, "location": place}


def hard_negative(it):
    t = it["type"]
    other = dict(it)
    others = [c for c in t[2] if c != it["color"]] or t[2]
    other["color"] = rng.choice(others)
    brands = [b for b in t[3] if b != it["brand"]] or t[3]
    other["brand"] = rng.choice(brands)
    other["mark"] = rng.choice(t[4])
    other["place"] = rng.choice(PLACES)
    return other


N = 200
items = [make_item() for _ in range(N)]
lost = [lost_report(i) for i in items]
found_true = [found_report(i) for i in items]
found_hard = [found_report(hard_negative(i)) for i in items[:100]]
found_rand = [found_report(make_item()) for _ in range(100)]
found = found_true + found_hard + found_rand
truth = list(range(N))  # lost k matches found k

docs_l = [build_text(x) for x in lost]
docs_f = [build_text(x) for x in found]


def sim_matrix(kind):
    if kind == "count":
        v = CountVectorizer(stop_words="english")
    elif kind == "tfidf":
        v = TfidfVectorizer(stop_words="english")
    elif kind == "tfidf_sub":
        v = TfidfVectorizer(stop_words="english", sublinear_tf=True)
    elif kind == "tfidf_bi":
        v = TfidfVectorizer(stop_words="english", sublinear_tf=True, ngram_range=(1, 2))
    elif kind == "jaccard":
        sets_l = [set(d.split()) for d in docs_l]
        sets_f = [set(d.split()) for d in docs_f]
        return [[len(a & b) / len(a | b) if (a | b) else 0.0 for b in sets_f] for a in sets_l]
    v.fit(docs_l + docs_f)
    return cosine_similarity(v.transform(docs_l), v.transform(docs_f)).tolist()


def rank_metrics(S):
    t1 = t3 = t5 = 0
    rr = 0.0
    for i, row in enumerate(S):
        order = sorted(range(len(row)), key=lambda j: row[j], reverse=True)
        pos = order.index(truth[i]) + 1
        t1 += pos <= 1
        t3 += pos <= 3
        t5 += pos <= 5
        rr += 1.0 / pos
    n = len(S)
    return {"top1": t1 / n, "top3": t3 / n, "top5": t5 / n, "mrr": rr / n}


methods = {
    "count": "Word counts + cosine (no IDF)",
    "jaccard": "Jaccard overlap of word sets",
    "tfidf": "TF-IDF (unigrams) + cosine",
    "tfidf_sub": "TF-IDF (sublinear tf) + cosine",
    "tfidf_bi": "TF-IDF (unigrams + bigrams) + cosine"
}
result = {
    "n_lost": N,
    "n_found": len(found),
    "n_true": N,
    "pairs": N * len(found),
    "methods": {}
}
mats = {}
for k in methods:
    mats[k] = sim_matrix(k)
    result["methods"][k] = {"label": methods[k], **rank_metrics(mats[k])}

# threshold table for the chosen method (sublinear TF-IDF)
S = mats["tfidf_sub"]
thr = []
for t in [0.10, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60]:
    tp = fp = 0
    for i, row in enumerate(S):
        for j, s in enumerate(row):
            if s >= t:
                if j == truth[i]:
                    tp += 1
                else:
                    fp += 1
    fn = N - tp
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / N
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    thr.append({"t": t, "tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f1})
result["thresholds"] = thr

# per-lost-report precision at the reported threshold: how many suggestions shown
cnt = [sum(1 for s in row if s >= 0.25) for row in S]
result["suggestions_per_report_t025"] = {
    "mean": statistics.mean(cnt),
    "max": max(cnt),
    "zero": sum(1 for c in cnt if c == 0)
}

# examples
ex = []
for i in (3, 17, 42, 88):
    row = S[i]
    order = sorted(range(len(row)), key=lambda j: row[j], reverse=True)
    ex.append({
        "lost": lost[i]["description"],
        "top": found[order[0]]["description"],
        "score": round(row[order[0]], 3),
        "correct": order[0] == truth[i],
        "true_rank": order.index(truth[i]) + 1
    })
result["examples"] = ex

# failures
fails = [i for i, row in enumerate(S) if sorted(range(len(row)), key=lambda j: row[j], reverse=True)[0] != truth[i]]
result["top1_failures"] = len(fails)

fx = []
for i in fails[:3]:
    row = S[i]
    order = sorted(range(len(row)), key=lambda j: row[j], reverse=True)
    fx.append({
        "lost": lost[i]["description"],
        "top": found[order[0]]["description"],
        "score": round(row[order[0]], 3),
        "true": found[truth[i]]["description"],
        "true_score": round(row[truth[i]], 3)
    })
result["failure_examples"] = fx

if __name__ == "__main__":
    with open("exp.json", "w") as f:
        json.dump(result, f, indent=2)
    print("Experiment completed. Output written to exp.json.")
    print("Methods performance:")
    for k, v in result["methods"].items():
        print(f"  {k:10s} Top-1: {v['top1']*100:.1f}%  Top-3: {v['top3']*100:.1f}%  Top-5: {v['top5']*100:.1f}%  MRR: {v['mrr']:.4f}")
