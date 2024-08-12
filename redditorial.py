import praw
import pandas as pd
from collections import defaultdict, Counter
from datetime import datetime
import time
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dash import Dash, dcc, html, Input, Output
from dash import callback_context
from scatter_plot import create_user_karma_time_scatter
from keyword_graph import create_keyword_graph
from top_words_graph import create_top_words_graph
from user_karma_graph import create_user_karma_graph
from cooccurrence_graph import create_cooccurrence_graph
from config import client_id, client_secret, user_agent

SEARCH_X_SUBREDDITS = 100

# Initialize the Reddit client
reddit = praw.Reddit(client_id=client_id,
                     client_secret=client_secret,
                     user_agent=user_agent)

# Cache for storing keyword graphs, top words, and user graphs
keyword_graph_cache = {}
top_words_cache = {}
user_graph_cache = {}

# Load custom stopwords from file
def load_custom_stopwords(file_path):
    with open(file_path, 'r') as file:
        stopwords = set(line.strip().lower() for line in file) 
    return stopwords

custom_stop_words = load_custom_stopwords('custom_stopwords.txt')

# Reddit data fetching function
def get_reddit_data():
    subreddit_activity = Counter()
    subreddit_karma = Counter()
    subreddit_comments = Counter()
    subreddit_subscribers = defaultdict(lambda: 'N/A')
    subreddit_sfw_count = Counter()
    subreddit_nsfw_count = Counter()
    subreddit_sfw_comments = Counter()
    subreddit_nsfw_comments = Counter()
    subreddit_users_karma = defaultdict(Counter)
    subreddit_users_posts = defaultdict(list)
    
    top_submissions = list(reddit.subreddit('all').top(time_filter='day', limit=1000))
    top_subreddits = [submission.subreddit.display_name for submission in top_submissions]
    top_100_subreddits = Counter(top_subreddits).most_common(SEARCH_X_SUBREDDITS)
    
    for subreddit, _ in top_100_subreddits:
        print(f"Processing subreddit: {subreddit}")
        after = None
        while True:
            subreddit_posts = list(reddit.subreddit(subreddit).top(time_filter='day', limit=500, params={'after': after}))
            
            if not subreddit_posts:
                break

            for post in subreddit_posts:
                subreddit_activity[subreddit] += 1
                subreddit_karma[subreddit] += post.score
                subreddit_comments[subreddit] += post.num_comments

                if post.author is not None:
                    subreddit_users_karma[subreddit][post.author.name] += post.score

                subreddit_users_posts[subreddit].append(post)

                if post.over_18:
                    subreddit_nsfw_count[subreddit] += 1
                    subreddit_nsfw_comments[subreddit] += post.num_comments
                else:
                    subreddit_sfw_count[subreddit] += 1
                    subreddit_sfw_comments[subreddit] += post.num_comments
            
            after = subreddit_posts[-1].fullname
            
            if len(subreddit_posts) < 500:
                break
            
            print('Pausing to stay within PRAW rate limits...')
            time.sleep(1)

        subreddit_obj = reddit.subreddit(subreddit)
        subreddit_subscribers[subreddit] = subreddit_obj.subscribers
    
    return top_100_subreddits, subreddit_activity, subreddit_karma, subreddit_comments, subreddit_subscribers, subreddit_sfw_count, subreddit_nsfw_count, subreddit_sfw_comments, subreddit_nsfw_comments, subreddit_users_karma, subreddit_users_posts

# Save data to CSV function
def save_data_to_csv(top_subreddits, date, subreddit_activity, subreddit_karma, subreddit_comments, subreddit_subscribers, subreddit_sfw_count, subreddit_nsfw_count, subreddit_sfw_comments, subreddit_nsfw_comments):
    subreddit_stats = []
    for subreddit, _ in top_subreddits:
        post_count = subreddit_activity[subreddit]
        karma_count = subreddit_karma[subreddit]
        comment_count = subreddit_comments[subreddit]
        subscriber_count = subreddit_subscribers[subreddit]
        sfw_percentage = (subreddit_sfw_count[subreddit] / post_count) * 100 if post_count > 0 else 0
        nsfw_percentage = (subreddit_nsfw_count[subreddit] / post_count) * 100 if post_count > 0 else 0
        subreddit_stats.append([subreddit, post_count, karma_count, comment_count, subscriber_count, 
                                subreddit_sfw_count[subreddit], subreddit_nsfw_count[subreddit],
                                subreddit_sfw_comments[subreddit], subreddit_nsfw_comments[subreddit],
                                sfw_percentage, nsfw_percentage])
    
    subreddit_stats_df = pd.DataFrame(subreddit_stats, columns=['Subreddit', 'Posts in Last 24 Hours', 
                                                                'Total Karma in Last 24 Hours', 'Total Comments in Last 24 Hours', 
                                                                'Subscribers', 'SFW Posts', 'NSFW Posts', 
                                                                'SFW Comments', 'NSFW Comments', 
                                                                'SFW Posts %', 'NSFW Posts %'])
    subreddit_stats_df.to_csv(f'subreddit_stats_{date}.csv', index=False)

    return subreddit_stats_df

