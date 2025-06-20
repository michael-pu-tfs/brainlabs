from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from starlette.middleware.cors import CORSMiddleware
import secrets
import json
from google.cloud import bigquery
from google.oauth2 import service_account
from openai import OpenAI
import json
import time
import re
import re
import pandas as pd
import numpy as np
import ast
from sklearn.metrics.pairwise import cosine_similarity
import logging
import os
import faiss
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import random
from clustering import cluster_existing_embeddings, analyze_clusters
from topic_generation import process_row_parallel, extract_topic_subtopic
from database import get_db_cursor
from prompts import system_message, generate_prompt, generate_synonym_prompt
import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# JWT and Security Configuration
SECRET_KEY = secrets.token_urlsafe(32)  # Generate a secure random key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
GOOGLE_CLIENT_ID = "your-google-client-id"

total_tokens_used = 0
MAX_TOKEN_LIMIT = 1000
project_id = "thermofigher-gen-ai"
dataset_id = "research_data"
scraped_table_name = "biopharma_data"
synonym_keywords_table_name = "research_keywords"
aggregated_syn_table_name = "aggregated_research_keywords"
agg_syn_outlines_table_name = "aggregated_research_outline_keywords"
optimize_content_table = "optimize_content"
extract_optimization_metrics_table_name = "extract_optimization_metrics"
outline_table = "research_outline"
# service_account_key_path = "thermofigher-gen-ai-5255b69aa6e4.json"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

security = HTTPBearer()
client = OpenAI(api_key=OPENAI_API_KEY)

credentials = service_account.Credentials.from_service_account_file(
    service_account_key_path
)
bq_client = bigquery.Client(credentials=credentials, project=project_id)

# Cookie configurations
COOKIE_NAME = "session_token"
COOKIE_MAX_AGE = 1800  # 30 minutes in seconds


