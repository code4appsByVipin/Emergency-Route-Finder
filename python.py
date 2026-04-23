import tkinter as tk
from tkinter import ttk, messagebox, Canvas
import random
import json
import os
import time
from ctypes import cdll, c_char_p, c_bool, c_int

# --- Constants for Futuristic Aesthetics ---

# Define the futuristic Neon Blue and Deep Space Black palette
COLOR_PRIMARY = "#0A0A1F"      # Deep Space Black (Main Background)
COLOR_SECONDARY = "#00FFFF"    # Neon Cyan/Blue (Accents, Text, Highlights)
COLOR_BACKGROUND = "#15152A"   # Dark Blue/Black (Control Panel BG)
COLOR_TEXT = "#E0FFFF"         # Near White/Light Cyan (High Visibility Text)
COLOR_WARNING = "#FF00FF"      # Neon Magenta (Incidents, Critical Actions)
COLOR_SUCCESS = "#00FF7F"      # Neon Green (Route Highlight, Success)
COLOR_HOSPITAL = "#FF4500"     # Bright Orange-Red (Enhanced Hospital Icon)
COLOR_POLICE = "#33CCFF"       # Bright Light Blue (Enhanced Police Icon)
COLOR_MAP_BG = "#0A0A1F"       # Map Background
COLOR_CRITICALITY = "#FF6600"  # Bright Orange for Delta

# Futuristic, technical font
FONT_TITLE = ("Consolas", 24, "bold")
FONT_HEADING = ("Consolas", 14, "bold")
FONT_NORMAL = ("Consolas", 11)
FONT_TOOLTIP = ("Consolas", 9)

# Realism Constants (Unchanged)
MAX_DISTANCE_UNIT = 100
DISTANCE_SCALING = 0.5
INCIDENT_SPEED_KMPH = 5

SPEED_PROFILES = {
    "Normal Traffic (40 kph)": 40,
    "Rush Hour (High Congestion - 25 kph)": 25,
    "Night/Off-Peak (55 kph)": 55
}

# --- Graph Data Initialization (Unchanged) ---

def generate_unique_node_names(count):
    prefixes = ['Maple', 'Oak', 'Pine', 'Cedar', 'Willow', 'River', 'Mountain', 'Valley', 'City', 'Grand', 'North', 'South', 'Express', 'Tech', 'Finance', 'Trade', 'Unity', 'Green', 'Golden', 'Iron']
    suffixes = ['Junction', 'Crossing', 'Square', 'Bridge', 'Terminal', 'Center', 'Market', 'Plaza', 'Gate', 'View', 'Park', 'Station', 'Hub', 'Zone', 'District', 'Exchange', 'Point', 'Loop', 'Street']
    
    names = set()
    while len(names) < count:
        p = random.choice(prefixes)
        s = random.choice(suffixes)
        names.add(f"{p} {s}")
        
    return list(names)

NUM_GENERIC_NODES = 120
GENERIC_NODE_NAMES = generate_unique_node_names(NUM_GENERIC_NODES)

# Initial fixed/special nodes
DEHRADUN_COORDINATES = {
    "H-Doon Hospital": (10, 80), "L-Clock Tower": (20, 70), "P-Kotwali Station": (30, 60),
    "H-Max Hospital": (90, 10), "R-Rajpur Road": (40, 50), "S-Welham Site": (50, 40)
}

# Edge metadata structure for Python visualization
DEHRADUN_GRAPH_EDGES = [] 
ALL_NODES = []
# Node categorization for map icons
NODE_TYPES = {'H': {'color': COLOR_HOSPITAL, 'symbol': 'HOSPITAL'}, 
              'P': {'color': COLOR_POLICE, 'symbol': 'POLICE'}, 
              'S': {'color': COLOR_SECONDARY, 'symbol': 'SITE'}, 
              'L': {'color': COLOR_TEXT, 'symbol': 'LANDMARK'}, 
              'R': {'color': COLOR_TEXT, 'symbol': 'ROAD'}}

def calculate_distance(u, v):
    """Calculates pseudo-distance (Euclidean) between two coordinate points, scaled to km."""
    x1, y1 = DEHRADUN_COORDINATES[u]
    x2, y2 = DEHRADUN_COORDINATES[v]
    return (((x1 - x2)**2 + (y1 - y2)**2)**0.5) * DISTANCE_SCALING

def calculate_time_minutes(distance_km, speed_kmph):
    """Calculates travel time in minutes."""
    return (distance_km / speed_kmph) * 60 if speed_kmph > 0 else float('inf')