# Pre-cache graphs
def pre_cache_graphs(subreddits, subreddit_users_karma, posts_data):
    for subreddit, _ in subreddits:
        print(f"Pre-caching data for subreddit: {subreddit}")
        top_posts = list(reddit.subreddit(subreddit).top(time_filter='day', limit=100))
        keyword_fig = create_keyword_graph(subreddit, top_posts) 
        keyword_graph_cache[subreddit] = keyword_fig
        top_words_fig = create_top_words_graph(subreddit, top_posts, custom_stop_words)
        top_words_cache[subreddit] = top_words_fig
        user_fig = create_user_karma_graph(subreddit, subreddit_users_karma)
        user_graph_cache[subreddit] = user_fig
        bubble_chart_fig = create_user_karma_time_scatter(subreddit, subreddit_users_karma, posts_data)
        user_graph_cache[subreddit + "_bubble"] = bubble_chart_fig
        cooccurrence_fig = create_cooccurrence_graph(subreddit, top_posts, custom_stop_words)
        user_graph_cache[subreddit + "_cooccurrence"] = cooccurrence_fig 


# Dash App Initialization
app = Dash(__name__)

# Main Layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=True),  # Location component for URL redirection
    dcc.Store(id='subreddit-url-store'),  # Store component for subreddit URL
    dcc.Graph(id='main-graph'),
    html.Script(src='https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js'),
    html.Script(
        '''
        $(document).ready(function(){
            $('#url').on('click', function(){
                var url = $(this).attr('href');
                if(url){
                    window.open(url, '_blank');
                    $(this).removeAttr('href');
                }
            });
        });
        '''
    ),
    html.Div([
        dcc.Graph(id='keyword-graph', style={'width': '50%', 'display': 'inline-block', 'vertical-align': 'top'}),
        dcc.Graph(id='top-words-graph', style={'width': '50%', 'display': 'inline-block', 'vertical-align': 'top'}),
    ]),
    html.Div([
        dcc.Graph(id='bubble-chart', style={'width': '50%', 'display': 'inline-block', 'vertical-align': 'top'}),
        dcc.Graph(id='user-graph', style={'width': '50%', 'display': 'inline-block', 'vertical-align': 'top'}),
    ]),
    html.Div([
        dcc.Graph(id='cooccurrence-graph', style={'width': '100%', 'display': 'inline-block', 'vertical-align': 'top'}),
    ])
])


