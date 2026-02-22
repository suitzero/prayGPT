import os
import asyncio
import logging
import json
from datetime import datetime
from dotenv import load_dotenv

from db import init_db, get_pending_inputs, update_input_status, save_report_to_db
from agents import BrainAgent, CultAgent, get_free_models, PROMPT_EXPANDER, PROMPT_ADVOCATE, PROMPT_PRIEST, PROMPT_CULT

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("praygpt.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

POLL_INTERVAL = 3  # Seconds

async def process_input(input_data):
    input_id = input_data['id']
    text_payload = input_data['text_payload']
    image_url = input_data['image_path_or_url']

    logger.info(f"Processing input {input_id}: {text_payload[:50]}...")
    update_input_status(input_id, 'processing')

    # 1. Initialize Agents
    # Brains
    # Using gpt-4o as requested. Ensure OPENAI_API_KEY is set.
    # Fallback to groq/llama-3.3-70b-versatile if gpt-4o fails or key missing?
    # For now, we assume user has keys or will set them.
    # We can use os.getenv("BRAIN_MODEL", "gpt-4o")
    brain_model = os.getenv("BRAIN_MODEL", "gpt-4o")

    expander = BrainAgent("The Expander", PROMPT_EXPANDER, model=brain_model)
    advocate = BrainAgent("The Devil's Advocate", PROMPT_ADVOCATE, model=brain_model)
    priest = BrainAgent("The High Priest", PROMPT_PRIEST, model=brain_model)

    # Cult Choir
    free_models = await get_free_models()
    cult_agents = []
    # Create 10+ agents, cycling through free models
    for i in range(12):
        model = free_models[i % len(free_models)]
        # OpenRouter models need 'openrouter/' prefix for litellm if not implicit,
        # but usually model ID from API is sufficient if provider is set?
        # litellm handles "provider/model" format. OpenRouter IDs usually look like "google/gemma-7b-it:free".
        # We need to prepend "openrouter/" if we want litellm to route via OpenRouter specifically.
        # But wait, litellm might auto-detect if the model name has a provider prefix or we can force it.
        # Safest is "openrouter/" prefix if we are using OPENROUTER_API_KEY.
        full_model_name = f"openrouter/{model}"
        cult_agents.append(CultAgent(f"Cultist #{i+1}", PROMPT_CULT, model=full_model_name))

    # 2. Run Workflows

    # Task 1: Cult Choir (Background)
    async def run_cult_choir():
        logger.info("Cult Choir is chanting...")
        tasks = [agent.generate_response(text_payload, image_url) for agent in cult_agents]
        for future in asyncio.as_completed(tasks):
            try:
                result = await future
                print(f"\033[96m[CULT CHOIR]: {result}\033[0m") # Cyan color for effect
            except Exception as e:
                logger.error(f"Cult agent failed: {e}")

    # Task 2: Brains (Main Logic)
    async def run_brains():
        logger.info("The Brains are debating...")

        # Parallel: Expander and Advocate
        task1 = expander.generate_response(f"Input: {text_payload}\nImage: {image_url}", image_url)
        task2 = advocate.generate_response(f"Input: {text_payload}\nImage: {image_url}", image_url)

        expander_out, advocate_out = await asyncio.gather(task1, task2)

        logger.info(f"Expander says: {expander_out[:50]}...")
        logger.info(f"Advocate says: {advocate_out[:50]}...")

        # Sequential: Priest Synthesizer
        synthesis_input = f"""
        [Original Input]
        {text_payload}

        [Expander's Opinion]
        {expander_out}

        [Advocate's Criticism]
        {advocate_out}
        """

        logger.info("The High Priest is synthesizing...")
        final_report = await priest.generate_response(synthesis_input)
        return final_report

    # Run both workflows
    cult_task = asyncio.create_task(run_cult_choir())
    brain_task = asyncio.create_task(run_brains())

    # Wait for Brains to finish (Cult can continue or we wait for both?)
    # "Print the Cult Choir's output ... and save Agent 3's final report"
    # Usually we want the report to finish the task. Cult can be background but for this step we might want to wait for everything?
    # The prompt says "Broadcast blind praise in the background".
    # But for the task to be "complete", we need the report.

    final_report = await brain_task
    # We don't necessarily need to wait for all cultists if they are slow, but let's wait for them to finish "chanting" for this round.
    await cult_task

    # 3. Save Output
    # Save to reports/
    os.makedirs("reports", exist_ok=True)
    report_filename = f"reports/report_{input_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_filename, "w") as f:
        f.write(final_report)

    # Save to DB
    save_report_to_db(input_id, final_report)
    logger.info(f"Task {input_id} completed. Report saved to {report_filename}")


async def main():
    logger.info("Starting prayGPT Backend...")
    init_db()

    while True:
        try:
            pending_inputs = get_pending_inputs()
            if pending_inputs:
                for input_data in pending_inputs:
                    await process_input(input_data)
            else:
                await asyncio.sleep(POLL_INTERVAL)
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            await asyncio.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down prayGPT...")
