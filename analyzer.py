import networkx as nx  # type: ignore


class BlastAnalyzer:
    def __init__(self, graph):
        self.graph = graph

    def analyze(self, change_intent):
        # Basic heuristic: try to find a node that matches something in change_intent
        # If the user says "Modify db_connector", we find nodes containing "db_connector"
        
        start_nodes = self._find_start_nodes(change_intent)
        if not start_nodes:
            # If nothing found, just pick the first module to show something for demo
            modules = [n for n, d in self.graph.nodes(data=True) if d.get("type") == "module"]
            if modules:
                start_nodes = [modules[0]]
            else:
                return {"error": "Could not identify starting node from intent."}
        
        start_nodes_set = set(start_nodes)
        
        # Traverse downstream (who depends on this?)
        # Since our graph edges are: 
        # A -> B (A contains B), A -> B (A calls B), A -> B (A imports B)
        # We need the REVERSE graph to see who uses B!
        # If A imports B, B changes -> A is impacted.
        # So we look for edges arriving at B in reverse.
        reverse_graph = self.graph.reverse()
        
        impacted_nodes = set()
        for node in start_nodes:
            # Get all reachable nodes in reverse graph (dependents)
            if node in reverse_graph:
                reachable = nx.descendants(reverse_graph, node)
                impacted_nodes.add(node)
                impacted_nodes.update(reachable)
            else:
                impacted_nodes.add(node)
            
        results = []
        for n in impacted_nodes:
            if n not in self.graph:
                continue
            node_data = self.graph.nodes[n]
            # Simple classification logic mock
            is_direct = bool(n in start_nodes_set)
            category = self._classify_impact(n, node_data)
            explanation = self._generate_explanation(n, category, change_intent, is_direct)
            
            results.append({
                "id": n,
                "label": node_data.get("label", n),
                "type": node_data.get("type", "unknown"),
                "is_direct": is_direct,
                "category": category,
                "explanation": explanation
            })
            
        return {
            "intent": change_intent,
            "start_nodes": list(start_nodes),
            "impacts": results,
            "graph_data": self._get_cytoscape_data(impacted_nodes)
        }

    def _find_start_nodes(self, intent):
        intent_lower = intent.lower()
        matched = []
        for n, data in self.graph.nodes(data=True):
            label = data.get("label", "").lower()
            if label and label in intent_lower and len(label) > 3: # Avoid matching short generic words
                matched.append(n)
        return matched

    def _classify_impact(self, node_id, node_data):
        ntype = node_data.get("type", "")
        if "api" in node_id.lower() or "app" in node_id.lower():
            return "API Contract"
        if "db" in node_id.lower() or "data" in node_id.lower() or "connector" in node_id.lower():
            return "Data Handling"
        if ntype == "function" or "service" in node_id.lower():
            return "Business Logic"
        return "General"

    def _generate_explanation(self, node_id, category, intent, is_direct):
        if is_direct:
            return f"Directly modified component as per change intent."
        else:
            if category == "API Contract":
                return f"Downstream layer '{node_id}' relies on modified component. May break external API consumers."
            elif category == "Data Handling":
                return f"Data model or query execution in '{node_id}' might be affected by upstream schema or logic changes."
            elif category == "Business Logic":
                return f"Execution flow or state in '{node_id}' depends on modified logic. Requires regression testing."
            else:
                return f"Trigged indirect dependency recalculation for '{node_id}'."

    def _get_cytoscape_data(self, highlight_nodes):
        cyto_elements = []
        # Add nodes
        for n, data in self.graph.nodes(data=True):
            cyto_elements.append({
                "data": {
                    "id": n,
                    "label": data.get("label", n),
                    "type": data.get("type", "unknown"),
                    "highlighted": n in highlight_nodes
                }
            })
            
        # Add edges
        for u, v, data in self.graph.edges(data=True):
            # For cytoscape, we should direct arrows from dependency to dependent. 
            # Or from caller to callee. Cytoscape defaults to pointing source -> target.
            # Our graph has A imports B. So A -> B. Downstream is actually A (A depends on B).
            # We'll just visualize it as caller -> callee.
            cyto_elements.append({
                "data": {
                    "id": f"{u}-{v}-{data.get('type', '')}",
                    "source": u,
                    "target": v,
                    "label": data.get("type", "")
                }
            })
            
        return cyto_elements
