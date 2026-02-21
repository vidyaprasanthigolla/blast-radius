import networkx as nx  # type: ignore

class GraphBuilder:
    def __init__(self, parsed_data):
        self.parsed_data = parsed_data
        self.graph = nx.DiGraph()

    def build(self):
        # Add Module Nodes
        for mod, data in self.parsed_data.get("modules", {}).items():
            self.graph.add_node(mod, type="module", label=mod)

        # Add Class Nodes
        for cls, data in self.parsed_data.get("classes", {}).items():
            self.graph.add_node(cls, type="class", label=data["name"])
            # Edge from module to class
            self.graph.add_edge(data["module"], cls, type="contains")

        # Add Function Nodes
        for func, data in self.parsed_data.get("functions", {}).items():
            self.graph.add_node(func, type="function", label=data["name"])
            # Edge from module or class to function
            parent = data["class"] if data["class"] else data["module"]
            self.graph.add_edge(parent, func, type="contains")

        # Add Import Edges
        for imp in self.parsed_data.get("imports", []):
            source = imp["source_module"]
            target = imp["target_module"]
            if target:
                self.graph.add_node(target, type="module", label=target) # might be external, add it anyway
                self.graph.add_edge(source, target, type="imports")

        # Add Call Edges (Best Effort linking)
        # Call graph in dynamic languages is tricky. We'll simply find nodes whose label ends with the callee name.
        all_nodes = list(self.graph.nodes(data=True))
        
        for call in self.parsed_data.get("calls", []):
            caller = call["caller"]
            callee_guess = call["callee"]
            
            # Simple heuristic: if we find a function or class ending with the callee name, we link it.
            # E.g. helper.do_something -> we look for do_something
            target_node = None
            callee_parts = callee_guess.split('.')
            func_name = callee_parts[-1]
            
            for n, data in all_nodes:
                if n.endswith(f".{func_name}") or n == func_name:
                    target_node = n
                    break
                    
            if target_node:
                self.graph.add_edge(caller, target_node, type="calls")
            else:
                # Add an external node if not found
                ext_node = f"ext:{callee_guess}"
                self.graph.add_node(ext_node, type="external", label=callee_guess)
                self.graph.add_edge(caller, ext_node, type="calls")

        return self.graph
