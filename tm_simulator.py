"""Turing Machine core with a bounded execution limit K (no GUI code here)."""
BLANK = "_"


class TMError(Exception):
    """Raised for any invalid user input; message is shown to the user."""


def parse_rules(text):
    """Parse lines like 'q0,1 -> q0,1,R' into {(state, read): (next, write, move)}."""
    rules = {}
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#")[0].strip()          # '#' starts a comment
        if not line:
            continue
        if line.count("->") != 1:
            raise TMError(f"Line {n}: expected 'state,read -> state,write,move' but got '{raw.strip()}'.")
        left, right = (p.strip() for p in line.split("->"))
        l = [x.strip() for x in left.split(",")]
        r = [x.strip() for x in right.split(",")]
        if len(l) != 2 or len(r) != 3 or not all(l + r):
            raise TMError(f"Line {n}: invalid syntax. Use 'state,read -> state,write,move' (e.g. q0,1 -> q0,1,R).")
        if len(l[1]) != 1 or len(r[1]) != 1:
            raise TMError(f"Line {n}: read/write symbols must be a single character (use _ for blank).")
        move = r[2].upper()
        if move not in ("L", "R"):
            raise TMError(f"Line {n}: invalid movement '{r[2]}'. Use L or R.")
        key = (l[0], l[1])
        if key in rules:
            raise TMError(f"Line {n}: duplicate transition for state '{l[0]}' reading '{l[1]}'.")
        rules[key] = (r[0], r[1], move)
    if not rules:
        raise TMError("Transition rules are empty. Add at least one rule.")
    return rules


class TuringMachine:
    FINAL = ("HALTED", "TIMEOUT", "NO TRANSITION")

    def __init__(self, tape, start, halt, rules, k):
        self.initial = tape.replace(" ", "")
        self.start, self.halt, self.rules, self.k = start, halt, rules, k
        self.reset()

    def reset(self):
        self.cells = {i: c for i, c in enumerate(self.initial) if c != BLANK}
        self.state, self.head, self.steps = self.start, 0, 0
        self.status, self.trace, self.last_rule = "READY", [], ""

    @property
    def read(self):
        return self.cells.get(self.head, BLANK)

    @property
    def finished(self):
        return self.status in self.FINAL

    def bounds(self):
        pos = list(self.cells) + [self.head]
        return min(pos), max(pos)

    def tape_text(self):
        lo, hi = self.bounds()
        return "".join(self.cells.get(i, BLANK) for i in range(lo, hi + 1))

    def _log(self):
        note = f"   (applied {self.last_rule})" if self.last_rule else ""
        self.trace.append(f"Step {self.steps}: State={self.state}, Head={self.head}, Read={self.read}{note}")

    def step(self):
        """Execute exactly one transition following the halting-boundary flowchart."""
        if self.finished:
            return self.status
        if not self.trace:
            self._log()                                   # Step 0 configuration
        if self.state == self.halt:                       # Is current state HALT?
            self.status = "HALTED"
            return self.status
        if self.steps >= self.k:                          # Is step >= K?
            self.status = "TIMEOUT"
            return self.status
        rule = self.rules.get((self.state, self.read))
        if rule is None:
            self.status = "NO TRANSITION"
            return self.status
        nxt, write, move = rule
        self.last_rule = f"{self.state},{self.read} -> {nxt},{write},{move}"
        if write == BLANK:
            self.cells.pop(self.head, None)
        else:
            self.cells[self.head] = write
        self.head += 1 if move == "R" else -1
        self.state = nxt
        self.steps += 1
        self._log()
        if self.state == self.halt:
            self.status = "HALTED"
        elif self.steps >= self.k:
            self.status = "TIMEOUT"
        else:
            self.status = "RUNNING"
        return self.status

    def run(self):
        while not self.finished:
            self.step()
        return self.status
