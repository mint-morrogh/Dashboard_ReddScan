
import plotly.graph_objects as go

def create_user_karma_graph(subreddit, users_karma):
    top_users = users_karma[subreddit].most_common(10)
    
    if not top_users:
        print(f"No significant users found for subreddit: {subreddit}")
        return go.Figure()  # Return an empty figure
    
    # Unpack users and karma
    users, karma = zip(*top_users)
    
    # Reverse the order to have the greatest to least
    users = list(users)[::-1]
    karma = list(karma)[::-1]

    fig = go.Figure(
        data=[go.Bar(
            x=karma,  # Sorted in descending order
            y=users,  # Sorted in descending order
            orientation='h',
            marker=dict(color='rgba(255, 100, 100, 0.6)', line=dict(color='rgba(255, 100, 100, 1.0)', width=1)),
        )],
        layout=go.Layout(
            title=f'Top {len(users)} Users by Karma in {subreddit}',
            xaxis=dict(title='Karma'),
            yaxis=dict(title='Users'),
            margin=dict(l=120, r=20, t=70, b=70),
        )
    )
    
    return fig
