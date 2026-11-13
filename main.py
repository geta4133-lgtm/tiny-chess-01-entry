"""Tiny Chess 4KB Engine for make.fun.

SPDX-License-Identifier: MIT
"""

import json, os, sys, urllib.error, urllib.request

ENV_URL = os.environ.get("MAKEFUN_ENV_URL") or sys.exit("MAKEFUN_ENV_URL is not set")
VAL = {"p": 100, "n": 320, "b": 330, "r": 500, "q": 900, "k": 20000}

PST_P = [
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0
]

PST_N = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]


def post(path, body):
    req = urllib.request.Request(
        ENV_URL + path,
        data=json.dumps(body).encode(),
        headers={"content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as res:
            return json.load(res)
    except urllib.error.HTTPError as e:
        sys.exit(f"{path}: HTTP {e.code} {e.read().decode(errors='replace')}")


def parse_board(fen):
    b = {}
    for r, row in enumerate(fen.split()[0].split("/")):
        f = 0
        for c in row:
            if c.isdigit():
                f += int(c)
            else:
                b["abcdefgh"[f] + str(8 - r)] = c
                f += 1
    return b


def eval_board(b, color):
    s = 0
    for sq, p in b.items():
        f = ord(sq[0]) - ord("a")
        r = int(sq[1]) - 1
        v = VAL.get(p.lower(), 0)
        idx = (7 - r) * 8 + f if p.isupper() else r * 8 + f
        bonus = PST_P[idx] if p.lower() == "p" else (PST_N[idx] if p.lower() == "n" else 0)
        tot = v + bonus
        s += tot if p.isupper() else -tot
    return s if color == "w" else -s


def move_score(m, b):
    src, dst = m[:2], m[2:4]
    mover = b.get(src, "p").lower()
    vic = b.get(dst)
    if not vic and mover == "p" and src[0] != dst[0]:
        vic = "p"
    score = VAL.get(vic.lower(), 0) * 10 - VAL.get(mover, 0) if vic else 0
    if len(m) == 5:
        score += VAL.get(m[4].lower(), 0)
    return score


def choose(fen, legal):
    if not legal:
        return None
    c = fen.split()[1] if len(fen.split()) > 1 else "w"
    b = parse_board(fen)
    sorted_moves = sorted(legal, key=lambda m: move_score(m, b), reverse=True)
    best_m, best_s = sorted_moves[0], -999999
    for m in sorted_moves:
        src, dst = m[:2], m[2:4]
        nb = dict(b)
        p = nb.pop(src, "P" if c == "w" else "p")
        if len(m) == 5:
            p = m[4].upper() if c == "w" else m[4].lower()
        nb[dst] = p
        s = -eval_board(nb, "b" if c == "w" else "w") + move_score(m, b)
        if s > best_s:
            best_s, best_m = s, m
    return best_m


def main():
    while True:
        g = post("/game", {})
        if g["status"] == "done":
            break
        while g["status"] == "your_move":
            mv = choose(g["fen"], g["legal_moves"])
            g = post("/move", {"game": g["game"], "move": mv})
        print(f"game {g['game']}: {g['outcome']} by {g['reason']}", file=sys.stderr)
    print(f"done: {g.get('wins')} won, {g.get('draws')} drawn, {g.get('losses')} lost", file=sys.stderr)


if __name__ == "__main__":
    main()
