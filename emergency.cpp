#include <iostream>
#include <vector>
#include <queue>
#include <map>
#include <string>
#include <limits>
#include <sstream>
#include <cmath> 
#include <algorithm> // Required for reverse

using namespace std;

// Define a large number for infinity
const int INF = numeric_limits<int>::max();

/**
 * @brief Represents a coordinate (X, Y) for heuristic calculation.
 */
struct Coordinate {
    int x; 
    int y; 
};

/**
 * @brief Represents an edge in the graph.
 */
struct Edge {
    string destination;
    int weight; // Cost (time/distance)
};

/**
 * @brief Represents a single segment of the final computed path.
 */
struct PathSegment {
    string from;
    string to;
    int cost; // Cost of this specific segment
};

/**
 * @brief Represents the complete result of a pathfinding query.
 */
struct PathResult {
    int total_cost = INF;
    string path_string = ""; // Simple string representation
    vector<PathSegment> segments; // Structured detail for UI
};

/**
 * @brief Comparator for Dijkstra's priority queue.
 */
struct CompareWeight {
    bool operator()(const pair<int, string>& a, const pair<int, string>& b) {
        return a.first > b.first;
    }
};

/**
 * @brief Comparator for A* priority queue.
 */
struct CompareFScore {
    bool operator()(const pair<double, string>& a, const pair<double, string>& b) {
        return a.first > b.first;
    }
};

/**
 * @brief Core Graph structure and pathfinding logic.
 */
class Graph {
private:
    map<string, vector<Edge>> adj;
    map<string, Coordinate> node_coordinates_;
    map<string, bool> nodes;

    /**
     * @brief Calculates the straight-line (Euclidean) distance heuristic h(n).
     */
    double calculateHeuristic(const string& current, const string& destination) const {
        if (node_coordinates_.count(current) && node_coordinates_.count(destination)) {
            const auto& start_coord = node_coordinates_.at(current);
            const auto& end_coord = node_coordinates_.at(destination);
            
            double dx = start_coord.x - end_coord.x;
            double dy = start_coord.y - end_coord.y;
            
            return sqrt(dx * dx + dy * dy);
        }
        return 0.0;
    }

public:
    void addNode(const string& name, int x, int y) {
        node_coordinates_[name] = {x, y};
        nodes[name] = true;
    }

    /**
     * @brief Adds a directed edge.
     */
    void addDirectedEdge(const string& from, const string& to, int initial_weight) {
        if (!nodes.count(from)) nodes[from] = true;
        if (!nodes.count(to)) nodes[to] = true;
        adj[from].push_back({to, initial_weight});
    }

    /**
     * @brief Adds a bidirectional edge, crucial for realistic road networks.
     */
    void setBidirectionalEdge(const string& node1, const string& node2, int weight) {
        addDirectedEdge(node1, node2, weight);
        addDirectedEdge(node2, node1, weight);
    }

    /**
     * @brief Dynamic Routing: Updates the weight of an existing edge.
     */
    bool updateEdgeWeight(const string& from, const string& to, int new_weight) {
        if (adj.count(from)) {
            for (auto& edge : adj[from]) {
                if (edge.destination == to) {
                    edge.weight = new_weight;
                    return true;
                }
            }
        }
        return false;
    }

    /**
     * @brief A* Search algorithm to find the shortest path (informed search).
     * @return PathResult containing total cost and detailed segments.
     */
    PathResult findShortestPathAStar(const string& start, const string& destination) {
        if (!nodes.count(start) || !nodes.count(destination)) {
            PathResult result;
            result.path_string = "Error: Start or destination not found.";
            return result;
        }

        map<string, int> g_score;
        map<string, double> f_score;
        map<string, string> predecessor;

        for (const auto& pair : nodes) {
            g_score[pair.first] = INF;
            f_score[pair.first] = numeric_limits<double>::max();
        }

        g_score[start] = 0;
        f_score[start] = (double)g_score[start] + calculateHeuristic(start, destination);

        priority_queue<pair<double, string>, vector<pair<double, string>>, CompareFScore> pq;
        pq.push({f_score[start], start});

        // Path reconstruction logic: needs the distance to the predecessor
        map<string, int> cost_to_predecessor;

        while (!pq.empty()) {
            double current_f = pq.top().first; 
            string u = pq.top().second;
            pq.pop();

            if (u == destination) break;
            if (current_f > f_score[u]) continue; 

            if (adj.count(u)) {
                for (const auto& edge : adj[u]) {
                    string v = edge.destination;
                    int weight = edge.weight;
                    
                    int tentative_g_score = g_score[u] + weight;

                    if (tentative_g_score < g_score[v]) {
                        predecessor[v] = u;
                        cost_to_predecessor[v] = weight; // Store the cost of this segment
                        g_score[v] = tentative_g_score;
                        f_score[v] = (double)g_score[v] + calculateHeuristic(v, destination);
                        
                        pq.push({f_score[v], v});
                    }
                }
            }
        }
        
        return reconstructPath(start, destination, g_score, predecessor, cost_to_predecessor);
    }

private:
    /**
     * @brief Helper function to reconstruct the path and populate the PathResult struct.
     */
    PathResult reconstructPath(const string& start, const string& destination, 
                               const map<string, int>& distance, 
                               const map<string, string>& predecessor,
                               const map<string, int>& cost_to_predecessor) const {
        PathResult result;

        if (distance.find(destination) == distance.end() || distance.at(destination) == INF) {
            result.path_string = "No path found.";
            return result;
        }
        
        result.total_cost = distance.at(destination);

        vector<string> nodes_in_path;
        string current = destination;
        while (current != start) {
            if (predecessor.find(current) == predecessor.end()) {
                result.path_string = "Error reconstructing path.";
                result.total_cost = INF;
                return result;
            }
            string prev = predecessor.at(current);
            int cost = cost_to_predecessor.at(current);
            
            result.segments.push_back({prev, current, cost});
            nodes_in_path.push_back(current);
            current = prev;
        }
        
        nodes_in_path.push_back(start);
        reverse(nodes_in_path.begin(), nodes_in_path.end());
        reverse(result.segments.begin(), result.segments.end()); // Segments should be start-to-end

        stringstream path_stream;
        for (size_t i = 0; i < nodes_in_path.size(); ++i) {
            path_stream << nodes_in_path[i];
            if (i < nodes_in_path.size() - 1) {
                path_stream << " -> ";
            }
        }
        result.path_string = path_stream.str();
        
        return result;
    }
};

