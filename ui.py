"""Tkinter GUI for Halting Boundary Tracker."""
import tkinter as tk
from tkinter import ttk, messagebox
from tm_simulator import TuringMachine, TMError, parse_rules, BLANK
from examples import EXAMPLES

NAVY, BG, CELL, MAX_K = "#1e3a5f", "#f4f6fa", 46, 100000
COLORS = {"READY": "#64748b", "RUNNING": "#2563eb", "HALTED": "#15803d",
          "TIMEOUT": "#c2410c", "NO TRANSITION": "#b91c1c"}
INFO = ("What is the Halting Problem?\n"
        "The Halting Problem asks whether it is possible to determine, for every Turing Machine and input, "
        "whether the machine will eventually halt. Alan Turing proved that no general algorithm can solve "
        "this problem for all possible machines.\n\n"
        "This application does not solve the general Halting Problem. Instead, it performs a bounded "
        "simulation. It executes the machine for at most K steps. If the machine halts within this boundary, "
        "HALTED is reported. Otherwise, TIMEOUT is reported. TIMEOUT does NOT prove the machine never halts; "
        "it only means it did not halt within the tested boundary K.")


class App:
    def __init__(self, root):
        self.root, self.tm, self.job, self.running, self.shown = root, None, None, False, 0
        root.title("Halting Boundary Tracker")
        root.geometry("1100x800")
        root.minsize(920, 680)
        self._build()
        self.load_example()

    # ---------- layout ----------
    def _build(self):
        r = self.root
        r.configure(bg=BG)
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("TFrame", background=BG)
        s.configure("TLabel", background=BG, font=("Segoe UI", 10))
        s.configure("TLabelframe", background=BG)
        s.configure("TLabelframe.Label", background=BG, foreground=NAVY, font=("Segoe UI", 10, "bold"))
        s.configure("TButton", font=("Segoe UI", 10), padding=5)
        s.configure("Accent.TButton", background=NAVY, foreground="white")
        s.map("Accent.TButton", background=[("active", "#2c5282")])
        r.columnconfigure(0, weight=1)
        r.rowconfigure(1, weight=1)

        head = tk.Frame(r, bg=NAVY)
        head.grid(row=0, column=0, sticky="ew")
        tk.Label(head, text="Halting Boundary Tracker", bg=NAVY, fg="white",
                 font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=16, pady=(10, 0))
        tk.Label(head, text="Bounded Turing Machine Simulation", bg=NAVY, fg="#bcd0ea",
                 font=("Segoe UI", 11)).pack(anchor="w", padx=16, pady=(0, 10))

        body = ttk.Frame(r)
        body.grid(row=1, column=0, sticky="nsew", padx=10, pady=8)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # --- left: configuration ---
        cfg = ttk.LabelFrame(body, text="Turing Machine Configuration", padding=10)
        cfg.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        self.tape, self.start = tk.StringVar(), tk.StringVar(value="q0")
        self.halt, self.k = tk.StringVar(value="HALT"), tk.StringVar(value="100")
        for i, (lbl, var) in enumerate([("Input tape", self.tape), ("Start state", self.start),
                                        ("Halting state", self.halt), ("Max steps K", self.k)]):
            ttk.Label(cfg, text=lbl).grid(row=i, column=0, sticky="w", pady=3)
            ttk.Entry(cfg, textvariable=var, width=22, font=("Consolas", 11)).grid(row=i, column=1, pady=3, padx=(8, 0))
        ttk.Label(cfg, text="Transition rules\n(state,read -> state,write,move)").grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(8, 2))
        self.rules = tk.Text(cfg, width=30, height=10, font=("Consolas", 11), undo=True)
        self.rules.grid(row=5, column=0, columnspan=2, sticky="nsew")
        cfg.rowconfigure(5, weight=1)
        ttk.Label(cfg, text="L = left, R = right, _ = blank, # = comment", foreground="#64748b").grid(
            row=6, column=0, columnspan=2, sticky="w")
        self.ex_box = ttk.Combobox(cfg, state="readonly", values=[e["name"] for e in EXAMPLES])
        self.ex_box.current(0)
        self.ex_box.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(10, 3))
        bf = ttk.Frame(cfg)
        bf.grid(row=8, column=0, columnspan=2, sticky="ew")
        bf.columnconfigure((0, 1), weight=1)
        buttons = [("Run (F5)", self.run, "Accent.TButton"), ("Step (F10)", self.step, "TButton"),
                   ("Start (F6)", self.toggle_auto, "TButton"), ("Reset (Ctrl+R)", self.reset, "TButton"),
                   ("Clear", self.clear, "TButton"), ("Load Example", self.load_example, "TButton")]
        for i, (t, cmd, sty) in enumerate(buttons):
            b = ttk.Button(bf, text=t, command=cmd, style=sty)
            b.grid(row=i // 2, column=i % 2, sticky="ew", padx=2, pady=2)
            if t.startswith("Start"):
                self.auto_btn = b
        for key, fn in (("<F5>", self.run), ("<F6>", self.toggle_auto), ("<F10>", self.step),
                        ("<Control-r>", self.reset)):
            r_ = self.root
            r_.bind(key, lambda e, f=fn: f())

        # --- right: simulation ---
        right = ttk.Frame(body)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(3, weight=1)
        self.status_lbl = tk.Label(right, text="READY", fg="white", font=("Segoe UI", 22, "bold"), pady=6)
        self.status_lbl.grid(row=0, column=0, sticky="ew")
        self.msg = ttk.Label(right, wraplength=600, justify="left")
        self.msg.grid(row=1, column=0, sticky="ew", pady=4)
        right.bind("<Configure>", lambda e: self.msg.config(wraplength=max(200, e.width - 20)))

        info = ttk.LabelFrame(right, text="Machine Status", padding=8)
        info.grid(row=2, column=0, sticky="ew")
        self.v = {n: tk.StringVar() for n in ("Steps Executed", "Maximum Steps (K)", "Current State",
                                              "Head Position", "Current Symbol", "Tape")}
        for i, (n, var) in enumerate(self.v.items()):
            ttk.Label(info, text=n + ":", font=("Segoe UI", 10, "bold")).grid(row=i // 2, column=(i % 2) * 2, sticky="w", padx=(0, 6))
            ttk.Label(info, textvariable=var, font=("Consolas", 11)).grid(row=i // 2, column=(i % 2) * 2 + 1, sticky="w", padx=(0, 24))
        self.pb = ttk.Progressbar(info, mode="determinate")
        self.pb.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        self.pb_lbl = ttk.Label(info, font=("Consolas", 10))
        self.pb_lbl.grid(row=3, column=3, sticky="w")

        lower = ttk.Frame(right)
        lower.grid(row=3, column=0, sticky="nsew", pady=6)
        lower.columnconfigure(0, weight=1)
        lower.rowconfigure(1, weight=1)
        tf = ttk.LabelFrame(lower, text="Tape (▼ marks the head)", padding=4)
        tf.grid(row=0, column=0, sticky="ew")
        tf.columnconfigure(0, weight=1)
        self.cv = tk.Canvas(tf, height=100, bg="white", highlightthickness=0)
        self.cv.grid(row=0, column=0, sticky="ew")
        hs = ttk.Scrollbar(tf, orient="horizontal", command=self.cv.xview)
        hs.grid(row=1, column=0, sticky="ew")
        self.cv.configure(xscrollcommand=hs.set)
        xf = ttk.LabelFrame(lower, text="Execution Trace", padding=4)
        xf.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        xf.columnconfigure(0, weight=1)
        xf.rowconfigure(0, weight=1)
        self.trace = tk.Text(xf, height=8, font=("Consolas", 10), state="disabled", bg="#fbfcfe")
        self.trace.grid(row=0, column=0, sticky="nsew")
        ys = ttk.Scrollbar(xf, command=self.trace.yview)
        ys.grid(row=0, column=1, sticky="ns")
        self.trace.configure(yscrollcommand=ys.set)
        sp = ttk.Frame(right)
        sp.grid(row=4, column=0, sticky="ew")
        ttk.Label(sp, text="Auto speed (steps/sec):").pack(side="left")
        self.speed = tk.Scale(sp, from_=1, to=20, orient="horizontal", bg=BG, highlightthickness=0, length=220)
        self.speed.set(4)
        self.speed.pack(side="left", padx=8)

        box = ttk.LabelFrame(body, text="Educational Information", padding=6)
        box.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        box.columnconfigure(0, weight=1)
        t = tk.Text(box, height=7, wrap="word", font=("Segoe UI", 10), bg=BG, relief="flat")
        t.insert("1.0", INFO)
        t.tag_add("h", "1.0", "1.end")
        t.tag_config("h", font=("Segoe UI", 10, "bold"), foreground=NAVY)
        t.config(state="disabled")
        t.grid(row=0, column=0, sticky="ew")

    # ---------- actions ----------
    def make(self):
        try:
            start, halt = self.start.get().strip(), self.halt.get().strip()
            if not start:
                raise TMError("Please enter a start state.")
            if not halt:
                raise TMError("Please enter a halting state.")
            try:
                k = int(self.k.get().strip())
            except ValueError:
                raise TMError("K must be a whole number (for example 100).")
            if k < 0:
                raise TMError("K cannot be negative.")
            if k > MAX_K:
                raise TMError(f"K is limited to {MAX_K} in this GUI to keep it responsive.")
            rules = parse_rules(self.rules.get("1.0", "end"))
            return TuringMachine(self.tape.get().strip(), start, halt, rules, k)
        except TMError as e:
            messagebox.showerror("Invalid input", str(e))
            return None

    def _ensure(self):
        if self.tm is None:
            self.tm = self.make()
            self.shown = 0
        return self.tm

    def step(self):
        self._pause()
        return self._do_step()

    def _do_step(self):
        tm = self._ensure()
        if tm is None or tm.finished:
            return False
        tm.step()
        self.refresh()
        return not tm.finished

    def run(self):
        self._pause()
        tm = self._ensure()
        if tm:
            tm.run()
            self.refresh()

    def toggle_auto(self):
        if self.running:
            return self._pause()
        tm = self._ensure()
        if tm is None or tm.finished:
            return
        self.running = True
        self.auto_btn.config(text="Pause (F6)")
        self._tick()

    def _tick(self):
        if not self.running:
            return
        if self._do_step():
            self.job = self.root.after(1000 // self.speed.get(), self._tick)
        else:
            self._pause()

    def _pause(self):
        self.running = False
        if self.job:
            self.root.after_cancel(self.job)
            self.job = None
        self.auto_btn.config(text="Start (F6)")

    def reset(self):
        self._pause()
        self.tm = self.make()
        self.shown = 0
        self._clear_trace()
        self.refresh()

    def clear(self):
        self._pause()
        self.tape.set("")
        self.start.set("q0")
        self.halt.set("HALT")
        self.k.set("100")
        self.rules.delete("1.0", "end")
        self.tm, self.shown = None, 0
        self._clear_trace()
        self.refresh()

    def load_example(self):
        e = EXAMPLES[self.ex_box.current()]
        self._pause()
        self.tape.set(e["tape"]); self.start.set(e["start"]); self.halt.set(e["halt"]); self.k.set(str(e["k"]))
        self.rules.delete("1.0", "end")
        self.rules.insert("1.0", e["rules"])
        self.tm, self.shown = None, 0
        self._clear_trace()
        self.refresh()

    # ---------- display ----------
    def _clear_trace(self):
        self.trace.config(state="normal")
        self.trace.delete("1.0", "end")
        self.trace.config(state="disabled")

    def refresh(self):
        tm = self.tm
        status = tm.status if tm else "READY"
        k = tm.k if tm else self.k.get().strip()
        self.status_lbl.config(text=status, bg=COLORS[status])
        if tm:
            sym, state, steps, head = tm.read, tm.state, tm.steps, tm.head
            cells, tape = tm.cells, tm.tape_text()
        else:
            sym, state, steps, head = "-", self.start.get().strip(), 0, 0
            cells = {i: c for i, c in enumerate(self.tape.get().replace(" ", "")) if c != BLANK}
            tape = self.tape.get().strip() or BLANK
            if cells:
                sym = cells.get(0, BLANK)
        msgs = {
            "READY": "Simulation has not started. Press Step, Run or Start.",
            "RUNNING": "Simulation in progress...",
            "HALTED": f"Machine reached the halting state after {steps} steps (within K = {k}).",
            "TIMEOUT": f"Machine did not halt within K = {k} steps. This does NOT prove the machine never halts; "
                       "it only means it did not halt within the tested boundary.",
            "NO TRANSITION": f"No rule exists for state '{state}' reading '{sym}'. The machine is stuck.",
        }
        self.msg.config(text=msgs[status])
        for name, val in zip(self.v, (steps, k, state, head, sym, tape)):
            self.v[name].set(str(val))
        try:
            kk = max(int(k), 1)
        except ValueError:
            kk = 1
        self.pb.config(maximum=kk, value=min(steps, kk))
        self.pb_lbl.config(text=f"{steps} / {k}")
        if tm and len(tm.trace) > self.shown:
            self.trace.config(state="normal")
            self.trace.insert("end", "\n".join(tm.trace[self.shown:]) + "\n")
            self.trace.see("end")
            self.trace.config(state="disabled")
            self.shown = len(tm.trace)
        self.draw_tape(cells, head)

    def draw_tape(self, cells, head):
        cv = self.cv
        cv.delete("all")
        pos = list(cells) + [head]
        lo, hi = min(pos) - 6, max(pos) + 6
        hi = max(hi, lo + 20)
        for p in range(lo, hi + 1):
            x = (p - lo) * CELL + 10
            on = p == head
            cv.create_rectangle(x, 28, x + CELL, 68, fill="#fde68a" if on else "#eef2f7",
                                outline=NAVY if on else "#94a3b8", width=3 if on else 1)
            cv.create_text(x + CELL / 2, 48, text=cells.get(p, BLANK), font=("Consolas", 16, "bold"))
            cv.create_text(x + CELL / 2, 82, text=str(p), font=("Consolas", 8), fill="#64748b")
            if on:
                cv.create_text(x + CELL / 2, 14, text="▼", fill="#b91c1c", font=("Segoe UI", 12))
        total = (hi - lo + 1) * CELL + 20
        cv.config(scrollregion=(0, 0, total, 100))
        cv.update_idletasks()
        cv.xview_moveto(max(0, (head - lo) * CELL - cv.winfo_width() / 2 + CELL / 2) / total)
