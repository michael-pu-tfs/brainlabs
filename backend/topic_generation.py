from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
import pandas as pd
import openai
import re
import time
import logging
import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

project_id = "halcyon-414514"
dataset_id = "B_n_Q"
difficulty_table = "Topic_SubTopic_V4_data"

# Logging setup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Global variable to track token usage
total_tokens_used = 0


def run_openai_api(prompt, max_retries=10):
    """
    Calls the OpenAI Chat Completion API with retry logic.
    """
    retries = 0
    backoff_factor = 2
    delay = 1

    while retries < max_retries:
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {"role": "system", "content": "You are an intelligent SEO Expert."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1000,
                temperature=0.0,
            )

            result_content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens

            global total_tokens_used
            total_tokens_used += tokens_used

            return result_content
        except openai.RateLimitError as e:
            retries += 1
            logging.warning(
                f"Rate limit error: {e}. Retrying in {delay:.2f} seconds... (Attempt {retries}/{max_retries})"
            )
            time.sleep(delay)
            delay *= backoff_factor
        except Exception as e:
            logging.error(f"Error in OpenAI API call: {e}")
            raise

    raise Exception("Failed after max retries due to rate limit or other issues.")


# Function to extract topic and subtopic
def extract_topic_subtopic(response):
    try:
        # Handle "Topic | Subtopic" pattern with square brackets
        match = re.search(r"(\[[^\]]+\])\s*\|\s*(\[[^\]]+\])", response)
        if match:
            return pd.Series(
                {
                    "topic": match.group(1).strip("[]"),
                    "subtopic": match.group(2).strip("[]"),
                }
            )

        # Handle "Topic | Subtopic" pattern with quotes
        match = re.search(r'"([^"]+)"\s*\|\s*"([^"]+)"', response)
        if match:
            return pd.Series({"topic": match.group(1), "subtopic": match.group(2)})

        # Handle "Topic | Subtopic" pattern without quotes (spaces, product codes, etc.)
        match = re.search(r"([^\|]+)\s*\|\s*([^\|]+)", response)
        if match:
            return pd.Series(
                {"topic": match.group(1).strip(), "subtopic": match.group(2).strip()}
            )

        # Handle cases with 'Input Keyword' and 'Output'
        output_match = re.search(
            r'Output:\s*"([^"]+)"\s*\|\s*"([^"]+)"', response, re.IGNORECASE
        )
        if output_match:
            return pd.Series(
                {"topic": output_match.group(1), "subtopic": output_match.group(2)}
            )

        # If no match, raise an error to handle it below
        raise ValueError("Pattern not found")

    except Exception:
        return pd.Series({"topic": None, "subtopic": None})
        # Return None for topic and subtopic
        return pd.Series({"topic": None, "subtopic": None})