# Function to read unprocessed rows from BigQuery (runs in a thread pool)
def read_unprocessed_rows(url):
    query = """
    SELECT *
    FROM `thermofigher-gen-ai.pdp_data.scraped_data_v2`
    WHERE origin_url = @url
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("url", "STRING", url)]
    )
    query_job = bq_client.query(query, job_config=job_config)
    results = query_job.result()

    return results.to_dataframe()


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


def analyze_intent(keyword, retries=3):
    test_messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": keyword},
    ]
    client = OpenAI(api_key=OPENAI_API_KEY)
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="ft:gpt-4o-mini-2024-07-18:brainlabs:tf-intent-classifier:AH9Zsveq",
                # model="gpt-4o",
                messages=test_messages,
                max_tokens=MAX_TOKEN_LIMIT,
                temperature=0,
            )
            return response.choices[0].message.content

        except Exception as e:
            time.sleep(1)  # Wait for a second before retrying
            if attempt == retries - 1:
                return None  # Return None if all attempts fail


# Function to apply intent analysis concurrently
def apply_intent_analysis(df):
    # Create a new column for the analyzed intent
    df["analysed_intent"] = None

    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit tasks to the executor for concurrent processing
        future_to_keyword = {
            executor.submit(analyze_intent, row["keyword"]): idx
            for idx, row in df.iterrows()
        }

        # Retrieve results and store them in the new column
        for future in concurrent.futures.as_completed(future_to_keyword):
            idx = future_to_keyword[future]
            try:
                result = future.result()
                df.at[idx, "analysed_intent"] = result
            except Exception as exc:
                print(f"Keyword analysis generated an exception for index {idx}: {exc}")

    return df


def run_openai_api(text, reference_keywords, page_text=None):
    client = OpenAI(api_key=OPENAI_API_KEY)
    PROMPT = generate_prompt(text, reference_keywords, page_text)
    response = client.chat.completions.create(
        model="gpt-4o-2024-05-13",
        # model="gpt-4o",
        messages=[{"role": "user", "content": PROMPT}],
        max_tokens=MAX_TOKEN_LIMIT,
        temperature=0,
    )
    obj = json.loads(response.json())
    inside_top_performing_kw = obj["choices"][0]["message"]["content"]
    tokens_used = obj["usage"]["total_tokens"]
    global total_tokens_used
    total_tokens_used = total_tokens_used + int(tokens_used)
    try:
        result = ast.literal_eval(inside_top_performing_kw)
        return result
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding response: {e}")
        return None


def extract_keywords_row_level(row, reference_keywords_obj, distinct_keywords):
    meta_desc = row.get("meta_desc")
    page_text = row.get("page_text")  # Use cleaned body text
    h1_1 = row.get("h1-1")
    h2_1 = row.get("H2-1")
    h2_2 = row.get("H2-2")

    if meta_desc:
        reference_keywords_obj["meta_desc"]["keywords"] = standardize_data(
            run_openai_api(meta_desc, distinct_keywords, page_text)
        )
    # if page_text:
    #     reference_keywords_obj['page_text']['keywords'] = standardize_data(run_openai_api(page_text, distinct_keywords,page_text))
    if h1_1:
        reference_keywords_obj["h1-1"]["keywords"] = standardize_data(
            run_openai_api(h1_1, distinct_keywords, page_text)
        )
    if h2_1:
        reference_keywords_obj["h2_1"]["keywords"] = standardize_data(
            run_openai_api(h2_1, distinct_keywords, page_text)
        )
    if h2_2:
        reference_keywords_obj["h2_2"]["keywords"] = standardize_data(
            run_openai_api(h2_2, distinct_keywords, page_text)
        )
    return reference_keywords_obj


def extract_synonyms_from_openai(reference_keyword, pg_txt):
    client = OpenAI(api_key=OPENAI_API_KEY)
    PROMPT = generate_synonym_prompt(reference_keyword, pg_txt)
    response = client.chat.completions.create(
        model="gpt-4o-2024-05-13",
        # model="gpt-4o",
        messages=[{"role": "user", "content": PROMPT}],
        max_tokens=MAX_TOKEN_LIMIT,
        temperature=0,
    )
    obj = json.loads(response.json())
    synonyms = obj["choices"][0]["message"]["content"]
    tokens_used = obj["usage"]["total_tokens"]

    global total_tokens_used
    total_tokens_used = total_tokens_used + int(tokens_used)
    try:
        if synonyms.strip().startswith("{") or synonyms.strip().startswith("["):
            result = json.loads(synonyms)
            result = pd.DataFrame(result, columns=["keyword"])
        else:
            # Otherwise, try using literal_eval
            result = ast.literal_eval(synonyms)
            result = pd.DataFrame(result, columns=["keyword"])
        return result
    except json.JSONDecodeError as e:
        print("Error decoding JSON:", e)
        return None


def process_keywords_and_tag_types_concurrently(df):
    # Convert keywords to lowercase
    df["keyword"] = df["keyword"].str.lower()

    # Compile regex pattern for trigger words
    trigger_words = [
        "vs",
        "top",
        "best",
        "how",
        "reviews",
        "review",
        "rating",
        "what",
        "which",
        "where",
        "when",
    ]
    pattern = re.compile(r"\b(?:" + "|".join(trigger_words) + r")\b")

    # Define the concurrent update function
    def update_tag_type(keyword, tag_type):
        if pattern.search(keyword):
            return tag_type + "-PAA"
        return tag_type

    # Use available CPU cores for parallel processing
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        # Map the function to each row, concurrently
        tag_type_futures = {
            executor.submit(update_tag_type, keyword, tag_type): index
            for index, (keyword, tag_type) in enumerate(
                zip(df["keyword"], df["tag_type"])
            )
        }

        # Retrieve results as the futures complete
        for future in tag_type_futures.keys():
            index = tag_type_futures[future]
            df.at[index, "tag_type"] = future.result()

    return df


def filter_keywords(df):
    # Condition for similarity score greater than 50
    condition_score = df["similarity_score"] > 50

    # Condition for tag_type ending with -PAA
    condition_tag_type = df["tag_type"].str.endswith("-PAA")
    condition_priority = df["priority"] == 1
    # Combined condition: either similarity score is high or tag_type ends with -PAA
    mask = condition_score | condition_tag_type | condition_priority

    # Apply the mask to filter the DataFrame
    filtered_df = df[mask]
    return filtered_df


def process_embedding(row):
    # Get embeddings for keyword, h1_text, and title_tag
    row["keyword_embedding"] = get_embedding_if_valid(row["keyword"])
    row["h1_text_embedding"] = get_embedding_if_valid(row["h1-1_text"])
    row["title_tag_embedding"] = get_embedding_if_valid(row["title_tag_text"])

    # Combine title_tag_text and h1_text wisely
    row["combined_text"] = (
        (row["title_tag_text"] + " " + row["h1-1_text"]).strip()
        if pd.notna(row["title_tag_text"]) and pd.notna(row["h1-1_text"])
        else (
            row["title_tag_text"]
            if pd.notna(row["title_tag_text"])
            else row["h1-1_text"]
        )
    )

    # Get embedding for combined text
    row["combined_embedding"] = get_embedding_if_valid(row["combined_text"])

    # Calculate similarity score
    row["similarity_score"] = calculate_similarity(row)

    return row


# def compute_embeddings(df):
def extract_synonyms_concurrently(row):
    # Each row performs synonym extraction
    df_synonyms = extract_synonyms_from_openai(row["keyword"], row["page_text_txt"])

    if not df_synonyms.empty:
        df_synonyms["is_synonym"] = 1
        df_synonyms["origin_url"] = row["origin_url"]
        df_synonyms["title_tag_text"] = row["title_tag_text"]
        df_synonyms["h1-1_text"] = row["h1-1_text"]
        df_synonyms["h2-1_text"] = row["h2-1_text"]
        df_synonyms["h2-2_text"] = row["h2-2_text"]
        df_synonyms["page_text_txt"] = row["page_text_txt"]
        df_synonyms["url_slug"] = row["url_slug"]
        df_synonyms["tag_type"] = row["tag_type"]
        df_synonyms["priority"] = row["priority"]
        df_synonyms["parent_keyword"] = row["keyword"]
        df_synonyms["count"] = row["count"]

        return df_synonyms.to_dict("records")

    return []


def process_synonym_extraction(df_flattened):
    processed_rows = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        # Process each row concurrently
        results = list(
            executor.map(extract_synonyms_concurrently, df_flattened.to_dict("records"))
        )

        for result in results:
            processed_rows.extend(result)

    return pd.DataFrame(processed_rows)


def compute_embeddings(df):
    max_workers = min(
        os.cpu_count(), len(df)
    )  # Limit workers to either CPU cores or number of rows

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Parallel execution for embedding generation (keyword embeddings generated per row)
        futures = {
            "keyword": {
                executor.submit(get_embedding_if_valid, keyword): idx
                for idx, keyword in enumerate(df["keyword"])
            }
        }

        # Compute h1 and title embeddings once (since they are the same for all rows)
        h1_text = (
            df["h1-1_text"].iloc[0] if not df["h1-1_text"].isnull().all() else None
        )
        title_text = (
            df["title_tag_text"].iloc[0]
            if not df["title_tag_text"].isnull().all()
            else None
        )

        h1_text_embedding = get_embedding_if_valid(h1_text) if h1_text else None
        title_tag_embedding = get_embedding_if_valid(title_text) if title_text else None

        # Assign embeddings for keyword and reuse for h1 and title
        df["keyword_embedding"] = [None] * len(df)
        df["h1_text_embedding"] = [h1_text_embedding] * len(df)
        df["title_tag_embedding"] = [title_tag_embedding] * len(df)

        for future, idx in futures["keyword"].items():
            df.at[idx, "keyword_embedding"] = future.result()

    # Combine text
    df["combined_text"] = df.apply(
        lambda row: (
            (row["title_tag_text"] + " " + row["h1-1_text"]).strip()
            if pd.notna(row["title_tag_text"]) and pd.notna(row["h1-1_text"])
            else (
                row["title_tag_text"]
                if pd.notna(row["title_tag_text"])
                else row["h1-1_text"]
            )
        ),
        axis=1,
    )

    # Embedding for combined text (only once as it is the same across rows)
    combined_text = (
        df["combined_text"].iloc[0] if not df["combined_text"].isnull().all() else None
    )
    combined_embedding = (
        get_embedding_if_valid(combined_text) if combined_text else None
    )
    df["combined_embedding"] = [combined_embedding] * len(df)

    # Calculate similarity score in vectorized manner
    df["similarity_score"] = df.apply(calculate_similarity, axis=1)

    # Cleanup,keyword_embedding
    df.drop(
        columns=[
            "h1_text_embedding",
            "title_tag_embedding",
            "combined_embedding",
            "combined_text",
        ],
        inplace=True,
    )
    df["similarity_score"] = (df["similarity_score"] * 100).round(2)

    return df


loaded_index = faiss.read_index("faiss_TF_index.bin")


def clustering(embedding_data):
    try:
        # Convert the loaded data into a pandas DataFrame
        df = pd.DataFrame(embedding_data)

        # Ensure the embedding column exists
        if "embedding" not in df.columns:
            raise ValueError("No 'embedding' column found in the data")

        # Perform clustering
        df_clustered = cluster_existing_embeddings(
            df=df, keyword_col="keyword", embedding_col="embedding", min_similarity=0.85
        )

        # Analyze results
        analysis = analyze_clusters(df_clustered)

        ##topic generation
        keywords_list = [",".join(i) for i in analysis["keywords"].tolist()]

        analysis["response"] = process_row_parallel(keywords_list)

        analysis[["Topic", "Subtopic"]] = analysis["response"].apply(
            lambda x: pd.Series(extract_topic_subtopic(x))
        )
        topic, subtopic = [], []
        for i, row in df_clustered.iterrows():
            df = analysis[analysis["cluster_id"] == row.cluster_id]
            topic.append(df.iloc[0].Topic)
            subtopic.append(df.iloc[0].Subtopic)
        df_clustered["topic"], df_clustered["subtopic"] = topic, subtopic
        df_clustered = df_clustered[["keyword", "topic", "subtopic", "cluster_id"]]
        return df_clustered.to_dict()
    except Exception as e:
        print(f"Error in main execution: {str(e)}")
        raise


def normalize_embeddings(embeddings):
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    return embeddings / norms


def match_keyword(keyword, threshold=0.85):
    # Convert keyword to embedding and normalize it
    embedding = np.array(get_embedding(keyword)).astype("float32")
    normalized_embedding = normalize_embeddings(embedding.reshape(1, -1))

    # Perform the search in the FAISS index
    distances, _ = loaded_index.search(normalized_embedding, k=1)

    # Convert L2 distance to cosine similarity
    l2_distance = distances[0][0]
    similarity = 1 - (l2_distance / 2)
    # Return 1 if similarity meets the threshold, otherwise return None
    return 1 if similarity >= threshold else None


def update_priority(row):
    match = match_keyword(row["keyword"])

    if match is not None:  # Only update if a match above threshold is found
        return 1  # Set priority to 1 if match meets threshold
    return row["priority"]  # Return existing priority if no match is found


def process_priority(row):
    # Process each row, calling update_priority for each row
    return update_priority(row)


def get_user_by_email(email: str):
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        return cursor.fetchone()


def create_user(
    email: str,
    password: Optional[str] = None,
    name: Optional[str] = None,
    is_google_account: bool = False,
):
    hashed_password = pwd_context.hash(password) if password else None
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO users (email, name, hashed_password, is_google_account)
            VALUES (?, ?, ?, ?)
        """,
            (email, name, hashed_password, 1 if is_google_account else 0),
        )

        # SQLite doesn't support RETURNING clause directly, so we need to get the last inserted row
        cursor.execute("SELECT * FROM users WHERE id = last_insert_rowid()")
        return cursor.fetchone()


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(email: str, password: str):
    user = get_user_by_email(email)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
