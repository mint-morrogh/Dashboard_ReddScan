import plotly.express as px
from datetime import datetime
import plotly.graph_objects as go 

def create_user_karma_time_scatter(subreddit, users_karma, posts_data):
    top_users = users_karma[subreddit].most_common(10)
    
    if not top_users:
        print(f"No significant users found for subreddit: {subreddit}")
        return go.Figure()  # Return an empty figure
    
    users = []
    karma = []
    times = []
    titles = []
    post_types = []
    urls = []  # To store URLs of posts

    for user, _ in top_users:
        user_posts = [
            post for post in posts_data[subreddit]
            if post.author is not None and post.author.name == user
        ]
        for post in user_posts:
            users.append(user)
            karma.append(max(post.score, 2))  # Ensure minimum size is 2 (since 1 is default karma)
            times.append(datetime.utcfromtimestamp(post.created_utc))  # Convert timestamp to datetime
            
            # Truncate the title if it exceeds 60 characters
            truncated_title = (post.title[:60] + '...') if len(post.title) > 60 else post.title
            titles.append(truncated_title)
            
            post_types.append("NSFW" if post.over_18 else "SFW")
            urls.append(post.url)  # Cache the URL

    # Reverse the order of the users list to have the highest karma at the top
    users = list(users)[::-1]
    karma = list(karma)[::-1]
    times = list(times)[::-1]
    titles = list(titles)[::-1]
    post_types = list(post_types)[::-1]
    urls = list(urls)[::-1]  # Reverse URLs to match the order

    fig = px.scatter(
        x=times,
        y=users,
        size=karma,  # Size of bubbles represents karma
        size_max=50,  # Maximum bubble size
        color=karma,  # Color bubbles based on karma
        labels={'x': 'Time of Submission', 'y': 'Users', 'color': 'Karma'},  # Change legend title to "Karma"
        title=f'Top 10 User Posts in {subreddit}',
        height=500,
        hover_name=titles,  # Use truncated post titles for hover
        hover_data={
            'User': users,
            'Submission Time': times,
            'Karma': karma,
            'Post Type': post_types,
            'URL': urls  # Include URLs in hover data, but not in the tooltip
        }
    )

    fig.update_traces(
        marker=dict(sizemode='area', sizemin=3),  # Ensure minimum bubble size is 8 pixels
        hovertemplate="<b>%{hovertext}</b><br><br>" +  # Bold title
                      "User : %{customdata[0]}<br>" +
                      "Submission Time : %{customdata[1]}<br>" +
                      "Karma : %{customdata[2]}<br>" +
                      "Post Type : %{customdata[3]}<extra></extra>"  # Removed URL from hover template
    )

    return fig
