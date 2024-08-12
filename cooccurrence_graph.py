
import networkx as nx
import plotly.graph_objects as go
from collections import defaultdict, Counter

def create_cooccurrence_graph(subreddit, top_titles, custom_stop_words):
    # Extracting words and tracking co-occurrences
    cooccurrence_dict = defaultdict(Counter)
    titles = [submission.title for submission in top_titles]
    
    for title in titles:
        words = [word for word in title.lower().split() if word not in custom_stop_words and word.isalpha()]
        for i in range(len(words)):
            for j in range(i + 1, len(words)):
                cooccurrence_dict[words[i]][words[j]] += 1
                cooccurrence_dict[words[j]][words[i]] += 1

    # Building the graph
    G = nx.Graph()
    
    for word, connections in cooccurrence_dict.items():
        for connected_word, count in connections.items():
            if count > 1:  # Only consider connections that occur more than once
                G.add_edge(word, connected_word, weight=count)
    
    # Filter nodes to include only those with 2 or more connections
    filtered_nodes = [node for node in G.nodes() if len(list(G.neighbors(node))) >= 2]
    G = G.subgraph(filtered_nodes).copy()

    # If no nodes are left after filtering, return an empty figure
    if len(G.nodes()) == 0:
        print("No significant nodes with 2 or more connections found.")
        return go.Figure()
    
    # Using community detection (optional)
    communities = nx.algorithms.community.greedy_modularity_communities(G)
    
    pos = nx.spring_layout(G, k=0.5)
    
    edge_trace = []
    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_trace.append(go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            line=dict(width=edge[2]['weight'], color='#888'),
            hoverinfo='text',
            text=f'{edge[0]} + {edge[1]}: {edge[2]["weight"]} co-occurrences',
            mode='lines'))

    node_trace = go.Scatter(
        x=[pos[k][0] for k in G.nodes()],
        y=[pos[k][1] for k in G.nodes()],
        text=[f'{node}' for node in G.nodes()],  # Only the word itself
        mode='markers+text',
        hoverinfo='text',
        hovertext=[f'{node} ({len(list(G.neighbors(node)))} connections)' for node in G.nodes()],  # Tooltip with connections
        marker=dict(
            showscale=True,
            colorscale='YlGnBu',
            size=[len(list(G.neighbors(node))) * 5 for node in G.nodes()],
            color=[len(list(G.neighbors(node))) for node in G.nodes()],
            colorbar=dict(
                thickness=15,
                title='Node Connections',
                xanchor='left',
                titleside='right'
            ),
            line_width=2))
    
    fig = go.Figure(data=edge_trace + [node_trace],
                    layout=go.Layout(
                        title=f'Co-Occurrence Network for {subreddit}',
                        titlefont_size=16,
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        annotations=[dict(
                            text=f'{subreddit} Co-Occurrence Network',
                            showarrow=False,
                            xref="paper", yref="paper",
                            x=0.005, y=-0.002 )],
                        xaxis=dict(showgrid=False, zeroline=False),
                        yaxis=dict(showgrid=False, zeroline=False))
                   )
    
    return fig
