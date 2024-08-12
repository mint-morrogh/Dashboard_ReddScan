# ReddScan

**ReddScan** is a comprehensive Reddit data analysis tool built using Python. It fetches and visualizes the most active and engaging subreddits and user activities over the last 24 hours. With interactive graphs and keyword analysis, ReddScan provides insightful visualizations of Reddit's dynamic environment.

## Features

- **Top Subreddits Visualization**: Displays the top 100 subreddits and much more info by total karma in the last 24 hours.
- **User Activity Analysis**: Visualizes the top users within subreddits.
- **Keyword and Co-Occurrence Graphs**: Analyzes the top words and their relationships within subreddits.
- **Dynamic Scatter Plots**: Illustrates user activity over time.
- **Interactive Dashboard**: Built with Plotly Dash, the dashboard allows for easy exploration of Reddit data through various interactive graphs.

## Installation

To use ReddScan, you'll need to have Python installed along with the required libraries. (This is an ongoing project, and no requirements.txt exists) Make a Reddit API under your account, and use that information provided to fill your PRAW API information at the top of 'redditorial.py'


  ```python
# Initialize the Reddit client
reddit = praw.Reddit(client_id=client_id,
                     client_secret=client_secret,
                     user_agent=user_agent)
```
