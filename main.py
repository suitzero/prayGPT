import os
import time
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

from agents import IdeatorAgent, CriticAgent, SynthesizerAgent
from email_sender import EmailSender

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("project28.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

MEMORY_FILE = os.path.join("data", "memory.json")
LOOP_INTERVAL = int(os.getenv("LOOP_INTERVAL", 180))

# Ensure data directory exists
os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error("Failed to decode memory file. Starting fresh.")
    return {"context": "", "insights": [], "last_sent_date": None}

def save_memory(memory):
    try:
        with open(MEMORY_FILE, 'w') as f:
            json.dump(memory, f, indent=4)
    except Exception as e:
        logger.error(f"Failed to save memory: {e}")

def main():
    logger.info("Starting Project 28 - AI Business Meditation System")

    # Initialize Agents
    ideator = IdeatorAgent()
    critic = CriticAgent()
    synthesizer = SynthesizerAgent()
    email_sender = EmailSender()

    while True:
        try:
            logger.info("Starting new loop iteration...")
            memory = load_memory()

            context = memory.get("context", "")
            insights = memory.get("insights", [])
            last_sent_date = memory.get("last_sent_date")

            # --- Agent Pipeline ---

            # 1. Ideator
            logger.info("Agent A (Ideator) is thinking...")
            idea = ideator.brainstorm(context)
            logger.info(f"Idea generated: {idea[:100]}...")

            # 2. Critic
            logger.info("Agent B (Critic) is reviewing...")
            critique = critic.critique(idea)
            logger.info(f"Critique provided: {critique[:100]}...")

            # 3. Synthesizer
            logger.info("Agent C (Synthesizer) is summarizing...")
            # We pass the previous context as history to keep continuity
            new_insight = synthesizer.synthesize(idea, critique, context)
            logger.info(f"Insight synthesized: {new_insight[:100]}...")

            # Update Memory
            # The new insight becomes the context for the next round
            memory["context"] = new_insight

            # Add to accumulated insights for the report
            # We might want to store it with a timestamp
            insight_entry = {
                "timestamp": datetime.now().isoformat(),
                "content": new_insight
            }
            insights.append(insight_entry)
            memory["insights"] = insights

            # Save intermediate state
            save_memory(memory)

            # --- Email Reporting ---
            if email_sender.should_send_email(last_sent_date):
                logger.info("Time to send daily report.")

                # Format insights for email (extract content)
                report_content = [i["content"] for i in insights]

                if email_sender.send_report(report_content):
                    logger.info("Report sent successfully. Clearing accumulated insights.")
                    # Clear insights after sending, but keep context
                    memory["insights"] = []
                    memory["last_sent_date"] = datetime.now().strftime("%Y-%m-%d")
                    save_memory(memory)
                else:
                    logger.error("Failed to send report. Will try again next loop.")

            logger.info(f"Sleeping for {LOOP_INTERVAL} seconds...")
            time.sleep(LOOP_INTERVAL)

        except KeyboardInterrupt:
            logger.info("Stopping Project 28...")
            break
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
            logger.info("Restarting loop in 60 seconds due to error...")
            time.sleep(60)

if __name__ == "__main__":
    main()
