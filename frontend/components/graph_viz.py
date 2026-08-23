import streamlit as st
import streamlit.components.v1 as components
import json

def render_interactive_graph(evidence_list):
    if not evidence_list:
        st.info("No active graph nodes to display.")
        return

    nodes = []
    edges = []
    node_ids = set()

    color_map = {
        "audio": "#38BDF8",
        "video_frame": "#F43F5E",
        "image": "#F59E0B",
        "pdf_text": "#10B981",
        "pdf_ocr": "#059669",
        "ocr": "#8B5CF6",
        "text": "#6366F1"
    }

    for item in evidence_list:
        n_id = item.get("node_id")
        if n_id not in node_ids:
            node_ids.add(n_id)
            mod = item.get("modality", "unknown")
            color = color_map.get(mod, "#94A3B8")
            label = f"{mod.upper()}\n{item.get('source_file', '')}"
            if item.get("timestamp") is not None:
                label += f"\n{item.get('timestamp'):.1f}s"
            elif item.get("page") is not None:
                label += f"\nPage {item.get('page')}"

            nodes.append({
                "id": n_id,
                "label": label,
                "color": color,
                "shape": "box",
                "font": {"color": "#FFFFFF", "size": 14},
                "shadow": True
            })

    for i in range(len(evidence_list)):
        curr = evidence_list[i]
        rel = curr.get("relationship_path")
        if rel and i > 0:
            prev_id = evidence_list[i - 1].get("node_id")
            curr_id = curr.get("node_id")
            edges.append({
                "from": prev_id,
                "to": curr_id,
                "label": rel,
                "color": {"color": "#38BDF8"},
                "arrows": "to",
                "font": {"color": "#38BDF8", "size": 12, "align": "middle"}
            })

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
      <style>
        body {{ margin: 0; padding: 0; background-color: #0F172A; }}
        #network {{ width: 100%; height: 420px; border: 1px solid #334155; border-radius: 10px; }}
      </style>
    </head>
    <body>
      <div id="network"></div>
      <script type="text/javascript">
        var nodes = new vis.DataSet({json.dumps(nodes)});
        var edges = new vis.DataSet({json.dumps(edges)});
        var container = document.getElementById('network');
        var data = {{ nodes: nodes, edges: edges }};
        var options = {{
          nodes: {{
            borderWidth: 2,
            shadow: true
          }},
          edges: {{
            width: 2,
            smooth: {{ type: 'continuous' }}
          }},
          physics: {{
            stabilization: true,
            barnesHut: {{ gravitationalConstant: -3000, springLength: 120 }}
          }}
        }};
        var network = new vis.Network(container, data, options);
      </script>
    </body>
    </html>
    """

    components.html(html_code, height=440)
