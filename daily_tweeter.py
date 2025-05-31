# daily_tweeter.py
#
# Description:
# This script generates a daily tweet draft based on your recent tweet history using
# the OpenAI GPT model (gpt-3.5-turbo). It fetches your latest tweets, sends them
# as context to the LLM, and prints the AI-generated tweet suggestion.
#
# THIS SCRIPT OUTPUTS A DRAFT TWEET TO THE CONSOLE. IT DOES NOT POST TO TWITTER AUTOMATICALLY.
# You should review the generated draft carefully before manually posting it.
#
# Setup:
# 1. Install necessary Python libraries:
#    pip install tweepy openai
#
# 2. Set Twitter API v2 Credentials as environment variables:
#    - TWITTER_API_KEY: Your Twitter App's API Key
#    - TWITTER_API_SECRET: Your Twitter App's API Key Secret
#    - TWITTER_ACCESS_TOKEN: Your Access Token
#    - TWITTER_ACCESS_TOKEN_SECRET: Your Access Token Secret
#
# 3. Set your OpenAI API Key as an environment variable:
#    - OPENAI_API_KEY: Your OpenAI API Key
#
# Execution:
# Run the script from your terminal:
#    python daily_tweeter.py
#
# The script will then print the suggested tweet draft to your console.
#
# Scheduling:
# This script can be run daily using a scheduler (e.g., cron on Linux/macOS,
# Task Scheduler on Windows, or a cloud-based scheduler like AWS Lambda).
# Ensure the execution environment for the scheduler has Python, the required
# libraries (tweepy, openai), and all necessary environment variables configured.
# The output (draft tweet or errors) will be sent to standard output/error streams,
# which can typically be captured by your scheduler's logging mechanism.

import tweepy
import os
import openai # Added for LLM integration

# --- Twitter API Authentication ---
try:
    twitter_consumer_key = os.environ['TWITTER_API_KEY']
    twitter_consumer_secret = os.environ['TWITTER_API_SECRET']
    twitter_access_token = os.environ['TWITTER_ACCESS_TOKEN']
    twitter_access_token_secret = os.environ['TWITTER_ACCESS_TOKEN_SECRET']
except KeyError as e:
    print(f"Error: Missing Twitter environment variable {e}. Please ensure all Twitter API credentials are set.")
    exit(1)

# Authenticate to Twitter
try:
    twitter_client = tweepy.Client(
        consumer_key=twitter_consumer_key,
        consumer_secret=twitter_consumer_secret,
        access_token=twitter_access_token,
        access_token_secret=twitter_access_token_secret
    )
    print("Twitter authentication successful.")
except tweepy.TweepyException as e:
    print(f"Error during Twitter authentication: {e}")
    exit(1)

# --- OpenAI API Authentication ---
try:
    openai.api_key = os.environ['OPENAI_API_KEY']
    # Test connection or list models to verify key (optional, but good practice)
    # For example, openai.Model.list() - requires openai version < 1.0
    # For openai version >= 1.0, client initialization handles this:
    openai_client = openai.OpenAI() # Initialize OpenAI client (v1.0+)
    print("OpenAI API key loaded and client initialized.")
except KeyError as e:
    print(f"Error: Missing environment variable OPENAI_API_KEY. Please ensure it is set.")
    exit(1)
except openai.APIError as e: # Catching potential errors during OpenAI client init
    print(f"Error initializing OpenAI client: {e}")
    exit(1)

# --- Twitter Functionality ---

def get_my_user_id(client: tweepy.Client):
    """Fetches the user ID of the authenticated user."""
    try:
        response = client.get_me(user_fields=["id"])
        if response.data:
            return response.data.id
        else:
            print("Error: Could not fetch authenticated user's ID.")
            return None
    except tweepy.TweepyException as e:
        print(f"Error fetching user ID: {e}")
        return None

def get_recent_tweets(client: tweepy.Client, user_id: str, count: int = 25):
    """
    Fetches the most recent tweets for a given user ID, excluding retweets and replies.
    Args:
        client (tweepy.Client): Initialized Tweepy client.
        user_id (str): The Twitter user ID.
        count (int): Number of tweets to fetch. Max is 100 per request for this endpoint.
    Returns:
        list[str]: A list of tweet texts, or an empty list if an error occurs or no tweets.
    """
    if not user_id:
        return []
    recent_tweets_text = []
    try:
        response = client.get_users_tweets(
            id=user_id,
            max_results=count,
            exclude=["retweets", "replies"], # Exclude retweets and replies
            tweet_fields=["text"] # Specify that we only need the text of the tweet
        )
        if response.data:
            for tweet in response.data:
                recent_tweets_text.append(tweet.text)
            print(f"Fetched {len(recent_tweets_text)} recent tweets.")
        else:
            print("No recent tweets found or user has no tweets.")
        return recent_tweets_text
    except tweepy.TweepyException as e:
        print(f"Error fetching recent tweets: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while fetching tweets: {e}")
        return []

