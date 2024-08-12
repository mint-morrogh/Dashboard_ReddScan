
import networkx as nx
import plotly.graph_objects as go
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def create_keyword_graph(subreddit, top_titles):
    titles = [submission.title for submission in top_titles]
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(titles)
    similarity_matrix = cosine_similarity(tfidf_matrix)
    terms = vectorizer.get_feature_names_out()

    G = nx.Graph()

    num_terms = len(terms)
    print(f"Number of terms: {num_terms}")
    print(f"Shape of similarity matrix: {similarity_matrix.shape}")

    num_edges_added = 0
    for i in range(num_terms):
        for j in range(i + 1, num_terms):
            if i < similarity_matrix.shape[0] and j < similarity_matrix.shape[1]:

                if similarity_matrix[i, j] > 0.1:
                    G.add_edge(terms[i], terms[j], weight=similarity_matrix[i, j])
                    num_edges_added += 1

    print(f"Number of nodes: {len(G.nodes)}")
    print(f"Number of edges added: {num_edges_added}")

    if len(G.nodes) == 0 or num_edges_added == 0:
        print("No meaningful keyword connections found.")
        return go.Figure()

    MIN_DEGREE = 1
    filtered_nodes = [node for node, degree in dict(G.degree()).items() if degree >= MIN_DEGREE]
    G = G.subgraph(filtered_nodes).copy()

    if len(G.nodes) == 0:
        print("No significant keyword connections after filtering.")
        return go.Figure()

    pos = nx.spring_layout(G)
    edge_trace = []
    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_trace.append(go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            line=dict(width=edge[2]['weight']*5, color='#888'),
            hoverinfo='none',
            mode='lines'))

    node_trace = go.Scatter(
        x=[pos[k][0] for k in G.nodes()],
        y=[pos[k][1] for k in G.nodes()],
        text=[f'{node}' for node in G.nodes()],
        mode='markers+text',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            colorscale='YlGnBu',
            size=20,
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
                        title=f'Keyword Map for {subreddit}',
                        titlefont_size=16,
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        annotations=[dict(
                            text=f'{subreddit} Keyword Connections',
                            showarrow=False,
                            xref="paper", yref="paper",
                            x=0.005, y=-0.002 )],
                        xaxis=dict(showgrid=False, zeroline=False),
                        yaxis=dict(showgrid=False, zeroline=False))
                   )
    
    return fig
