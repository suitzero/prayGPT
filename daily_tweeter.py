# daily_tweeter.py
#
# Description:
# This script sends a predefined, fixed tweet daily. It requires Twitter API v2 credentials.
#
# Setup:
# 1. Install the tweepy library:
#    pip install tweepy
#
# 2. Set the following environment variables with your Twitter Developer App credentials:
#    - TWITTER_API_KEY: Your API Key
#    - TWITTER_API_SECRET: Your API Key Secret
#    - TWITTER_ACCESS_TOKEN: Your Access Token
#    - TWITTER_ACCESS_TOKEN_SECRET: Your Access Token Secret
#
# 3. (Optional) Modify the FIXED_TWEET_TEXT variable in this script to change the tweet content.
#
# Execution:
# Run the script from your terminal:
#    python daily_tweeter.py
#
# Scheduling:
# This script is designed to be run by a scheduler (e.g., cron, AWS Lambda, Windows Task Scheduler).
# Ensure the execution environment for the scheduler has Python, tweepy, and the environment
# variables configured. Output (including errors) will be printed to standard output/error streams,
# which can typically be captured by the scheduler's logging mechanism.

import tweepy
import os

# --- Twitter API Authentication ---
# Load credentials from environment variables
try:
    consumer_key = os.environ['TWITTER_API_KEY']
    consumer_secret = os.environ['TWITTER_API_SECRET']
    access_token = os.environ['TWITTER_ACCESS_TOKEN']
    access_token_secret = os.environ['TWITTER_ACCESS_TOKEN_SECRET']
except KeyError as e:
    print(f"Error: Missing environment variable {e}. Please ensure all Twitter API credentials are set.")
    exit(1)

# Authenticate to Twitter
try:
    # For Twitter API v2, you need a Client instance
    client = tweepy.Client(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_token,
        access_token_secret=access_token_secret
    )
    print("Authentication successful.")

except tweepy.TweepyException as e:
    print(f"Error during authentication: {e}")
    exit(1)

# --- Tweet Functionality ---
# Modify this string to change the content of your daily tweet
FIXED_TWEET_TEXT = "This is a daily tweet!"

def send_tweet(text_to_tweet):
    """
    Sends a tweet using the Twitter API v2.
    Args:
        text_to_tweet (str): The text content of the tweet.
    Returns:
        str: The ID of the created tweet if successful, None otherwise.
    """
    try:
        response = client.create_tweet(text=text_to_tweet)
        if response.data and response.data.get('id'):
            tweet_id = response.data['id']
            print(f"Tweet sent successfully! Tweet ID: {tweet_id}")
            return tweet_id
        else:
            print(f"Error sending tweet: No tweet ID in response. Response: {response}")
            return None
    except tweepy.TweepyException as e:
        print(f"Error sending tweet: {e}")
        return None

# --- Main script logic ---
if __name__ == "__main__":
    print(f"Attempting to send tweet: '{FIXED_TWEET_TEXT}'")
    tweet_id_sent = send_tweet(FIXED_TWEET_TEXT)
    if tweet_id_sent:
        print(f"Successfully posted tweet with ID: {tweet_id_sent}")
    else:
        print("Failed to post tweet.")