/**
 * @brief Main function to demonstrate A* search with structured output and dynamic routing.
 * * Note: This C++ engine would be compiled as a backend library in a real system.
 */
int main() {
    Graph dehradun_map;
    
    // --- Node and Coordinate Setup ---
    dehradun_map.addNode("H-DoonHospital", 10, 80); 
    dehradun_map.addNode("L-ClockTower", 20, 70); 
    dehradun_map.addNode("P-Kotwali", 30, 60);
    dehradun_map.addNode("H-MaxHospital", 90, 10);
    dehradun_map.addNode("R-RajpurRoad", 40, 50);
    dehradun_map.addNode("S-WelhamGirls", 50, 40);

    // Adding coordinates for the extensive graph structure (Nodes 1 to 120)
    for(int i = 1; i <= 120; ++i) {
        string current = "Node-" + to_string(i);
        int x = (i % 20) * 5 + 5; 
        int y = 100 - (i / 10) * 8; 
        dehradun_map.addNode(current, x, y);
    }
    
    // --- Edge Setup (Using Bidirectional Edges) ---
    dehradun_map.setBidirectionalEdge("H-DoonHospital", "L-ClockTower", 10);
    dehradun_map.setBidirectionalEdge("L-ClockTower", "P-Kotwali", 3);
    dehradun_map.setBidirectionalEdge("P-Kotwali", "H-MaxHospital", 15);
    dehradun_map.setBidirectionalEdge("H-MaxHospital", "R-RajpurRoad", 8);
    dehradun_map.setBidirectionalEdge("R-RajpurRoad", "L-ClockTower", 12);
    
    // Connecting the 120 nodes bidirectionally
    for(int i = 1; i <= 120; ++i) {
        string current = "Node-" + to_string(i);
        string next = "Node-" + to_string(i + 1);
        string far = "Node-" + to_string(i + 5);

        if (i < 120) dehradun_map.setBidirectionalEdge(current, next, 5 + (i % 3));
        
        // Shortcuts
        if (i % 10 == 0 && i < 115) dehradun_map.setBidirectionalEdge(current, far, 10);
        
        // Connections to major hubs
        if (i % 20 == 0) dehradun_map.setBidirectionalEdge(current, "H-DoonHospital", 25);
    }
    
    dehradun_map.setBidirectionalEdge("L-ClockTower", "Node-1", 1);
    dehradun_map.setBidirectionalEdge("Node-120", "H-MaxHospital", 1);
    
    // --- Path Calculation Demonstration ---
    string start_node = "H-DoonHospital";
    string end_node = "H-MaxHospital";
    
    cout << "=================================================" << endl;
    cout << "  EMERGENCY ROUTE FINDER: STRUCTURED A* OUTPUT   " << endl;
    cout << "=================================================" << endl;

    auto result = dehradun_map.findShortestPathAStar(start_node, end_node);
    
    cout << "\n--- Initial Path Calculation ---" << endl;
    if (result.total_cost != INF) {
        cout << "Total Time: " << result.total_cost << " minutes" << endl;
        cout << "Path String: " << result.path_string << endl;
        cout << "--- Detailed Segments ---" << endl;
        for(const auto& segment : result.segments) {
            cout << "  " << segment.from << " -> " << segment.to << " (Cost: " << segment.cost << ")" << endl;
        }
    } else {
        cout << result.path_string << endl;
    }

    // --- Dynamic Routing Demonstration ---
    cout << "\n=================================================" << endl;
    cout << "    DYNAMIC ROUTING: INCIDENT SIMULATION         " << endl;
    cout << "=================================================" << endl;
    
    // Simulate a major incident on Node-1 to Node-2
    cout << "Simulating accident: 'Node-1' to 'Node-2' travel time increased to 50 minutes." << endl;
    dehradun_map.updateEdgeWeight("Node-1", "Node-2", 50); 
    // Since roads are often bidirectional, we update the reverse path too, though sometimes incident only affects one direction.
    // For this demo, let's assume the reverse path (Node-2 to Node-1) is also affected.
    dehradun_map.updateEdgeWeight("Node-2", "Node-1", 50); 
    
    auto dynamic_result = dehradun_map.findShortestPathAStar(start_node, end_node);

    cout << "\n--- Recalculated Path (After Incident) ---" << endl;
    if (dynamic_result.total_cost != INF) {
        cout << "Total Time: " << dynamic_result.total_cost << " minutes" << endl;
        cout << "Path String: " << dynamic_result.path_string << endl;
    } else {
        cout << dynamic_result.path_string << endl;
    }

    return 0;
}


