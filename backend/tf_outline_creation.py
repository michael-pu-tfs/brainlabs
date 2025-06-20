from flask import Flask, request, jsonify
from google.cloud import bigquery
from google.oauth2 import service_account
from openai import OpenAI
import json
import time
import re
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import logging
import faiss
import concurrent.futures
import random
import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


app = Flask(__name__)
app.config["DEBUG"] = True
total_tokens_used = 0
MAX_TOKEN_LIMIT = 1000
project_id = "thermofigher-gen-ai"
dataset_id = "pdp_data"
scraped_table_name = "biopharma_data"
extracted_keywords_table_name = "extracted_keywords_gpt4"
synonym_keywords_table_name = "synonym_keywords_gpt4"
similarity_table_name = "keyword_similarity_scores"

# service_account_key_path = "thermofigher-gen-ai-5255b69aa6e4.json"

# Initialize the OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

credentials = service_account.Credentials.from_service_account_file(
    service_account_key_path
)
bq_client = bigquery.Client(credentials=credentials, project=project_id)


def extract_text(body_text):
    match = re.search(r"< \[\.\.\.\](.*?)CUSTOMER SERVICES \+", body_text)
    return match.group(1).strip() if match else None


def mark_as_processed(url_slug):
    try:
        query = """
        UPDATE `halcyon-414514.halcyon_web_scraper.scraped_data_v1`
        SET processed = TRUE
        WHERE url_slug = @url_slug
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("url_slug", "STRING", url_slug)
            ]
        )
        bq_client.query(query, job_config=job_config).result()
        print(f"Marked {url_slug} as processed.")
    except Exception as e:
        print(f"Error processing {url_slug} as {e}")


def standardize_data(array_of_strings):
    standardized_array = []
    for s in array_of_strings:
        if len(s) > 1 and not s.isdigit():
            standardized_string = " ".join(s.split()).replace("-", " ").lower()
            if standardized_string:
                match = re.match(r"^(.*?)(\(\d+\))\s*$", standardized_string.strip())
                if match:
                    standardized_array.append(match.group(1))
                else:
                    standardized_array.append(standardized_string)
    return standardized_array


def get_embedding(text, max_retries=50):
    retries = 0
    while retries < max_retries:
        try:
            response = client.embeddings.create(
                input=[text.replace("\n", " ")],  # Input as a list
                model="text-embedding-3-small",
            )
            return np.array(response.data[0].embedding)

        except Exception as e:
            retries += 1
            delay = min(random.uniform(2, 4) * (2**retries), 60)
            logging.error(
                f"General error: {e}. Retrying in {delay:.2f} seconds... (Attempt {retries}/{max_retries})"
            )
            time.sleep(delay)

    raise Exception(
        f"Failed to process after {max_retries} retries due to persistent errors."
    )


def calculate_similarity(row):
    keyword_embedding = row["keyword_embedding"]
    h1_text_embedding = row["h1_text_embedding"]
    title_tag_embedding = row["title_tag_embedding"]
    combined_embedding = row["combined_embedding"]

    if pd.notna(row["h1-1_text"]) and row["h1-1_text"].strip():
        if pd.notna(row["title_tag_text"]) and row["title_tag_text"].strip():
            similarity_score_h1_text = cosine_similarity(
                [keyword_embedding], [h1_text_embedding]
            )[0][0]
            similarity_score_combined_text = cosine_similarity(
                [keyword_embedding], [combined_embedding]
            )[0][0]
            similarity_score = (similarity_score_h1_text * 0.5) + (
                similarity_score_combined_text * 0.5
            )
        else:
            similarity_score = cosine_similarity(
                [keyword_embedding], [h1_text_embedding]
            )[0][0]
    else:
        similarity_score = cosine_similarity(
            [keyword_embedding], [title_tag_embedding]
        )[0][0]

    return similarity_score


def get_embedding_if_valid(text):
    if pd.notna(text) and text.strip():
        return get_embedding(text)
    else:
        return None


def run_openai_api(text, page_text, heading_type):
    client = OpenAI(api_key=OPENAI_API_KEY)
    PROMPT = (
        generate_prompt(text, page_text, heading_type)
        + "\n\nPlease respond with a comma-separated list only, no other text."
    )

    try:
        # Send the request to OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[{"role": "user", "content": PROMPT}],
            max_tokens=MAX_TOKEN_LIMIT,
            temperature=0,
        )

        # Access the relevant data inside 'choices'
        inside_top_performing_kw = response.choices[0].message.content.strip()
        tokens_used = response.usage.total_tokens
        print(tokens_used)

        global total_tokens_used
        total_tokens_used += int(tokens_used)

        print("res", inside_top_performing_kw)

        # Validate the format: Check if it's a comma-separated list
        if (
            isinstance(inside_top_performing_kw, str)
            and "," in inside_top_performing_kw
        ):
            # Remove any unwanted text like periods, newlines, etc.
            sanitized_response = (
                inside_top_performing_kw.replace("\n", "")
                .replace(".", "")
                .replace('"', "")
            )
            # Split the sanitized string into a list
            try:
                result = [item.strip() for item in sanitized_response.split(",")]
                return result
            except Exception as parse_error:
                logging.error(f"Error parsing comma-separated list: {parse_error}")
                return None
        else:
            logging.error(
                "The response is not in the expected comma-separated list format."
            )
            return None

    except json.JSONDecodeError as json_error:
        logging.error(f"Error decoding JSON from OpenAI response: {json_error}")
        return None
    except Exception as e:
        logging.error(f"Error processing OpenAI response: {e}")
        return None


def extract_keywords_row_level(row, reference_keywords_obj):
    title = row.get("title")
    page_text = row.get("page_text")  # Use cleaned body text
    h1_1 = row.get("h1-1")
    h2_1 = row.get("H2-1")
    h2_2 = row.get("H2-2")

    if title:
        heading_type = "Title"
        reference_keywords_obj["title_tag"]["keywords"] = run_openai_api(
            title, page_text, heading_type
        )
    if h1_1:
        heading_type = "H1-1"
        reference_keywords_obj["h1-1"]["keywords"] = run_openai_api(
            h1_1, page_text, heading_type
        )
    if h2_1:
        heading_type = "H2-1"
        reference_keywords_obj["h2_1"]["keywords"] = run_openai_api(
            h2_1, page_text, heading_type
        )
    if h2_2:
        heading_type = "H2-2"
        reference_keywords_obj["h2_2"]["keywords"] = run_openai_api(
            h2_2, page_text, heading_type
        )
    return reference_keywords_obj


def generate_prompt(text, page_text, heading_type):
    PROMPT = f"""Role: You are an SEO expert specializing in heading optimization and title tag creation.

                Task: Generate 3-5 SEO-optimized versions of the provided {heading_type} based on the webpage context. The {heading_type} is : {text} and the webpage contnt is : {page_text}.

                Input Parameters:
                - heading_type: The type of heading to optimize (title, h1-1, h2-1, or h2-2)
                - webpage_text: The full webpage content for context
                - original_heading: The current heading to optimize

                Constraints:
                - Generate exactly 3-5 variations
                - Title: 50-60 characters
                - H1: 20-70 characters
                - H2: 20-65 characters
                - Include primary keyword naturally
                - Maintain proper capitalization
                - Front-load important keywords when possible

                Instructions:
                1. Analyze webpage content for context and keywords
                2. Create compelling variations that maintain original intent
                3. Ensure proper character length for heading type
                4. Incorporate emotional triggers when appropriate
                5. Use power words that drive engagement
                6. Include numbers/years if relevant
                7. Maintain natural language flow

                Positive elements to include:
                - Action words
                - Specific numbers or quantities
                - Current year if relevant
                - Benefit-driven language
                - Product/service qualifiers
                - Solution-oriented phrasing

                Elements to avoid:
                - Clickbait language
                - Excessive punctuation
                - Keyword stuffing
                - Generic phrases
                - Redundant words
                - Misleading terms

                Output format:
                Strictly comma-separated list of variations, no additional text or formatting
                

                Sample input:
                heading_type: "title or heading"
                webpage_text: "Comprehensive guide about ergonomic office chairs, featuring reviews, buying tips, and recommendations for back pain relief..."
                original_heading: "Office Chairs Guide"

                Sample output:
                  [
                    "heading1",
                    "heading2",
                    "heading3",
                    "heading4",
                    "heading5",
                    "heading6",
                    "heading7"
                  ]

                Important: Return ONLY the comma-separated list of variations with no additional explanation or formatting."""

    return PROMPT


loaded_index = faiss.read_index("faiss_TF_index.bin")
print(loaded_index)


def normalize_embeddings(embeddings):
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    return embeddings / norms


def match_keyword(keyword, threshold=0.65):
    # Convert keyword to embedding and normalize it
    embedding = np.array(get_embedding(keyword)).astype("float32")
    normalized_embedding = normalize_embeddings(embedding.reshape(1, -1))

    # Perform the search in the FAISS index
    distances, _ = loaded_index.search(normalized_embedding, k=1)

    # Convert L2 distance to cosine similarity
    l2_distance = distances[0][0]
    similarity = 1 - (l2_distance / 2)

    print(
        f"Keyword: {keyword}, Cosine similarity: {similarity}, Threshold: {threshold}"
    )

    # Return 1 if similarity meets the threshold, otherwise return None
    return 1 if similarity >= threshold else None


def update_priority(row):
    match = match_keyword(row["keyword"])

    if match is not None:  # Only update if a match above threshold is found
        print(f"Updating priority for keyword: {row['keyword']}")
        return 1  # Set priority to 1 if match meets threshold
    print(f"Retaining original priority for keyword: {row['keyword']}")
    return row["priority"]  # Return existing priority if no match is found


def process_priority(row):
    # Process each row, calling update_priority for each row
    return update_priority(row)


def process_row_for_outlines(row_data_for_outlines):
    # row_data = request.json
    row_data = row_data_for_outlines
    url_slug = row_data_for_outlines.get("url_slug")
    reference_keywords_obj = {
        "origin_url": row_data["origin_url"],
        "url_slug": row_data["url_slug"],
        "h1-1": {"keywords": [], "priority": 1},
        "title_tag": {"keywords": [], "priority": 2},
        "meta_desc": {"keywords": [], "priority": 3},
        "page_text": {"keywords": [], "priority": 4},
        "h2_1": {"keywords": [], "priority": 2},
        "h2_2": {"keywords": [], "priority": 2},
    }

    if row_data["title"] is not None:
        reference_keywords_obj["title_tag"]["keywords"] = list(
            set(row_data["title"].split("|"))
        )
        reference_keywords_obj["title_tag_text"] = row_data["title"]
    reference_keywords_obj["h1-1_text"] = row_data["h1-1"]
    reference_keywords_obj["h2-1_text"] = row_data["H2-1"]
    reference_keywords_obj["h2-2_text"] = row_data["H2-2"]
    reference_keywords_obj["page_text_txt"] = row_data["page_text"]

    processed_data = extract_keywords_row_level(row_data, reference_keywords_obj)
    print("********Processed_data:*********", processed_data)
    priority_order = {
        "h1-1": 1,
        "title_tag": 2,
        "h2_2": 3,
        "h2_1": 5,
        "page_text": 5,
        "meta_desc": 4,
    }
    flattened_data = []
    for tag_type, data in processed_data.items():
        if isinstance(data, dict) and "keywords" in data:
            for keyword in set(data["keywords"]):
                flattened_data.append(
                    {
                        "keyword": keyword,
                        "origin_url": processed_data["origin_url"],
                        "title_tag_text": processed_data["title_tag_text"],
                        "h1-1_text": processed_data["h1-1_text"],
                        "h2-1_text": processed_data["h2-1_text"],
                        "h2-2_text": processed_data["h2-2_text"],
                        "page_text_txt": processed_data["page_text_txt"],
                        "url_slug": processed_data["url_slug"],
                        "tag_type": tag_type,
                        "priority": data["priority"],
                        "is_synonym": 0,
                        "parent_keyword": "parent itself",
                    }
                )

    df_flattened = pd.DataFrame(flattened_data)
    df_flattened["keyword"] = df_flattened["keyword"].str.strip().str.lower()
    df_flattened["keyword"] = df_flattened["keyword"].str.normalize("NFKC")
    df_flattened["count"] = df_flattened.groupby("keyword")["keyword"].transform("size")

    df_flattened = df_flattened.sort_values(
        by=["keyword", "tag_type"], ascending=[True, False]
    )
    df_flattened = df_flattened.drop_duplicates(subset="keyword", keep="first")
    df_flattened["count"] = df_flattened["count"].astype(str)
    df_flattened["tag_priority"] = df_flattened["tag_type"].map(priority_order)

    # Drop duplicates while keeping the first occurrence (which will be 'h1' if available)
    df_flattened = df_flattened.drop(columns=["tag_priority"])

    with concurrent.futures.ThreadPoolExecutor() as executor:
        priority_results = list(
            executor.map(process_priority, df_flattened.to_dict("records"))
        )
    print("priority_results:", priority_results)
    df_flattened["priority"] = priority_results
    return df_flattened