# --- OpenAI LLM Tweet Generation ---
def generate_llm_tweet(client: openai.OpenAI, history_tweets: list[str]):
    """
    Generates a new tweet using OpenAI's GPT model based on recent tweet history.
    Args:
        client (openai.OpenAI): Initialized OpenAI client.
        history_tweets (list[str]): A list of recent tweet texts.
    Returns:
        str: The generated tweet text, or None if an error occurs.
    """
    if not history_tweets:
        print("No tweet history provided to LLM. Cannot generate tweet.")
        return None

    # Format the history for the prompt
    formatted_history = "\n".join([f"- "{tweet}"" for tweet in history_tweets])

    # Craft the prompt
    # System message sets the context for the AI
    system_message = (
        "You are a helpful assistant that writes tweets. "
        "Generate a new, original tweet that is inspired by the user's recent tweet history. "
        "The new tweet should be concise, engaging, and suitable for Twitter (under 280 characters). "
        "Do not directly copy phrases from the history unless it's a common expression. "
        "Try to match the general tone and topics of the provided tweets."
    )

    # User message provides the specific data (tweet history)
    user_message_content = (
        "Here is my recent tweet history:\n"
        f"{formatted_history}\n\n"
        "Please generate a new tweet for me based on this history."
    )

    print("\nSending request to OpenAI LLM...")
    print(f"System Prompt: {system_message[:200]}...") # Log snippet
    print(f"User Prompt (history part): {user_message_content[:200]}...") # Log snippet

    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message_content}
            ],
            max_tokens=70,  # Max length of a tweet (approx 280 chars / 4 chars_per_token)
            temperature=0.7, # Balances creativity and coherence
            n=1, # Generate one tweet
            stop=None # Let the model decide when to stop, or use specific stop sequences
        )

        if completion.choices and completion.choices[0].message:
            generated_text = completion.choices[0].message.content.strip()

            # Basic check for empty or placeholder responses
            if not generated_text or len(generated_text) < 10:
                print(f"LLM generated a very short or empty response: '{generated_text}'. Not using.")
                return None

            # Optional: Add a small filter for common refusal phrases if observed
            refusal_phrases = ["I cannot fulfill this request", "I am unable to", "As an AI model"]
            if any(phrase.lower() in generated_text.lower() for phrase in refusal_phrases):
                print(f"LLM response seems like a refusal: '{generated_text}'. Not using.")
                return None

            print(f"LLM generated tweet: {generated_text}")
            return generated_text
        else:
            print("Error: OpenAI API call did not return expected choices or message.")
            if completion:
                 print(f"Full API Response (choices part): {completion.choices}")
            return None

    except openai.APIError as e:
        print(f"OpenAI API error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during LLM tweet generation: {e}")
        return None

# --- Original Tweet Functionality (to be modified/removed) ---
FIXED_TWEET_TEXT = "This is a daily tweet!" # Will be replaced by LLM output

def send_tweet(text_to_tweet): # This function might be used later or removed
    """
    Sends a tweet using the Twitter API v2.
    Args:
        text_to_tweet (str): The text content of the tweet.
    Returns:
        str: The ID of the created tweet if successful, None otherwise.
    """
    try:
        response = twitter_client.create_tweet(text=text_to_tweet)
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

# --- Main script logic (to be updated) ---
if __name__ == "__main__":
    print("Script initialized for LLM tweet generation.")

    # 1. Get authenticated user's ID
    my_id = get_my_user_id(twitter_client)

    if my_id:
        tweet_history = get_recent_tweets(twitter_client, my_id, count=25)
        if tweet_history:
            print("\nRecent Tweet History (for LLM context):")
            for i, text in enumerate(tweet_history[:3]): # Print first 3 for brevity
                print(f"  {i+1}. {text[:100]}...")

            # 3. Generate tweet with LLM
            generated_draft = generate_llm_tweet(openai_client, tweet_history)

            if generated_draft:
                print("\n--- GENERATED TWEET DRAFT ---")
                print(generated_draft)
                print("--- END OF DRAFT ---")
                print("\n(This draft was generated by an LLM. Review carefully before posting.)")
            else:
                print("\nLLM failed to generate a tweet draft.")
        else:
            print("No tweet history found to pass to LLM.")
    else:
        print("Could not proceed without user ID.")

    # Example of using the old send_tweet function (will be removed/changed)
    # print(f"Attempting to send fixed tweet: '{FIXED_TWEET_TEXT}'")
    # tweet_id_sent = send_tweet(FIXED_TWEET_TEXT)
    # if tweet_id_sent:
    #     print(f"Successfully posted fixed tweet with ID: {tweet_id_sent}")
    # else:
    #     print("Failed to post fixed tweet.")
