
import plotly.graph_objects as go
from collections import Counter

def create_top_words_graph(subreddit, top_titles, custom_stop_words):
    titles = [submission.title for submission in top_titles]
    words = ' '.join(titles).lower().split()

    # Filter out stopwords and non-alphabetic words
    filtered_words = [
        word for word in words
        if word not in custom_stop_words and word.isalpha()
    ]
    
    # Count remaining words
    word_counts = Counter(filtered_words)
    
    # Get the top 10 most common words (or however many are available)
    top_words = word_counts.most_common(10)
    
    # Handle the case where there are no top words
    if not top_words:
        print(f"No significant words found for subreddit: {subreddit}")
        return go.Figure()  # Return an empty figure
    
    # Unpack the available top words and their counts
    words, counts = zip(*top_words) if top_words else ([], [])

    # Reverse the order to have the greatest to least
    words = list(words)[::-1]
    counts = list(counts)[::-1]

    # Create the bar graph with words in descending order
    fig = go.Figure(
        data=[go.Bar(
            x=counts,
            y=words,
            orientation='h',
            marker=dict(color='rgba(50, 171, 96, 0.6)', line=dict(color='rgba(50, 171, 96, 1.0)', width=1)),
        )],
        layout=go.Layout(
            title=f'Top {len(words)} Words for {subreddit}',
            xaxis=dict(title='Frequency'),
            yaxis=dict(title='Words'),
            margin=dict(l=120, r=20, t=70, b=70),
        )
    )
    
    return fig