# Main graph update function
@app.callback(
    Output('main-graph', 'figure'),
    Input('main-graph', 'id')
)
def update_main_graph(_):
    top_subreddits, subreddit_activity, subreddit_karma, subreddit_comments, subreddit_subscribers, \
    subreddit_sfw_count, subreddit_nsfw_count, subreddit_sfw_comments, subreddit_nsfw_comments, subreddit_users_karma, subreddit_users_posts = get_reddit_data()

    pre_cache_graphs(top_subreddits, subreddit_users_karma, subreddit_users_posts)

    subreddit_stats_df = save_data_to_csv(top_subreddits, datetime.now().strftime('%Y-%m-%d'),
                                          subreddit_activity, subreddit_karma, subreddit_comments,
                                          subreddit_subscribers, subreddit_sfw_count, subreddit_nsfw_count,
                                          subreddit_sfw_comments, subreddit_nsfw_comments)

    subreddit_stats_df = subreddit_stats_df.sort_values(by='Total Karma in Last 24 Hours', ascending=False)

    hover_template_sfw = (
        "Subreddit (SFW Content): %{x}<br>" +
        "Subscribers: %{customdata[2]:,.0f}<br>" +
        "Karma: %{y:,.0f}<br>" +
        "Total SFW Posts: %{customdata[0]:,.0f}<br>" +
        "Total SFW Comments: %{customdata[1]:,.0f}<br>" +
        "SFW Posts Percentage: %{customdata[3]:.2f}%<extra></extra>"
    )

    hover_template_nsfw = (
        "Subreddit (NSFW Content): %{x}<br>" +
        "Subscribers: %{customdata[2]:,.0f}<br>" +
        "Karma: %{y:,.0f}<br>" +
        "Total NSFW Posts: %{customdata[0]:,.0f}<br>" +
        "Total NSFW Comments: %{customdata[1]:,.0f}<br>" +
        "NSFW Posts Percentage: %{customdata[3]:.2f}%<extra></extra>"
    )
    
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=subreddit_stats_df['Subreddit'],
        y=subreddit_stats_df['Total Karma in Last 24 Hours'] * (subreddit_stats_df['SFW Posts %'] / 100),
        name='SFW Posts',
        marker=dict(color='blue'),
        hovertemplate=hover_template_sfw,
        customdata=subreddit_stats_df[['SFW Posts', 'SFW Comments', 'Subscribers', 'SFW Posts %']]
    ))

    fig.add_trace(go.Bar(
        x=subreddit_stats_df['Subreddit'],
        y=subreddit_stats_df['Total Karma in Last 24 Hours'] * (subreddit_stats_df['NSFW Posts %'] / 100),
        name='NSFW Posts',
        marker=dict(color='red'),
        hovertemplate=hover_template_nsfw,
        customdata=subreddit_stats_df[['NSFW Posts', 'NSFW Comments', 'Subscribers', 'NSFW Posts %']]
    ))

    fig.update_layout(
        barmode='stack',
        xaxis=dict(
            tickmode='linear',
            tickangle=45,
            range=[-1, 10],
            showgrid=False,
            zeroline=False,
        ),
        xaxis_rangeslider=dict(visible=True),
        showlegend=False
    )
    
    fig.update_layout(title='Top 100 Subreddits by Total Karma in Last 24 Hours',
                      xaxis_title='Subreddit',
                      yaxis_title='Total Karma in Last 24 Hours',
                      height=450)

    return fig

# Combined URL click callback for both subreddit and post URLs
@app.callback(
    Output('url', 'href'),
    Input('main-graph', 'clickData'),
    Input('bubble-chart', 'clickData'),
    prevent_initial_call=True
)
def open_url_on_click(main_click_data, bubble_click_data):
    ctx = callback_context

    if not ctx.triggered:
        return None
    
    # Determine which graph was clicked
    triggered_input = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_input == 'main-graph' and main_click_data and 'points' in main_click_data:
        subreddit = main_click_data['points'][0]['x']
        return f"https://www.reddit.com/r/{subreddit}"

    if triggered_input == 'bubble-chart' and bubble_click_data and 'points' in bubble_click_data:
        post_url = bubble_click_data['points'][0]['customdata'][4]  # Extract the URL from the custom data
        return post_url

    return None

# Update graphs callback
@app.callback(
    Output('keyword-graph', 'figure'),
    Output('top-words-graph', 'figure'),
    Output('user-graph', 'figure'),
    Output('bubble-chart', 'figure'),
    Output('cooccurrence-graph', 'figure'),
    Input('main-graph', 'hoverData')
)
def update_graphs(hoverData):
    if hoverData is None or 'points' not in hoverData or len(hoverData['points']) == 0:
        print("No bar was hovered over.")
        return go.Figure(), go.Figure(), go.Figure(), go.Figure(), go.Figure()

    hovered_subreddit = hoverData['points'][0]['x']
    print(f"Hovered subreddit: {hovered_subreddit}")

    keyword_fig = keyword_graph_cache.get(hovered_subreddit, go.Figure())
    top_words_fig = top_words_cache.get(hovered_subreddit, go.Figure())
    user_fig = user_graph_cache.get(hovered_subreddit, go.Figure())
    bubble_chart_fig = user_graph_cache.get(hovered_subreddit + "_bubble", go.Figure())
    cooccurrence_fig = user_graph_cache.get(hovered_subreddit + "_cooccurrence", go.Figure())

    return keyword_fig, top_words_fig, user_fig, bubble_chart_fig, cooccurrence_fig

if __name__ == "__main__":
    app.run_server(debug=True)
