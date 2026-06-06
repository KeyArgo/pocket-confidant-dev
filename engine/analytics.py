from collections import Counter, defaultdict
from datetime import datetime
import sqlite3


STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "up", "about", "into", "over", "after",
    "is", "are", "was", "were", "be", "been", "being", "have", "has",
    "had", "do", "does", "did", "will", "would", "could", "should",
    "may", "might", "shall", "can", "need", "dare", "ought", "used",
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves",
    "you", "your", "yours", "yourself", "yourselves", "he", "him",
    "his", "himself", "she", "her", "hers", "herself", "it", "its",
    "itself", "they", "them", "their", "theirs", "themselves",
    "what", "which", "who", "whom", "this", "that", "these", "those",
    "not", "no", "nor", "so", "very", "just", "as", "if", "than",
    "then", "now", "once", "here", "there", "when", "where", "why",
    "how", "all", "each", "every", "both", "few", "more", "most",
    "other", "some", "such", "only", "own", "same", "too", "also",
    "get", "got", "go", "goes", "went", "see", "seen", "know",
    "like", "make", "take", "think", "come", "came", "want", "give",
    "use", "find", "tell", "ask", "work", "seem", "feel", "try",
    "leave", "call", "keep", "let", "begin", "show", "hear", "play",
    "run", "move", "live", "said", "say", "says", "thing", "things",
    "one", "two", "time", "way", "people", "day", "year", "back",
    "well", "even", "still", "much", "really", "long", "new", "good",
    "first", "last", "great", "little", "right", "old", "big",
    "high", "different", "small", "large", "next", "early", "young",
    "important", "because", "while", "since", "before", "after",
    "though", "although", "until", "during", "always", "never",
    "ever", "often", "sometimes", "usually", "maybe",
}


def get_entries_per_period(db_path, period="day"):
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT day FROM entries ORDER BY ts").fetchall()
    conn.close()

    counts = defaultdict(int)
    for (day_str,) in rows:
        dt = datetime.fromisoformat(day_str)
        if period == "week":
            label = f"{dt.isocalendar()[0]}-W{dt.isocalendar()[1]:02d}"
        elif period == "month":
            label = f"{dt.year}-{dt.month:02d}"
        else:
            label = day_str
        counts[label] += 1

    labels = sorted(counts.keys())
    return {"labels": labels, "counts": [counts[l] for l in labels]}


def get_writing_streak(db_path):
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT DISTINCT day FROM entries ORDER BY day").fetchall()
    conn.close()

    days = [r[0] for r in rows]
    total_days = len(days)

    if total_days == 0:
        return {"current": 0, "longest": 0, "total_days": 0}

    longest = 1
    current_run = 1
    for i in range(1, len(days)):
        prev = datetime.fromisoformat(days[i - 1])
        cur = datetime.fromisoformat(days[i])
        if (cur - prev).days == 1:
            current_run += 1
            if current_run > longest:
                longest = current_run
        else:
            current_run = 1

    today = datetime.now().date()
    last = datetime.fromisoformat(days[-1]).date()
    if (today - last).days > 1:
        current = 0
    else:
        current = 1
        for i in range(len(days) - 2, -1, -1):
            d = datetime.fromisoformat(days[i]).date()
            if (last - d).days == current:
                current += 1
            else:
                break

    return {"current": current, "longest": longest, "total_days": total_days}


def get_top_topics(db_path, limit=15):
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT text FROM entries").fetchall()
    conn.close()

    counter = Counter()
    for (text,) in rows:
        words = text.lower().split()
        for w in words:
            w = w.strip(".,!?;:\"'()[]{}")
            if len(w) > 2 and w not in STOP_WORDS and w.isalpha():
                counter[w] += 1

    most_common = counter.most_common(limit)
    return {
        "topics": [w for w, _ in most_common],
        "counts": [c for _, c in most_common],
    }


def get_busiest_days(db_path):
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT ts FROM entries").fetchall()
    conn.close()

    dow = defaultdict(int)
    hod = defaultdict(int)
    for (ts,) in rows:
        dt = datetime.fromtimestamp(ts)
        dow[dt.strftime("%A")] += 1
        hod[dt.hour] += 1

    return {
        "day_of_week": dict(sorted(dow.items(), key=lambda x: x[1], reverse=True)),
        "hour_of_day": dict(sorted(hod.items())),
    }


def get_entry_stats(db_path):
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT COUNT(*), MIN(day), MAX(day), AVG(LENGTH(text) - LENGTH(REPLACE(text, ' ', '')) + 1) FROM entries"
    ).fetchone()
    conn.close()

    total, first, last, avg = row
    return {
        "total_entries": total,
        "first_entry": first or "",
        "last_entry": last or "",
        "avg_words": round(avg) if avg else 0,
    }