def construct_prompt(keywords):
    """
    Constructs the prompt for the OpenAI API.
    """
    return f""" SEO Keyword Clustering for Topic and Subtopic Classification
                Purpose: Optimize keyword categorization for SEO strategy and content planning.

                ## Task
                Generate a Topic and a Subtopic for the provided list of keywords following strict categorization rules. Topics must be concise and specific, while Subtopics must reflect precise searcher intent.

                ## Output Format
                "Topic | Subtopic"

                - No specific subtopic exists: Output "-" for subtopic
                - Unclear or unrelated keywords: Output "- | -"

                ## Guidelines for SEO Classification

                ### 1. Topic Creation
                - Use concise, specific names that capture the core category
                - Maintain consistent naming conventions across similar categories
                - For brand-specific keywords, always include brand name at topic level
                - Avoid lengthy descriptive phrases in topic names
                - Break down broad categories into more specific topics when possible

                ### 2. Subtopic Creation
                - Create distinct subtopics for different user intents (informational vs. transactional)
                - Separate material types, colors, and specific features into their own subtopics
                - Use clear, specific intent markers:
                - Informational: "How To", "Guide", "Understanding"
                - Transactional: "Shopping", "Comparison", "Options"
                - Never combine different intents in one subtopic

                ### 3. Intent Classification Rules
                Informational Keywords:
                - Learning-focused queries (what, how, why)
                - Process understanding
                - Problem-solving queries
                - Usage instructions

                Transactional Keywords:
                - Purchase-focused queries
                - Product comparisons
                - Price-related searches
                - Brand/model specific searches

                ### 4. Granularity Guidelines
                - Split broad categories when keywords suggest distinct subcategories
                - Create separate subtopics for:
                - Materials (e.g., "Wooden", "Metal", "Plastic")
                - Applications (e.g., "Kitchen Use", "Bathroom Use")
                - Skill Levels (e.g., "Beginner", "Professional")
                - Features (e.g., "Cordless", "Manual")

                ## Examples with Intent Separation

                Input Keywords:
                best vacuum cleaner, vaccum cleaner
                Output:
                "Vacuum Cleaners" | "Product Comparison & Selection"

                Input Keywords:
                how to use vacuum cleaner, guide to use vaccum cleaner
                Output:
                "Vacuum Cleaners" | "Usage & Maintenance Guide"

                Input Keywords:
                milwaukee m18 drill price
                Output:
                "Milwaukee M18 Drills" | "Shopping & Pricing"

                Input Keywords:
                how to use milwaukee m18 drill", ", "milwaukee 
                Output:
                "Milwaukee M18 Drills" | "Usage Instructions"

                Input Keywords:
                "milwaukee m18 drill manual"

                Input Keywords:
                ["inset sink stainless steel", "granite inset sink", "ceramic inset sink"]
                Output:
                "Inset Sinks" | "Material Options"

                ## Constraints

                ### Must Follow
                - Maintain consistent topic structure across similar categories
                - Use specific, intent-focused subtopics
                - Separate different materials, colors, or features into distinct subtopics
                - Keep topics concise and specific
                - Always categorize brand-specific keywords at the topic level

                ### Must Avoid
                - Mixing informational and transactional intents in one subtopic
                - Using generic subtopics without clear intent
                - Creating overly broad or lengthy topic names
                - Inconsistent handling of brand-specific content
                - Combining different materials or features in one subtopic

                ### Input Keywords List:
                Keywords: {keywords}"""


def apply_openai_api(keywords):
    """
    Calls the OpenAI API for a given keyword and processes the response.
    """
    try:
        prompt = construct_prompt(keywords)
        response = run_openai_api(prompt)
        return response
    except Exception as e:
        logging.error(f"Error processing keyword '{keywords}': {e}")
        return None


def process_row_parallel(keywords_list, max_workers=5):
    """
    Processes rows in parallel using ThreadPoolExecutor.
    """
    responses = [None] * len(
        keywords_list
    )  # Initialize the responses list with None values

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all jobs and store future-to-index mapping
        future_to_index = {
            executor.submit(apply_openai_api, keywords): index
            for index, keywords in enumerate(keywords_list)
        }

        # Collect results as they complete
        for future in as_completed(future_to_index):
            index = future_to_index[future]  # Get the index of the keyword in the list
            try:
                response = future.result()
                responses[index] = response  # Store the result at the correct index
            except Exception as e:
                logging.error(
                    f"Error processing keywords '{keywords_list[index]}': {e}"
                )
                responses[index] = None  # If error occurs, store None at the index

    return responses


def main():
    # Load your dataset
    cluster_df = pd.read_csv("cluster_analysis.csv")

    keywords_list = [
        ",".join(i[1:-1].replace("'", "").split(","))
        for i in cluster_df["keywords"].tolist()
    ]
    # # Process rows in parallel
    logging.info("Starting parallel processing of keywords...")
    cluster_df["response"] = process_row_parallel(keywords_list)

    cluster_df[["Topic", "Subtopic"]] = cluster_df["response"].apply(
        lambda x: pd.Series(extract_topic_subtopic(x))
    )
    print(cluster_df)
    cluster_df.to_csv("samsung_topic_subtopic.csv", index=False)


if __name__ == "__main__":
    main()