def initialize_graph_metadata():
    global DEHRADUN_COORDINATES, DEHRADUN_GRAPH_EDGES, ALL_NODES
    
    initial_speed = SPEED_PROFILES["Normal Traffic (40 kph)"]

    for i in range(NUM_GENERIC_NODES):
        current = GENERIC_NODE_NAMES[i]
        x = ((i % 11) * 8 + random.uniform(0, 2)) % 100
        y = 100 - ((i // 11) * 8 + random.uniform(0, 2)) % 100
        DEHRADUN_COORDINATES[current] = (x, y)

    ALL_NODES = sorted(list(DEHRADUN_COORDINATES.keys()))

    connections = [
        ("H-Doon Hospital", "L-Clock Tower"), ("L-Clock Tower", "P-Kotwali Station"),
        ("P-Kotwali Station", "H-Max Hospital"), ("H-Max Hospital", "R-Rajpur Road"),
        ("R-Rajpur Road", "L-Clock Tower"), ("L-Clock Tower", GENERIC_NODE_NAMES[0]),
        (GENERIC_NODE_NAMES[-1], "H-Max Hospital")
    ]
    
    for i in range(NUM_GENERIC_NODES):
        current = GENERIC_NODE_NAMES[i]
        if i < NUM_GENERIC_NODES - 1: 
            connections.append((current, GENERIC_NODE_NAMES[i+1]))
        if i < NUM_GENERIC_NODES - 10: 
            connections.append((current, GENERIC_NODE_NAMES[i+10]))
        if i % 5 == 0:
            rand_target = random.choice(GENERIC_NODE_NAMES)
            if current != rand_target:
                connections.append((current, rand_target))

    for start, end in connections:
        dist = calculate_distance(start, end)
        time = calculate_time_minutes(dist, initial_speed)
        
        if dist < 0.5: continue

        for u, v in [(start, end), (end, start)]:
            exists = any((e['u'] == u and e['v'] == v) for e in DEHRADUN_GRAPH_EDGES)
            if not exists:
                 DEHRADUN_GRAPH_EDGES.append({
                    'u': u, 'v': v, 
                    'dist_km': dist, 
                    'initial_t': time, 
                    'current_t': time, 
                    'incident': False, 
                    'line_id': None
                })

initialize_graph_metadata()

# --- C++ Library Wrapper (ctypes) ---

class CppEngine:
    """Wrapper for the external C++ library performing A* pathfinding."""
    def __init__(self):
        self.library = None
        self.load_library()

    def load_library(self):
        """Attempts to load the shared C++ library."""
        if os.name == 'nt': lib_name = "route_finder.dll"
        else: lib_name = "route_finder.so"

        try:
            # NOTE: This assumes the C++ library is built and available.
            self.library = cdll.LoadLibrary(os.path.abspath(lib_name))
            self.library.find_route_from_library.restype = c_char_p
            self.library.find_route_from_library.argtypes = [c_char_p, c_char_p]
            self.library.free_route_string.argtypes = [c_char_p]
            self.library.update_cpp_edge.argtypes = [c_char_p, c_char_p, c_int]
            self.library.update_cpp_edge.restype = c_bool
            print("C++ Library loaded successfully.")
        except OSError:
            self.library = None
            print("WARNING: C++ Library not found. Running in simulation fallback mode.")
            
    def find_route(self, start_node, end_node):
        """Calls the C++ A* function or runs a simulation (if C++ is unavailable)."""
        
        if self.library:
            # C++ engine logic
            start_b = start_node.encode('utf-8')
            end_b = end_node.encode('utf-8')
            result_ptr = self.library.find_route_from_library(start_b, end_b)
            json_data = result_ptr.decode('utf-8')
            self.library.free_route_string(result_ptr)
            
            try:
                result = json.loads(json_data)
                return result
            except json.JSONDecodeError:
                print(f"ERROR: Failed to decode JSON from C++: {json_data[:100]}")
                return {'total_cost': float('inf'), 'segments': []}
        
        # --- Simulation Mode Fallback ---
        else:
            nominal_speed = app._get_current_nominal_speed() if 'app' in globals() else SPEED_PROFILES["Normal Traffic (40 kph)"]
            segments = []
            total_time = float('inf')
            
            try:
                # Simple simulation of a path
                path_nodes = [start_node, random.choice(GENERIC_NODE_NAMES), end_node]
                
                for i in range(len(path_nodes) - 1):
                    u, v = path_nodes[i], path_nodes[i+1]
                    dist = calculate_distance(u, v)
                    
                    # Find the current edge time based on incident status
                    edge_data = next((e for e in DEHRADUN_GRAPH_EDGES if e['u'] == u and e['v'] == v), None)
                    if not edge_data: continue

                    time_cost = edge_data['current_t']
                    
                    segments.append({'from': u, 'to': v, 'cost': int(time_cost)})

                if segments:
                    total_time = sum(s['cost'] for s in segments)
            except Exception as e:
                print(f"Simulation Error: {e}")

            return {'total_cost': total_time, 'segments': segments}
            
    def update_edge_weight(self, u, v, new_weight):
        """Calls the C++ function to dynamically update the graph, or simulates update."""
        if self.library:
            return self.library.update_cpp_edge(u.encode('utf-8'), v.encode('utf-8'), new_weight)
        else:
             # Simulation mode update (Not necessary here as Python dicts handle the weights directly in the main class)
             return True

# --- Application Class ---
class EmergencyRouteFinder(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Emergency Dispatch | A* Network Control (Futuristic UI)")
        self.geometry("1200x800")
        self.configure(bg=COLOR_PRIMARY)
        
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self._configure_styles()
        
        self.cpp_engine = CppEngine()
        self.nodes = DEHRADUN_COORDINATES
        
        self.selected_start = tk.StringVar(self)
        self.selected_end = tk.StringVar(self)
        self.incident_node_var = tk.StringVar(self)
        self.time_of_day_var = tk.StringVar(self)
        
        self.current_route_segments = []
        self.incident_active = False
        self.log_counter = 0

        # State for baseline tracking and pulsing animation
        self.nominal_time = 0.0
        self._last_start = ""
        self._last_end = ""
        self._pulse_size = 15
        self._pulse_direction = 1
        
        self._create_widgets()
        
        # Set default values
        self.time_of_day_var.set(list(SPEED_PROFILES.keys())[0])
        self.selected_start.set("H-Doon Hospital")
        self.selected_end.set("H-Max Hospital")
        self._last_speed_profile_key = self.time_of_day_var.get()
        self.incident_node_var.set(GENERIC_NODE_NAMES[0])
        
        # Bindings for map interactivity
        self.map_canvas.bind('<Motion>', self._handle_mouse_move)
        self.map_canvas.bind('<Leave>', self._clear_tooltip)
        
        # Bindings for route recalculation and baseline update
        self.selected_start.trace_add("write", self._update_coordinate_display)
        self.selected_end.trace_add("write", self._update_coordinate_display)
        self.time_of_day_var.trace_add("write", self._apply_speed_profile)
        
        self._last_start = self.selected_start.get()
        self._last_end = self.selected_end.get()
        self._calculate_nominal_baseline() # Initial baseline calculation
        
        self._draw_map()
        self.update_log("SYSTEM ONLINE | A* Module Initialized.", COLOR_SUCCESS)
        self._update_coordinate_display()
        
        self._pulse_highlight() # Start pulsing animation

    # --- Tooltip and Map Interactivity Logic ---
    def _handle_mouse_move(self, event):
        """Checks for nodes or edges near the mouse and displays a tooltip."""
        self._clear_tooltip()
        
        # Check Nodes
        for name, (x, y) in self.nodes.items():
            cx, cy = self._get_canvas_coords(x, y)
            if abs(event.x - cx) < 15 and abs(event.y - cy) < 15:
                # Node found
                self._show_node_tooltip(event.x, event.y, name, x, y)
                return

        # Check Edges (Iterate through all edges to check distance to line segment)
        for edge_data in DEHRADUN_GRAPH_EDGES:
            u, v = edge_data['u'], edge_data['v']
            x1, y1 = self.nodes.get(u)
            cx1, cy1 = self._get_canvas_coords(x1, y1)
            x2, y2 = self.nodes.get(v)
            cx2, cy2 = self._get_canvas_coords(x2, y2)
            
            # Simple bounding box check before complex distance calculation
            min_x, max_x = min(cx1, cx2), max(cx1, cx2)
            min_y, max_y = min(cy1, cy2), max(cy1, cy2)
            
            if min_x - 5 <= event.x <= max_x + 5 and min_y - 5 <= event.y <= max_y + 5:
                if self._distance_to_segment(event.x, event.y, cx1, cy1, cx2, cy2) < 5:
                    # Edge found
                    self._show_edge_tooltip(event.x, event.y, edge_data)
                    return

    def _distance_to_segment(self, px, py, x1, y1, x2, y2):
        """Calculates the minimum distance from point (px, py) to segment (x1, y1)-(x2, y2)."""
        l2 = (x2 - x1)**2 + (y2 - y1)**2
        if l2 == 0: return ((px - x1)**2 + (py - y1)**2)**0.5
        t = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / l2
        t = max(0, min(1, t))
        closest_x = x1 + t * (x2 - x1)
        closest_y = y1 + t * (y2 - y1)
        return ((px - closest_x)**2 + (py - closest_y)**2)**0.5

    def _show_node_tooltip(self, x, y, name, gx, gy):
        """Displays a tooltip for a map node."""
        text = f"NODE: {name}\nCOORD: ({gx:.0f}, {gy:.0f})"
        self._show_tooltip(x + 10, y - 5, text)

    def _show_edge_tooltip(self, x, y, edge_data):
        """Displays a tooltip for a map edge."""
        u, v = edge_data['u'], edge_data['v']
        dist = edge_data['dist_km']
        time = edge_data['current_t']
        incident = "CRITICAL BLOCK" if edge_data['incident'] else "NOMINAL"
        text = f"ROUTE: {u} -> {v}\nDIST: {dist:.2f} km\nTIME: {time:.0f} min\nSTATUS: {incident}"
        self._show_tooltip(x + 10, y - 5, text)
        
    def _show_tooltip(self, x, y, text):
        """Generic function to create the tooltip window."""
        self._clear_tooltip()
        
        self.tooltip = tk.Toplevel(self)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{self.winfo_rootx() + x}+{self.winfo_rooty() + y}")
        self.tooltip.config(bg=COLOR_WARNING, padx=5, pady=3)
        
        label = tk.Label(self.tooltip, text=text, bg=COLOR_BACKGROUND, fg=COLOR_TEXT, 
                         font=FONT_TOOLTIP, justify=tk.LEFT, relief=tk.SOLID, borderwidth=1, padx=5, pady=2)
        label.pack(ipady=2, ipadx=2)

    def _clear_tooltip(self, *args):
        """Destroys the active tooltip."""
        if hasattr(self, 'tooltip') and self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
            
    # --- Dynamic Highlight Animation ---
    def _pulse_highlight(self):
        """Creates a pulsing effect on the start/end node highlights."""
        start_node = self.selected_start.get()
        end_node = self.selected_end.get()
        
        if self.map_canvas.find_withtag("node_pulse"):
            self.map_canvas.delete("node_pulse")

        if start_node in self.nodes:
            self._draw_pulse_ring(start_node, COLOR_SUCCESS, self._pulse_size)
        
        if end_node in self.nodes:
            self._draw_pulse_ring(end_node, COLOR_WARNING, self._pulse_size)

        # Update pulse size and direction
        self._pulse_size += self._pulse_direction
        if self._pulse_size > 20 or self._pulse_size < 15:
            self._pulse_direction *= -1
            
        # Re-schedule the pulse animation
        self.after(100, self._pulse_highlight)

    def _draw_pulse_ring(self, name, color, size):
        """Draws the dynamic pulse ring for a given node."""
        x, y = self.nodes[name]
        cx, cy = self._get_canvas_coords(x, y)
        # Draw a translucent, larger ring
        self.map_canvas.create_oval(cx - size, cy - size, cx + size, cy + size, 
                                    outline=color, width=4, tags=("node_highlight", "node_pulse"),
                                    dash=(5, 5))
        self.map_canvas.tag_raise("node_pulse")

    # --- Utility Methods ---
    def _get_current_nominal_speed(self):
        """Returns the current nominal speed based on the Time of Day selection."""
        key = self.time_of_day_var.get()
        return SPEED_PROFILES.get(key, SPEED_PROFILES["Normal Traffic (40 kph)"])

    def _apply_speed_profile(self, *args):
        """Applies the new speed profile to the graph by resetting weights."""
        
        if self.incident_active:
             self.update_status("ERROR: Cannot change speed profile while an incident is active.", COLOR_WARNING)
             self.time_of_day_var.set(self._last_speed_profile_key)
             return
             
        new_speed = self._get_current_nominal_speed()
        
        for edge_data in DEHRADUN_GRAPH_EDGES:
            u, v, dist_km = edge_data['u'], edge_data['v'], edge_data['dist_km']
            new_time = calculate_time_minutes(dist_km, new_speed)
            
            self.cpp_engine.update_edge_weight(u, v, int(new_time))
            edge_data['current_t'] = new_time
            edge_data['initial_t'] = new_time # Reset initial time as well
        
        self._last_speed_profile_key = self.time_of_day_var.get()
        self.update_log(f"Traffic Profile set to: {self.time_of_day_var.get()}", COLOR_SECONDARY)
        
        # Recalculate baseline and route
        self._calculate_nominal_baseline()
        self._update_coordinate_display()
        self.calculate_route()

    def _calculate_nominal_baseline(self):
        """Calculates the baseline time for the current start/end nodes without any incidents."""
        
        start_node = self.selected_start.get()
        end_node = self.selected_end.get()
        
        if not start_node or not end_node:
            self.nominal_time = float('inf')
            return

        # 1. Temporarily clear incidents and set to nominal speed for true baseline
        current_active = self.incident_active
        self.clear_incidents(quiet=True) 

        # 2. Calculate route (using the function logic but tailored for baseline)
        try:
            result = self.cpp_engine.find_route(start_node, end_node)
            self.nominal_time = result.get('total_cost', float('inf'))
            
            if self.nominal_time != float('inf'):
                self.update_log(f"Baseline (Nominal) Time Calculated: {self.nominal_time:.0f} min.", COLOR_TEXT)
            
        except Exception as e:
            print(f"Baseline calculation error: {e}")
            self.nominal_time = float('inf')

        # 3. Restore incident state if it was active
        if current_active and self.incident_node_var.get():
             self.simulate_incident(node=self.incident_node_var.get(), quiet=True)

    def _configure_styles(self):
        # Configure styles for the Futuristic Theme
        self.style.configure('Main.TFrame', background=COLOR_PRIMARY)
        # Technical panel look with high-contrast border
        self.style.configure('Input.TFrame', background=COLOR_BACKGROUND, relief='solid', borderwidth=2, bordercolor=COLOR_SECONDARY)
        
        self.style.configure('TLabel', background=COLOR_BACKGROUND, foreground=COLOR_TEXT, font=FONT_NORMAL)
        self.style.configure('Title.TLabel', background=COLOR_PRIMARY, foreground=COLOR_SECONDARY, font=FONT_TITLE, padding=[15, 15])
        self.style.configure('Heading.TLabel', background=COLOR_BACKGROUND, foreground=COLOR_SECONDARY, font=FONT_HEADING, padding=5)

        # Button style (Neon Cyan/Blue accent)
        self.style.configure('TButton', font=FONT_HEADING, background=COLOR_SECONDARY, foreground=COLOR_PRIMARY, 
                             relief='flat', padding=12, borderwidth=0)
        self.style.map('TButton', 
                       background=[('active', COLOR_SUCCESS), ('pressed', COLOR_PRIMARY)],
                       foreground=[('active', COLOR_PRIMARY), ('pressed', COLOR_SECONDARY)])

        # Incident Button Style (Neon Magenta/Warning)
        self.style.configure('Warning.TButton', font=FONT_HEADING, background=COLOR_WARNING, foreground=COLOR_PRIMARY, 
                             relief='flat', padding=12, borderwidth=0)
        self.style.map('Warning.TButton', 
                       background=[('active', COLOR_SECONDARY), ('pressed', COLOR_PRIMARY)],
                       foreground=[('active', COLOR_PRIMARY), ('pressed', COLOR_WARNING)])

        # Combobox style to match the dark theme and look technical
        self.style.configure('TCombobox', font=FONT_NORMAL, padding=[8, 8])
        self.style.map('TCombobox',
                       fieldbackground=[('readonly', COLOR_PRIMARY)], 
                       selectbackground=[('readonly', COLOR_SECONDARY)],
                       selectforeground=[('readonly', COLOR_PRIMARY)],
                       foreground=[('readonly', COLOR_TEXT)],
                       background=[('readonly', COLOR_PRIMARY)])

        # Treeview (Output table) style
        self.style.configure('Treeview.Heading', font=FONT_HEADING, background=COLOR_BACKGROUND, foreground=COLOR_WARNING, padding=8)
        self.style.configure('Treeview', font=FONT_NORMAL, background=COLOR_PRIMARY, fieldbackground=COLOR_PRIMARY, foreground=COLOR_TEXT, rowheight=30)
        self.style.map('Treeview', background=[('selected', COLOR_SECONDARY)])

    def _create_widgets(self):
        # --- Top Header ---
        header_frame = ttk.Frame(self, style='Main.TFrame')
        header_frame.pack(fill='x', padx=20, pady=(15, 10))
        ttk.Label(header_frame, text="DYNAMIC A* PATHFINDING | EMERGENCE CONTROL", 
                  style='Title.TLabel', anchor='center', background=COLOR_PRIMARY).pack(fill='x')
        
        # Status/Toast Message Area 
        self.status_bar = ttk.Label(self, text="Status: Awaiting Dispatch Command", anchor='center', 
                                    background=COLOR_SECONDARY, foreground=COLOR_PRIMARY, font=FONT_HEADING)
        self.status_bar.pack(fill='x', padx=20, pady=(0, 10))

        # --- Main Content Frame (Grid Layout) ---
        main_frame = ttk.Frame(self, style='Main.TFrame')
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        main_frame.grid_columnconfigure(0, weight=2) 
        main_frame.grid_columnconfigure(1, weight=5) 
        main_frame.grid_rowconfigure(0, weight=1)
        
        # --- Left Control Panel & Log Container ---
        left_container = ttk.Frame(main_frame, style='Main.TFrame')
        left_container.grid(row=0, column=0, sticky='nsew', padx=(0, 20), pady=0)
        left_container.grid_rowconfigure(0, weight=2) # Input frame
        left_container.grid_rowconfigure(1, weight=1) # Log frame
        left_container.grid_columnconfigure(0, weight=1)

        # 1. Routing Inputs Frame
        control_panel = ttk.Frame(left_container, style='Input.TFrame', padding=25)
        control_panel.grid(row=0, column=0, sticky='nsew', pady=(0, 15))
        
        ttk.Label(control_panel, text="ROUTE COMMAND & TRAFFIC PROFILE", style='Heading.TLabel').pack(fill='x', pady=(0, 15))

        # Time of Day Control 
        ttk.Label(control_panel, text="[SYSTEM] Traffic Profile:", style='TLabel').pack(fill='x', pady=(5, 2))
        time_dropdown = ttk.Combobox(control_panel, textvariable=self.time_of_day_var, values=list(SPEED_PROFILES.keys()), state="readonly")
        time_dropdown.pack(fill='x', ipady=3)

        ttk.Label(control_panel, text="[DISPATCH] Start Location (NODE-U):", style='TLabel').pack(fill='x', pady=(15, 2))
        start_dropdown = ttk.Combobox(control_panel, textvariable=self.selected_start, values=ALL_NODES, state="readonly")
        start_dropdown.pack(fill='x', ipady=3)
        
        ttk.Label(control_panel, text="[DISPATCH] Destination (NODE-V):", style='TLabel').pack(fill='x', pady=(15, 2))
        end_dropdown = ttk.Combobox(control_panel, textvariable=self.selected_end, values=ALL_NODES, state="readonly")
        end_dropdown.pack(fill='x', ipady=3)

        # Coordinate/Heuristic Display 
        self.coord_label = ttk.Label(control_panel, text="Coords: --", style='TLabel', font=("Consolas", 10))
        self.coord_label.pack(fill='x', pady=(10, 0))
        
        self.heuristic_label = ttk.Label(control_panel, text="A* Heuristic (H): -- km", style='TLabel', font=("Consolas", 10, "bold"), foreground=COLOR_SUCCESS)
        self.heuristic_label.pack(fill='x', pady=(0, 20))

        self.calc_button = ttk.Button(control_panel, text="EXECUTE PATHFINDING COMMAND", command=self._start_calculation)
        self.calc_button.pack(fill='x', pady=(5, 20))

        # 2. Dynamic Routing Control
        ttk.Label(control_panel, text="DYNAMIC INTERVENTION MODULE", style='Heading.TLabel', foreground=COLOR_WARNING).pack(fill='x', pady=(0, 10))
        
        # Incident Location dropdown (Consistent styling)
        ttk.Label(control_panel, text="Incident Grid Reference:", style='TLabel').pack(fill='x', pady=(5, 2))
        incident_dropdown = ttk.Combobox(control_panel, textvariable=self.incident_node_var, values=ALL_NODES, state="readonly")
        incident_dropdown.pack(fill='x', ipady=3)
        
        # Warning/Critical Action Button
        ttk.Button(control_panel, text="TRIGGER MAJOR GRIDLOCK (REROUTE)", style='Warning.TButton', command=self.simulate_incident).pack(fill='x', pady=(15, 5))
        ttk.Button(control_panel, text="RESOLVE ALL INCIDENTS / RESET", command=self.clear_incidents).pack(fill='x', pady=5)
        
        # 3. Activity Log
        log_frame = ttk.Frame(left_container, style='Input.TFrame', padding=15)
        log_frame.grid(row=1, column=0, sticky='nsew')
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        ttk.Label(log_frame, text="ACTIVITY LOG (NETWORK MONITOR)", style='Heading.TLabel').grid(row=0, column=0, sticky='w', pady=(0, 5))
        
        self.log_tree = ttk.Treeview(log_frame, columns=('time', 'event'), show='headings', height=10)
        self.log_tree.heading('time', text='T-Stamp')
        self.log_tree.heading('event', text='Event Description')
        self.log_tree.column('time', width=80, anchor='center', stretch=tk.NO)
        self.log_tree.column('event', stretch=tk.YES)
        
        log_vsb = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_tree.yview)
        log_vsb.grid(row=1, column=1, sticky='ns')
        self.log_tree.configure(yscrollcommand=log_vsb.set)
        
        self.log_tree.grid(row=1, column=0, sticky='nsew')
        
        # --- Right Map/Output Panel ---
        output_frame = ttk.Frame(main_frame, style='Main.TFrame')
        output_frame.grid(row=0, column=1, sticky='nsew', pady=0)
        output_frame.grid_rowconfigure(0, weight=4)
        output_frame.grid_rowconfigure(1, weight=1)
        output_frame.grid_columnconfigure(0, weight=1)
        
        # 4. Map Canvas
        map_container = ttk.Frame(output_frame, style='Input.TFrame', padding=15)
        map_container.grid(row=0, column=0, sticky='nsew', pady=(0, 15))
        map_container.grid_rowconfigure(0, weight=1)
        map_container.grid_columnconfigure(0, weight=1)
        
        self.map_canvas = Canvas(map_container, bg=COLOR_MAP_BG, relief="flat", highlightthickness=1, highlightbackground=COLOR_SECONDARY)
        self.map_canvas.grid(row=0, column=0, sticky='nsew')
        self.map_canvas.bind("<Configure>", self._resize_map)
        
        # 5. Route Summary and Details Table
        details_container = ttk.Frame(output_frame, style='Input.TFrame', padding=15)
        details_container.grid(row=1, column=0, sticky='nsew')
        
        summary_frame = ttk.Frame(details_container, style='TLabel', height=50)
        summary_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(summary_frame, text="TRANSMISSION DATA:", style='Heading.TLabel').pack(side='left', padx=10)
        
        self.result_label_time = ttk.Label(summary_frame, text="ETA: -- min", style='Heading.TLabel', font=("Consolas", 18, "bold"), foreground=COLOR_SUCCESS)
        self.result_label_time.pack(side='left', padx=15)
        
        self.result_label_dist = ttk.Label(summary_frame, text="DIST: -- km", style='Heading.TLabel', font=("Consolas", 18, "bold"), foreground=COLOR_TEXT)
        self.result_label_dist.pack(side='left', padx=15)
        
        # New Criticality Score Display
        self.result_label_criticality = ttk.Label(summary_frame, text="STATUS: NOMINAL", style='Heading.TLabel', font=("Consolas", 18, "bold"), foreground=COLOR_TEXT)
        self.result_label_criticality.pack(side='left', padx=15)

        ttk.Label(details_container, text="[SUB-MODULE] Route Segment Details", style='Heading.TLabel').pack(anchor='w', pady=(5, 5))
        self.segments_tree = ttk.Treeview(details_container, columns=('from', 'to', 'dist', 'time', 'speed'), show='headings', height=4)
        self.segments_tree.heading('from', text='Source Location')
        self.segments_tree.heading('to', text='Target Location')
        self.segments_tree.heading('dist', text='Dist (km)')
        self.segments_tree.heading('time', text='Time (min)')
        self.segments_tree.heading('speed', text='Speed (kph)')
        
        self.segments_tree.column('dist', width=100, anchor='center')
        self.segments_tree.column('time', width=100, anchor='center')
        self.segments_tree.column('speed', width=100, anchor='center')
        self.segments_tree.pack(fill='both', expand=True)

    # --- Utility Methods ---
    def update_status(self, message, color):
        """Updates the top status bar/toast message."""
        self.status_bar.config(text=message, background=color, 
                               foreground=COLOR_PRIMARY if color != COLOR_SECONDARY and color != COLOR_WARNING else COLOR_PRIMARY)
        
    def update_log(self, message, color):
        """Adds an entry to the dispatch log."""
        self.log_counter += 1
        current_time = time.strftime("%H:%M:%S")
        self.log_tree.insert('', 0, values=(current_time, message), tags=(color,))
        self.log_tree.tag_configure(COLOR_SUCCESS, foreground=COLOR_SUCCESS)
        self.log_tree.tag_configure(COLOR_WARNING, foreground=COLOR_WARNING)
        self.log_tree.tag_configure(COLOR_SECONDARY, foreground=COLOR_SECONDARY)
        self.log_tree.tag_configure(COLOR_TEXT, foreground=COLOR_TEXT)
        self.log_tree.tag_configure(COLOR_CRITICALITY, foreground=COLOR_CRITICALITY)

    def _update_coordinate_display(self, *args):
        """Updates the display of the selected nodes' coordinates AND the A* heuristic, and recalculates baseline."""
        start_node = self.selected_start.get()
        end_node = self.selected_end.get()
        
        start_coords = self.nodes.get(start_node, ('--', '--'))
        end_coords = self.nodes.get(end_node, ('--', '--'))

        coord_text = f"U(X:{start_coords[0]:.0f}, Y:{start_coords[1]:.0f}) | V(X:{end_coords[0]:.0f}, Y:{end_coords[1]:.0f})"
        self.coord_label.config(text=coord_text)
        
        try:
            heuristic_dist = calculate_distance(start_node, end_node)
            self.heuristic_label.config(text=f"A* Heuristic (H): {heuristic_dist:.2f} km (Euclidean Distance)")
        except:
            self.heuristic_label.config(text="A* Heuristic (H): [CALC ERROR]")

        # Recalculate baseline if start or end changes
        if self._last_start != start_node or self._last_end != end_node:
            self._calculate_nominal_baseline()
            self._last_start = start_node
            self._last_end = end_node
            self.calculate_route()

    # --- Map Visualization Logic ---
    def _get_canvas_coords(self, x, y):
        """Transforms graph coordinates (0-100) to canvas coordinates."""
        padding = 50 
        c_width = self.map_canvas.winfo_width() - 2 * padding
        c_height = self.map_canvas.winfo_height() - 2 * padding
        canvas_x = int((x / 100) * c_width + padding)
        canvas_y = int((1 - y / 100) * c_height + padding)
        return canvas_x, canvas_y
        
    def _draw_node(self, name, cx, cy):
        """Draws a node with its specific icon/color based on type."""
        node_type_char = name.split('-')[0]
        is_special = node_type_char in NODE_TYPES
        
        tags = (name, "node") # Tag the node with its name for interactivity

        if is_special:
            node_info = NODE_TYPES[node_type_char]
            node_color = node_info['color']
            node_symbol = node_info['symbol'][0] 
            node_size = 12
            
            # Draw Outer Ring (Special Nodes are larger and neon-framed)
            self.map_canvas.create_oval(cx - node_size, cy - node_size, 
                                        cx + node_size, cy + node_size, 
                                        fill='', outline=node_color, width=3, tags=("node_special", *tags))
            
            # Draw Inner Fill and Symbol
            self.map_canvas.create_oval(cx - 6, cy - 6, cx + 6, cy + 6, 
                                        fill=node_color, outline='', tags=("node_fill", *tags))
            
            self.map_canvas.create_text(cx, cy, text=node_symbol, fill=COLOR_MAP_BG, 
                                        font=("Consolas", 8, "bold"), tags=("node_icon_special", *tags))
        else:
            # Generic Nodes (Smaller dot)
            node_color = COLOR_TEXT
            node_size = 5
            self.map_canvas.create_oval(cx - node_size, cy - node_size, 
                                        cx + node_size, cy + node_size, 
                                        fill=node_color, outline='', tags=("node_generic", *tags))

        # Draw Label (only for special nodes to keep map clean)
        if is_special:
            self.map_canvas.create_text(cx, cy + 18, text=name, fill=COLOR_TEXT, 
                                        font=("Consolas", 8), tags=("name", *tags))

    def _draw_map(self):
        """Draws all nodes and edges with their current incident status."""
        self.map_canvas.delete("all")
        
        c_width = self.map_canvas.winfo_width()
        c_height = self.map_canvas.winfo_height()
        grid_color = "#152030"
        
        # 1. Draw Grid Background (Technical Grid Overlay)
        for i in range(1, 11):
            x = c_width * i / 11
            self.map_canvas.create_line(x, 0, x, c_height, fill=grid_color, dash=(2, 2))
            y = c_height * i / 11
            self.map_canvas.create_line(0, y, c_width, y, fill=grid_color, dash=(2, 2))

        # 2. Draw Edges (Roads)
        for edge_data in DEHRADUN_GRAPH_EDGES:
            u, v = edge_data['u'], edge_data['v']
            incident_status = edge_data['incident']
            
            x1, y1 = self.nodes.get(u, (0, 0))
            cx1, cy1 = self._get_canvas_coords(x1, y1)
            x2, y2 = self.nodes.get(v, (0, 0))
            cx2, cy2 = self._get_canvas_coords(x2, y2)
            
            # Determine color and width
            line_color = COLOR_TEXT if not incident_status else COLOR_WARNING # Neon Magenta for incident
            line_width = 1 if not incident_status else 4
            line_dash = () if not incident_status else (6, 3)
            
            line = self.map_canvas.create_line(cx1, cy1, cx2, cy2, 
                                               fill=line_color, width=line_width, 
                                               arrow='last', arrowshape=(8, 10, 3), 
                                               dash=line_dash, tags=("road", "edge", f"edge_{u}_{v}"))
            
            edge_data['line_id'] = line
            
        # 3. Draw Nodes (Locations)
        for name, (x, y) in self.nodes.items():
            cx, cy = self._get_canvas_coords(x, y)
            self._draw_node(name, cx, cy)
        
        # Ensure special nodes and names are drawn over roads
        self.map_canvas.tag_raise("node_generic")
        self.map_canvas.tag_raise("node_special")
        self.map_canvas.tag_raise("node_fill")
        self.map_canvas.tag_raise("node_icon_special")
        self.map_canvas.tag_raise("name")
        self.map_canvas.tag_raise("node_highlight")

    def _draw_path(self, segments):
        """Highlights the computed shortest path on the map."""
        
        # Reset previous path highlights 
        # (Must redraw map to properly reset incident lines, then highlight path)
        self.map_canvas.delete("path_highlight")
        
        # 1. Highlight Path Edges
        for segment in segments:
            u = segment['from']
            v = segment['to']
            
            for edge_data in DEHRADUN_GRAPH_EDGES:
                if edge_data['u'] == u and edge_data['v'] == v:
                    line_id = edge_data['line_id']
                    if line_id:
                        color = COLOR_SUCCESS # Neon Green for path
                        width = 4
                        # Draw a thicker line underneath the current edge to highlight it
                        # NOTE: Using create_line again ensures it draws over the incident color
                        x1, y1 = self.nodes.get(u)
                        cx1, cy1 = self._get_canvas_coords(x1, y1)
                        x2, y2 = self.nodes.get(v)
                        cx2, cy2 = self._get_canvas_coords(x2, y2)
                        
                        self.map_canvas.create_line(cx1, cy1, cx2, cy2, 
                                                    fill=color, width=width, 
                                                    arrow='last', arrowshape=(8, 10, 3), 
                                                    tags=("road", "path_highlight"))
                        
                        # Re-raise the incident lines so they are visible under the path line if needed
                        if edge_data['incident']:
                             self.map_canvas.tag_lower(line_id) 

                    break
        
        self.map_canvas.tag_raise("node") # Ensure nodes are always on top

    # --- Button Command Handlers ---

    def _start_calculation(self):
        """Starts calculation with a delay to simulate latency/processing."""
        self.calc_button.config(state=tk.DISABLED, text="PROCESSING A* ALGORITHM...")
        self.update_status("Processing route optimization...", COLOR_SECONDARY)
        self.after(250, self.calculate_route)

    def calculate_route(self):
        """Calls the C++ engine via ctypes (or simulation) for route calculation."""
        start_node = self.selected_start.get()
        end_node = self.selected_end.get()

        if not start_node or not end_node:
            self.update_status("ERROR: Select valid start and destination nodes.", COLOR_WARNING)
            self.calc_button.config(state=tk.NORMAL, text="EXECUTE PATHFINDING COMMAND")
            return

        try:
            result = self.cpp_engine.find_route(start_node, end_node)
            total_time = result.get('total_cost', float('inf'))
            self.current_route_segments = result.get('segments', [])
            
            if total_time == float('inf') or not self.current_route_segments:
                self.update_status("ROUTE UNREACHABLE or BLOCKED. Check network status.", COLOR_WARNING)
                self.update_log(f"Route failed: {start_node} to {end_node}. UNREACHABLE.", COLOR_WARNING)
            else:
                self.update_status(f"ROUTE SUCCESS | ETA: {total_time:.0f} min.", COLOR_SUCCESS)
                self.update_log(f"Optimal route calculated. Time: {total_time:.0f} min.", COLOR_SUCCESS)
            
            self._update_result_display(total_time, self.current_route_segments)
            self._draw_map()
            if total_time != float('inf'):
                self._draw_path(self.current_route_segments)
                
        except Exception as e:
             self.update_status(f"RUNTIME ERROR: {e}", COLOR_WARNING)
        
        self.calc_button.config(state=tk.NORMAL, text="EXECUTE PATHFINDING COMMAND")

    def _update_result_display(self, total_time, segments):
        """Updates the results labels, segment table, and criticality score."""
        
        self.segments_tree.delete(*self.segments_tree.get_children())
        total_dist_km = 0
        
        # 1. Update Segment Details and Total Distance
        for segment in segments:
            u, v, time_min_raw = segment['from'], segment['to'], segment['cost']
            
            edge_data_found = next((e for e in DEHRADUN_GRAPH_EDGES if e['u'] == u and e['v'] == v), None)
            dist_km = edge_data_found['dist_km'] if edge_data_found else 0.0
            
            speed_kph = (dist_km / (time_min_raw / 60)) if time_min_raw > 0 and dist_km > 0 else 0
            
            total_dist_km += dist_km
            
            self.segments_tree.insert('', 'end', 
                                     values=(u, v, f"{dist_km:.2f}", f"{time_min_raw:.0f}", f"{speed_kph:.1f}"))

        # 2. Calculate Criticality Score
        nominal_time = self.nominal_time
        time_delta = total_time - nominal_time if nominal_time != float('inf') and total_time != float('inf') else 0

        if total_time == float('inf'):
             criticality_text = "STATUS: UNREACHABLE"
             criticality_color = COLOR_WARNING
        elif time_delta > 5:
             criticality_text = f"CRITICAL: +{time_delta:.0f} min (DELAY)"
             criticality_color = COLOR_WARNING
        elif time_delta > 0:
             criticality_text = f"WARNING: +{time_delta:.0f} min (DELAY)"
             criticality_color = COLOR_CRITICALITY
        else:
             criticality_text = "STATUS: NOMINAL"
             criticality_color = COLOR_SUCCESS if self.incident_active else COLOR_TEXT # Green if reroute was successful, else white

        self.result_label_criticality.config(text=criticality_text, foreground=criticality_color)

        # 3. Update Summary Labels
        if total_time == float('inf'):
            time_str = "ETA: UNREACHABLE"
            dist_str = "DIST: N/A"
            time_color = COLOR_WARNING
        else:
            time_str = f"ETA: {total_time:.0f} min"
            dist_str = f"DIST: {total_dist_km:.2f} km"
            time_color = COLOR_SUCCESS if not self.incident_active else COLOR_WARNING 

        self.result_label_time.config(text=time_str, foreground=time_color)
        self.result_label_dist.config(text=dist_str)

    def simulate_incident(self, node=None, quiet=False):
        """Simulates a road closure/major traffic incident affecting multiple roads."""
        incident_node = node if node else self.incident_node_var.get()
        incident_count = 0
        
        base_edges = [e for e in DEHRADUN_GRAPH_EDGES if (e['u'] == incident_node or e['v'] == incident_node) and not e['incident']]
        
        if not base_edges:
             if not quiet:
                 self.update_status(f"ERROR: No available roads from {incident_node} to block.", COLOR_WARNING)
             return
             
        edges_to_block = random.sample(base_edges, min(len(base_edges), 3))
        
        current_nominal_speed = self._get_current_nominal_speed()

        for edge_data in edges_to_block:
            u, v, dist_km = edge_data['u'], edge_data['v'], edge_data['dist_km']
            
            # New cost based on reducing speed to 5kph
            new_time = calculate_time_minutes(dist_km, INCIDENT_SPEED_KMPH)
            
            # Ensure both directions are updated
            for edge in DEHRADUN_GRAPH_EDGES:
                if (edge['u'] == u and edge['v'] == v) or (edge['u'] == v and edge['v'] == u):
                    edge['current_t'] = new_time
                    edge['incident'] = True
                    self.cpp_engine.update_edge_weight(edge['u'], edge['v'], int(new_time))
            
            incident_count += 1
            
        self.incident_active = True
        
        if not quiet:
            self.update_status(f"INCIDENT DETECTED: {incident_count} sectors locked near {incident_node}. Rerouting...", COLOR_WARNING)
            self.update_log(f"CRITICAL: Traffic incident triggered at {incident_node}.", COLOR_WARNING)
            
            self._draw_map()
            self.calculate_route()

    def clear_incidents(self, quiet=False):
        """Resets all edge weights to the current traffic profile."""
        incident_count = 0
        current_nominal_speed = self._get_current_nominal_speed()
        
        for edge_data in DEHRADUN_GRAPH_EDGES:
            if edge_data['incident']:
                u, v, dist_km = edge_data['u'], edge_data['v'], edge_data['dist_km']
                
                reset_time = calculate_time_minutes(dist_km, current_nominal_speed)

                self.cpp_engine.update_edge_weight(u, v, int(reset_time))
                self.cpp_engine.update_edge_weight(v, u, int(reset_time))
                
                edge_data['current_t'] = reset_time
                edge_data['incident'] = False
                incident_count += 1
            
        self.incident_active = False
        
        if not quiet:
            if incident_count > 0:
                self.update_status(f"INCIDENTS RESOLVED: {incident_count} sectors cleared. Network restored.", COLOR_SUCCESS)
                self.update_log("All network incidents cleared. Weights reset to nominal.", COLOR_SUCCESS)
            else:
                self.update_status("NETWORK NOMINAL: No active incidents to resolve.", COLOR_SECONDARY)
            
            self._draw_map()
            self.calculate_route()
        
    def _resize_map(self, event):
        """Redraws the map when the canvas size changes."""
        self._draw_map()
        if self.current_route_segments:
            self._draw_path(self.current_route_segments)
            
    def destroy(self):
        """Override destroy to clear the tooltip on exit."""
        self._clear_tooltip()
        super().destroy()

if __name__ == "__main__":
    app = EmergencyRouteFinder()
    app.mainloop()

