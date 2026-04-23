# 🚑 Emergency Route Finder (A* Pathfinding System)

A futuristic **Emergency Dispatch & Route Optimization System** built using **Python (Tkinter GUI)** and a high-performance **C++ A* pathfinding engine**.

This project simulates a real-world **smart traffic control system** that dynamically calculates the fastest routes for emergency services (ambulance, police, etc.) and adapts to traffic conditions and incidents in real time.

---

## ✨ Features

* ⚡ **A* Pathfinding Algorithm (C++ Backend)**
* 🖥️ **Modern Futuristic GUI (Tkinter)**
* 🗺️ **Interactive Map Visualization**
* 🚦 **Dynamic Traffic Simulation**
* 🚧 **Incident Simulation (Road Block / Congestion)**
* 🔄 **Real-time Route Recalculation**
* 📊 **Detailed Route Segments & Metrics**
* 📡 **Activity Log & System Monitoring**
* 🎯 **Heuristic-based Optimization (Euclidean Distance)**

---

## 🧠 Tech Stack

| Component      | Technology Used       |
| -------------- | --------------------- |
| Frontend UI    | Python (Tkinter)      |
| Backend Engine | C++ (A* Algorithm)    |
| Integration    | ctypes (Python ↔ C++) |
| Data Handling  | JSON                  |
| Visualization  | Canvas (Tkinter)      |

---

## 📂 Project Structure

```
Emergency-Route-Finder/
│
├── main.py                 # Python GUI Application
├── route_finder.cpp       # C++ A* Algorithm Engine
├── route_finder.dll / .so # Compiled shared library
├── README.md              # Project Documentation
```

---

## 🚀 How It Works

1. The **Python GUI** allows users to:

   * Select start & destination nodes
   * Choose traffic conditions
   * Simulate incidents

2. The request is sent to the **C++ A* Engine** via `ctypes`.

3. The engine:

   * Computes the shortest path using **A***
   * Returns structured JSON output

4. The GUI:

   * Displays the route on the map
   * Shows ETA, distance, and route segments
   * Updates dynamically on incidents

---

## 🧪 Simulation Features

### 🚦 Traffic Profiles

* Normal Traffic (40 km/h)
* Rush Hour (25 km/h)
* Night / Off-Peak (55 km/h)

### 🚧 Incident Simulation

* Blocks multiple roads dynamically
* Forces rerouting
* Displays critical delays

---

## 📊 Output Metrics

* ⏱️ ETA (Estimated Time of Arrival)
* 📏 Total Distance
* 📉 Delay / Criticality Status
* 🧩 Route Segments Breakdown

---

## 🎨 UI Highlights

* Neon futuristic theme 🌌
* Real-time animated node highlighting
* Interactive tooltips for nodes & edges
* Live activity log system

---

## 🔥 Example Use Case

> An ambulance needs the fastest route from **Hospital A → Hospital B**
> A traffic accident occurs → system instantly recalculates optimal route.

---

## ⚠️ Notes

* If the C++ library is not found, the system runs in **simulation mode**.
* Ensure `.dll` or `.so` file is in the same directory as `main.py`.

---

## 📌 Future Improvements

* 🌍 Real-world map integration (Google Maps API)
* 🤖 AI-based traffic prediction
* 📱 Mobile app version
* ☁️ Cloud-based deployment
* 📡 Live GPS tracking

---

## 👨‍💻 Author

**Vipin Singh**

---

## 📜 License

This project is open-source and available under the **MIT License**.

---

## ⭐ Support

If you like this project, give it a ⭐ on GitHub!

---
