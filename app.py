from flask import Flask, request, jsonify, render_template  # type: ignore
from typing import Dict, Any
import os
from parser import CodeParser  # type: ignore
from graph_builder import GraphBuilder  # type: ignore
from analyzer import BlastAnalyzer  # type: ignore

app = Flask(__name__)

@app.route('/')
def index() -> Any:
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze() -> Any:
    data: Dict[str, Any] = request.get_json(silent=True) or {}  # type: ignore
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON payload"}), 400
        
    codebase_path = data.get('codebase_path')
    change_intent = data.get('change_intent')

    if not codebase_path or not isinstance(codebase_path, str) or not os.path.exists(codebase_path):
        return jsonify({"error": "Invalid or missing codebase path"}), 400

    if not change_intent or not isinstance(change_intent, str):
        return jsonify({"error": "Missing change intent"}), 400

    try:
        # 1. Parse codebase
        code_parser = CodeParser(codebase_path)
        parsed_data = code_parser.parse()

        # 2. Build graph
        builder = GraphBuilder(parsed_data)
        graph = builder.build()

        # 3. Analyze impact
        analyzer = BlastAnalyzer(graph)
        result = analyzer.analyze(change_intent)

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
