def text_to_csv(inp, out):
    import re
    import csv

    pg = ""
    ch = ""
    rows = []

    with open(inp, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            m = re.match(r"--- Page (\d+) ---", line)
            if m:
                pg = m.group(1)
                continue

            if "CHAPTER" in line:
                ch = line
                continue

            m = re.match(r"(\d+[A-Z]?)\.\s*(.+)", line)
            if m:
                sec = m.group(1)
                title = m.group(2)
                rows.append([sec, title, ch, pg])

    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Section", "Title", "Chapter", "Page"])
        writer.writerows(rows)