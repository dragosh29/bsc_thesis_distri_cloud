import tkinter as tk
from tkinter import messagebox, ttk
import requests
import threading
import time
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import networkx as nx

# ====== CONFIG ======
API_BASE = 'http://localhost:18000/api'
SETUP_URL = f'{API_BASE}/experiment/trust_validation/setup/'
KEEPALIVE_URL = f'{API_BASE}/experiment/trust_validation/keep_alive/'
TASK_URL = lambda tid: f'{API_BASE}/tasks/{tid}/'
SUBMIT_RESULT_URL = f'{API_BASE}/tasks/submit_result/'

# Experiment Constants
RESULT_MAPPING = {
    "LowNode-0": "evil",
    "LowNode-1": "evil",
    "LowNode-2": "evil",
    "HighNode-0": "42",
    "HighNode-1": "42",
}
TRUST_LOW = 3
TRUST_HIGH = 7.0
ALL_NODE_NAMES = list(RESULT_MAPPING.keys())

class ValidationExperimentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Trust Validation Experiment")

        # ─── ttk STYLE ──────────────────────────────────────────────────────────────
        style = ttk.Style()
        style.theme_use('alt')
        style.configure('TButton',
                        font=('Segoe UI', 11),
                        padding=(8, 4))
        style.configure('TEntry',
                        font=('Segoe UI', 11),
                        padding=(4, 4))
        style.map('TButton',
                  background=[('active', '#4a90e2'), ('!active', '#357ab7')],
                  foreground=[('active', 'white'),     ('!active', 'white')])

        try:
            self.root.state('zoomed')
        except:
            pass

        # ─── INTERNAL STATE ────────────────────────────────────────────────────────
        self.nodes = {}
        self.task_id = ""
        self.assignment_edges = []
        self.result_edges = []
        self.validated_output = None
        self.trust_score = None
        self.final_status = None
        self.keepalive_running = False
        self.trust_sums = {}
        self.trust_fracs = {}

        # ─── LAYOUT ────────────────────────────────────────────────────────────────
        self.frame = ttk.Frame(self.root, padding=10)
        self.frame.grid(row=0, column=0, sticky="nsew")

        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.frame.columnconfigure(2, weight=1)
        for r in range(7):
            self.frame.rowconfigure(r, weight=0)
        self.frame.rowconfigure(7, weight=1)

        self._make_widgets()
        self._make_canvas()
        self.draw_graph()


    def _make_widgets(self):
        self.setup_btn = ttk.Button(self.frame, text="1. Setup Experiment", command=self.setup_experiment)
        self.setup_btn.grid(row=1, column=0, columnspan=2, sticky="ew", pady=2)

        self.keepalive_btn = ttk.Button(self.frame, text="2. Start Keep-Alive", command=self.start_keepalive, state='disabled')
        self.keepalive_btn.grid(row=2, column=0, columnspan=2, sticky="ew", pady=2)

        self.assignment_btn = ttk.Button(self.frame, text="3. Confirm Assignment", command=self.check_assignments, state='disabled')
        self.assignment_btn.grid(row=3, column=0, columnspan=2, sticky="ew", pady=2)

        self.submit_results_btn = ttk.Button(self.frame, text="4. Submit Results", command=self.submit_results, state='disabled')
        self.submit_results_btn.grid(row=4, column=0, columnspan=2, sticky="ew", pady=2)

        self.show_final_btn = ttk.Button(self.frame, text="5. Show Final Result", command=self.show_final_result, state='disabled')
        self.show_final_btn.grid(row=5, column=0, columnspan=2, sticky="ew", pady=2)

        self.status_var = tk.StringVar(value="Waiting for setup.")
        self.status_label = ttk.Label(self.frame, textvariable=self.status_var, foreground="darkblue")
        self.status_label.grid(row=6, column=0, columnspan=2, sticky="w", pady=(10,0))


    def _make_canvas(self):
        self.fig, self.ax = plt.subplots(figsize=(8,8), constrained_layout=True)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame)
        w = self.canvas.get_tk_widget()
        w.grid(row=0, column=2, rowspan=8, sticky="nsew", padx=10, pady=10)

    def draw_graph(self):
        import numpy as np

        self.ax.clear()
        G = nx.DiGraph()

        # ─── PARAMETERS ──────────────────────────────────────────────────────────
        N = len(ALL_NODE_NAMES)
        R = 6.0
        node_size = 8000
        task_size = 10000
        center = (0, 0)

        pos = {}
        colors = []

        G.add_node("TASK")
        pos["TASK"] = center

        if self.nodes:
            for i, name in enumerate(ALL_NODE_NAMES):
                theta = 2 * np.pi * i / N
                x, y = R * np.cos(theta), R * np.sin(theta)
                pos[name] = (x, y)
                G.add_node(name)
                colors.append("limegreen" if "High" in name else "tomato")

            nx.draw_networkx_nodes(G, pos, ax=self.ax,
                                   nodelist=ALL_NODE_NAMES, node_color=colors,
                                   node_size=node_size, linewidths=2, edgecolors='black')

            for name in ALL_NODE_NAMES:
                x, y = pos[name]
                self.ax.text(x, y, name,
                             fontsize=12, fontweight='bold',
                             ha='center', va='center',
                             color='white')

        nx.draw_networkx_nodes(G, pos, ax=self.ax,
                               nodelist=["TASK"], node_color='#90caf9',
                               node_shape='s', node_size=task_size,
                               linewidths=2, edgecolors='black')
        self.ax.text(0, 0, "TASK",
                     fontsize=20, fontweight='bold',
                     ha='center', va='center',
                     color='white')

        if self.assignment_edges and not self.result_edges:
            for src, _ in self.assignment_edges:
                nx.draw_networkx_edges(G, pos, edgelist=[(src, "TASK")], ax=self.ax,
                                       edge_color='gray', style='dotted', width=2,
                                       arrowstyle='-|>', arrowsize=15,
                                       connectionstyle='arc3,rad=0.1')
                x, y = (pos[src][0] + pos["TASK"][0]) / 2, (pos[src][1] + pos["TASK"][1]) / 2
                self.ax.text(x, y, "assigned",
                             fontsize=12, color='gray',
                             ha='center', va='center',
                             bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

        if self.result_edges:
            for src, _, result in self.result_edges:
                if self.final_status is None:
                    col = 'darkgray'
                else:
                    col = 'forestgreen' if result == self.validated_output else 'crimson'

                nx.draw_networkx_edges(G, pos, edgelist=[(src, "TASK")], ax=self.ax,
                                       edge_color=col, style='solid', width=2,
                                       arrowstyle='-|>', arrowsize=15,
                                       connectionstyle='arc3,rad=0.1')
                x, y = (pos[src][0] + pos["TASK"][0]) / 2, (pos[src][1] + pos["TASK"][1]) / 2
                self.ax.text(x, y, result,
                             fontsize=12, color=col,
                             ha='center', va='center',
                             bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

        if self.trust_sums:
            x0, y0 = pos['TASK']
            dy = 0.8

            self.ax.text(
                x0, y0 - R - 1,
                f"Trust 42: {self.trust_sums['42']:.1f}",
                ha='center', va='top',
                color='forestgreen',
                fontsize=12,
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'),
            )
            self.ax.text(
                x0, y0 - R - 1 - dy,
                f"Trust evil: {self.trust_sums['evil']:.1f}",
                ha='center', va='top',
                color='crimson',
                fontsize=12,
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'),
            )

        self.ax.set_title("Trust Validation Experiment", fontsize=20, fontweight='bold')
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        self.ax.set_xlim(-R - 2, R + 2)
        self.ax.set_ylim(-R - 2, R + 2)

        self.canvas.draw()


    def setup_experiment(self):
        try:
            resp = requests.post(SETUP_URL, timeout=10, data={"trust_low": TRUST_LOW, "trust_high": TRUST_HIGH})
            if resp.status_code != 201:
                raise Exception(resp.json())
            data = resp.json()
            self.task_id = data["task_id"]
            self.nodes = {n["name"]: n for n in data["nodes"]}
            self.status_var.set("Status: Experiment setup complete. Nodes created.")
            self.keepalive_btn.config(state='normal')
            self.assignment_btn.config(state='normal')
            self.step = 1
            self.draw_graph()
        except Exception as e:
            messagebox.showerror("API Error", f"Failed to setup experiment:\n{e}")

    def start_keepalive(self):
        if self.keepalive_running:
            return
        self.keepalive_running = True
        self.keepalive_btn.config(state='disabled')
        self.status_var.set("Status: Keep-alive started (every 60s).")
        self.keepalive_thread = threading.Thread(target=self.keep_nodes_alive_loop, daemon=True)
        self.keepalive_thread.start()

    def keep_nodes_alive_loop(self):
        while self.keepalive_running:
            try:
                resp = requests.post(KEEPALIVE_URL, json={"node_names": ALL_NODE_NAMES}, timeout=5)
                if resp.status_code != 200:
                    print("Keep-alive failed", resp.json())
            except Exception as e:
                print("Keep-alive exception", e)
            time.sleep(60)

    def check_assignments(self):
        if not self.task_id:
            messagebox.showerror("Input Error", "No Task ID set!")
            return
        try:
            resp = requests.get(TASK_URL(self.task_id), timeout=10)
            if resp.status_code != 200:
                raise Exception(resp.json())
            task = resp.json()
            assigned = []
            for name in ALL_NODE_NAMES:
                node = self.nodes.get(name)
                assigned.append((name, self.task_id))
            self.assignment_edges = assigned
            self.status_var.set("Status: Assignments confirmed. Proceed to result submission.")
            self.submit_results_btn.config(state='normal')
            self.draw_graph()
        except Exception as e:
            messagebox.showerror("API Error", f"Error fetching assignments:\n{e}")

    def submit_results(self):
        self.result_edges = []
        errors = []
        for name, result in RESULT_MAPPING.items():
            node = self.nodes.get(name)
            if not node:
                errors.append(f"Node {name} not found!")
                continue
            payload = {
                "task_id": self.task_id,
                "node_id": node["id"],
                "result": {"output": result},
            }
            try:
                resp = requests.post(SUBMIT_RESULT_URL, json=payload, timeout=10)
                if resp.status_code != 200:
                    errors.append(f"{name}: {resp.json()}")
                else:
                    self.result_edges.append((name, self.task_id, result))
            except Exception as e:
                errors.append(f"{name}: {e}")
        if errors:
            messagebox.showerror("Submission Error", "\n".join(map(str, errors)))
        else:
            self.status_var.set("Status: Results submitted. Show final result!")
            self.show_final_btn.config(state='normal')
        self.draw_graph()

    def show_final_result(self):
        try:
            resp = requests.get(TASK_URL(self.task_id), timeout=10)
            if resp.status_code != 200:
                raise Exception(resp.json())
            task = resp.json()
            self.final_status = task["status"]
            self.validated_output = None
            self.trust_score = None
            if "result" in task and task["result"]:
                self.validated_output = task["result"].get("validated_output")
                self.trust_score = task["result"].get("trust_score")
            from collections import defaultdict
            trust_sums = defaultdict(float)
            for name, _, result in self.result_edges:
                trust_sums[result] += self.nodes[name]['trust_index']
            total = sum(trust_sums.values())
            trust_fracs = {r: trust_sums[r] / total for r in trust_sums}

            # 2) Store for drawing (so draw_graph can pick them up)
            self.trust_sums = trust_sums
            self.trust_fracs = trust_fracs

            # 3) Update status bar to include the numbers:
            frac_42 = trust_fracs.get("42", 0)
            frac_evil = trust_fracs.get("evil", 0)
            self.status_var.set(
                f"Final status: {self.final_status} | "
                f"42→{trust_sums['42']} ({frac_42:.2%}), "
                f"evil→{trust_sums['evil']} ({frac_evil:.2%}) | "
                f"Validated: {self.validated_output}, Score: {self.trust_score:.2f}"
            )
            self.draw_graph()

        except Exception as e:
            messagebox.showerror("API Error", f"Error fetching task result:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ValidationExperimentApp(root)
    root.mainloop()
