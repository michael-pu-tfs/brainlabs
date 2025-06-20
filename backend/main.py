from fastapi import FastAPI, HTTPException, Depends, Response, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPBearer
from google.oauth2 import id_token
from google.auth.transport import requests
from pydantic import BaseModel, EmailStr, constr
from jwt import InvalidTokenError
from typing import Optional, List, Union, Dict
from tf_outline_creation import process_row_for_outlines
from content_creation_tf import optimize_content, extract_optimization_metrics
from final_content import final_optimize_content
from serp_metrics import get_metrics_and_ranking, get_difficulty_metrics
from scraper import scrape_url
from database import  init_db, test_db_connection
from utility import *

app = FastAPI()


# Update CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tfgenai-650699698990.us-central1.run.app",
        "http://0.0.0.0:8080",
        "http://localhost:5173",
        "http://127.0.0.1:8080",
        "http://localhost:8080",
        "https://tf-gen-ai-937478371170.us-central1.run.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_headers(request, call_next):
    response = await call_next(request)
    response.headers["Referrer-Policy"] = "no-referrer-when-downgrade"
    return response

# API Endpoints
@app.post("/api/auth/login")
async def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": user["email"]})

    response.set_cookie(
        key=COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
    )

    return {
        "message": "Login successful",
        "name": user["name"],  # Include user's name in response
    }


# @app.options("/api/auth/register")
# async def register_options():
#     return {}  # Return empty response for OPTIONS request


class UserCreate(BaseModel):
    email: EmailStr
    password: constr(min_length=8)  # Ensure password is at least 8 characters
    name: Optional[str] = None


@app.post("/api/auth/register")
async def register(user: UserCreate):
    existing_user = get_user_by_email(user.email)
    if existing_user:
        if existing_user["is_google_account"]:
            raise HTTPException(
                status_code=400, detail="Email already registered with Google account"
            )
        else:
            raise HTTPException(status_code=400, detail="Email already registered")

    # Add password complexity validation
    if len(user.password) < 12:
        raise HTTPException(
            status_code=400, detail="Password must be at least 12 characters long"
        )

    if (
        not any(c.isupper() for c in user.password)
        or not any(c.islower() for c in user.password)
        or not any(c.isdigit() for c in user.password)
        or not any(c in "!@#$%^&*" for c in user.password)
    ):
        raise HTTPException(
            status_code=400,
            detail="Password must contain uppercase, lowercase, number, and special character",
        )

    # Create user with hashed password
    new_user = create_user(email=user.email, password=user.password, name=user.name)

    # Don't return sensitive information
    return {"message": "Registration successful", "email": new_user["email"]}


@app.post("/api/auth/google")
async def google_login(token: str):
    try:
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), GOOGLE_CLIENT_ID
        )
        email = idinfo["email"]

        user = get_user_by_email(email)
        if not user:
            user = create_user(
                email=email, name=idinfo.get("name"), is_google_account=True
            )

        access_token = create_access_token(data={"sub": email})
        return {"access_token": access_token, "token_type": "bearer"}

    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")


# Add new endpoint for Google registration
@app.post("/api/auth/register/google")
async def register_with_google(token: str):
    try:
        # Verify the Google token
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), GOOGLE_CLIENT_ID
        )

        email = idinfo["email"]
        name = idinfo.get("name", "")

        # Check if user already exists
        existing_user = get_user_by_email(email)
        if existing_user:
            if existing_user["is_google_account"]:
                # If user exists and is a Google account, just return success
                return {
                    "email": email,
                    "name": name,
                    "id": existing_user["id"],
                    "message": "Account already exists",
                }
            else:
                # If user exists but is not a Google account, return error
                raise HTTPException(
                    status_code=400, detail="Email already registered with password"
                )

        # Create new user with Google account
        new_user = create_user(email=email, name=name, is_google_account=True)

        return {
            "email": new_user["email"],
            "name": new_user["name"],
            "id": new_user["id"],
            "message": "Registration successful",
        }

    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")
    except Exception as e:
        print(f"Google registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")


@app.post("/api/auth/logout")
async def logout(response: Response):
    response.delete_cookie(key=COOKIE_NAME, httponly=True, secure=True, samesite="lax")
    return {"message": "Logout successful"}


@app.get("/api/auth/verify")
async def verify_auth(session_token: str = Cookie(None)):
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # Verify the JWT token
        payload = jwt.decode(session_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication token")

        # Check if user exists
        user = get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return {"status": "authenticated", "email": email}

    except InvalidTokenError:
        raise HTTPException(
            status_code=401, detail="Invalid authentication credentials"
        )


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    try:
        init_db()
        if test_db_connection():
            print("Application started successfully with database connection")
        else:
            print("Application started but database connection failed")
    except Exception as e:
        print(f"Startup error: {str(e)}")


class KeywordData(BaseModel):
    keyword: str
    searchVolume: int
    difficulty: int
    # Add other fields as needed


@app.get("/api/keywords")
async def get_keywords(category: str, url: str) -> List[KeywordData]:
    try:
        # Add your logic to fetch keyword data based on category and URL
        # This is just an example response
        data = [
            {
                "keyword": "example keyword",
                "searchVolume": 1000,
                "difficulty": 45,
                # Add other fields
            }
        ]
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class UrlRequest(BaseModel):
    url: str


class KeywordMetric(BaseModel):
    cpc: Optional[float]
    difficulty: Optional[int]
    intent_classification: str
    keyword: str
    position: int
    search_volume: int
    serp_feature: List[str]
    tf_url: str


class TopicCluster(BaseModel):
    cluster_id: Dict[str, int]
    keyword: Dict[str, str]
    subtopic: Dict[str, str]
    topic: Dict[str, str]


class ContentSummary(BaseModel):
    count: str
    is_synonym: str
    outline: str
    parent_keyword: str
    priority: str
    tag_type: str
    tf_url: str
    url_slug: str


class CompetitorRanking(BaseModel):
    keyword: str
    target_url: str
    target_rank: Union[int, str]
    competitor1_url: str
    competitor1_rank: int
    competitor2_url: str
    competitor2_rank: int
    competitor3_url: str
    competitor3_rank: int
    tf_url: str
    tf_rank: Union[int, str]


class ModifiedContentMetrics(BaseModel):
    url_slug: Dict[str, str]
    content_length_original: Dict[str, str]
    content_length_modified: Dict[str, str]
    keyword_count_original: Dict[str, str]
    keyword_count_modified: Dict[str, str]
    keyword_density_original: Dict[str, str]
    keyword_density_modified: Dict[str, str]
    keywords_incorporated: Dict[str, str]
    outline_count_original: Dict[str, str]
    outline_count_modified: Dict[str, str]
    outlines_incorporated: Dict[str, str]


class ProcessRowResponse(BaseModel):
    keyword_metrics: List[KeywordMetric]
    topic_ai_cluster: TopicCluster
    content_summary: List[ContentSummary]
    competitor_ranking: List[CompetitorRanking]
    modified_content: List[Union[str, int]]
    modified_content_metrics: ModifiedContentMetrics


@app.post("/process_row")
async def process_row(request: UrlRequest) -> ProcessRowResponse:
    url = request.url
    url_data = await scrape_url(url)
    row_data = url_data.to_json(orient="records")
    row_data = json.loads(row_data)
    row_data = row_data[0]
    row_data_for_outlines = row_data.copy()

    url_slug = row_data.get("url_slug")

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

    # distinct_keywords = reference_keywords_obj['h1']['keywords'] + reference_keywords_obj['h2']['keywords'] + reference_keywords_obj['title_tag']['keywords']
    distinct_keywords = reference_keywords_obj["title_tag"]["keywords"]
    logging.debug(f"Distinct keywords received: {distinct_keywords}")
    processed_data = extract_keywords_row_level(
        row_data, reference_keywords_obj, distinct_keywords
    )
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
    df_synonyms = process_synonym_extraction(df_flattened)

    processed_rows = []
    df_synonyms["keyword"] = df_synonyms["keyword"].str.strip().str.lower()
    df_synonyms["keyword"] = df_synonyms["keyword"].str.normalize("NFKC")
    df_synonyms["count"] = df_synonyms.groupby("keyword")["keyword"].transform("size")
    df_synonyms["tag_priority"] = df_synonyms["tag_type"].map(priority_order)
    df_synonyms = df_synonyms.sort_values(by=["keyword", "tag_priority"])
    df_synonyms = df_synonyms.drop_duplicates(subset="keyword", keep="first")
    df_synonyms["count"] = df_synonyms["count"].astype(str)
    df_synonyms = df_synonyms.drop(columns=["tag_priority"])
    df_synonyms = pd.concat(
        [df_flattened, df_synonyms.drop_duplicates(subset="keyword", keep="first")],
        ignore_index=True,
    )

    df_synonyms = compute_embeddings(df_synonyms)
    df_synonyms = process_keywords_and_tag_types_concurrently(df_synonyms)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        priority_results = list(
            executor.map(process_priority, df_synonyms.to_dict("records"))
        )
    df_synonyms["priority"] = priority_results
    df_synonyms = apply_intent_analysis(df_synonyms)
    df_synonyms_copy = df_synonyms.copy()
    df_synonyms_copy["priority"] = df_synonyms_copy["priority"].astype("int64")
    df_synonyms_copy["is_synonym"] = df_synonyms_copy["is_synonym"].astype("bool")
    df_synonyms_copy["count"] = df_synonyms_copy["count"].astype("int64")
    df_synonyms_copy["similarity_score"] = df_synonyms_copy["similarity_score"].astype(
        "float64"
    )
    df_synonyms_copy = df_synonyms_copy.rename(
        columns={
            "h1-1_text": "h1_1_text",
            "h2-1_text": "h2_1_text",
            "h2-2_text": "h2_2_text",
        }
    )  # final_synonym

    def process_row_v1(row):
        keyword_metrics, competitor_ranking = get_metrics_and_ranking(
            row.keyword, row.origin_url
        )
        if keyword_metrics:
            keyword_metrics["intent_classification"] = row.analysed_intent
            keyword_metrics["tf_url"] = row.origin_url
        return (keyword_metrics, competitor_ranking)

    def process_outline(row):
        keyword_metric = {}

        # keyword_metric['intent_classification'] = row.analysed_intent
        keyword_metric["outline"] = row.keyword
        keyword_metric["tf_url"] = row.origin_url
        keyword_metric["url_slug"] = row.url_slug
        keyword_metric["tag_type"] = row.tag_type
        keyword_metric["priority"] = row.priority
        keyword_metric["is_synonym"] = row.is_synonym
        keyword_metric["parent_keyword"] = row.parent_keyword
        keyword_metric["count"] = row["count"]

        return keyword_metric

    try:
        keyword_metrics = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(
                process_row_v1, [row for _, row in df_synonyms.iterrows()]
            )
        competitor_ranking, keyword_metrics = [], []
        for metrics, rankings in results:
            if metrics:
                if metrics["search_volume"] and metrics["search_volume"] > 0:
                    keyword_metrics.append(metrics)
            if rankings:
                competitor_ranking.extend(rankings)

        # Filter out any None or invalid entries
        competitor_ranking = [
            r
            for r in competitor_ranking
            if isinstance(r, dict)
            and all(
                isinstance(r.get(k), (str, int, float))
                for k in [
                    "target_url",
                    "competitor1_url",
                    "competitor1_rank",
                    "competitor2_url",
                    "competitor2_rank",
                    "competitor3_url",
                    "competitor3_rank",
                ]
            )
        ]

        difficulty = get_difficulty_metrics(df_synonyms)

        for i in keyword_metrics:
            for j in difficulty["keywords"]:
                if i["keyword"] == j["keyword"]:
                    i["difficulty"] = j["difficulty"]
                    i["cpc"] = j["cpc"]

        # Extracting keys from keyword_metric
        keys_to_filter = [item["keyword"] for item in keyword_metrics]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(get_embedding_if_valid, keys_to_filter))

        # Now results will correspond to    the same order of keys_to_filter
        embeddings_with_keys = list(zip(keys_to_filter, results))

        # Prepare a list of dictionaries to dump into JSON format
        embedding_data = [
            {"keyword": key, "embedding": embedding.tolist()}
            for key, embedding in embeddings_with_keys
        ]
        topic_ai_cluster = clustering(embedding_data)

        new_df = []
        for i, row in df_synonyms.iterrows():
            if row.keyword in keys_to_filter:
                new_df.append(row.to_dict())
        df_synonyms = pd.DataFrame(new_df)

        df_synonyms["aggregate_synonyms"] = df_synonyms.apply(
            lambda row: [row["keyword"], row["priority"], row["tag_type"]], axis=1
        )

        # # Group by 'url_slug' and create a new DataFrame with aggregated lists
        aggregated_syn_df = (
            df_synonyms.groupby("url_slug")
            .agg({"aggregate_synonyms": lambda x: list(x), "page_text_txt": "first"})
            .reset_index()
        )

        aggregated_syn_df_bigquery = (
            df_synonyms.groupby("url_slug")
            .agg(
                {
                    "keyword": lambda x: {
                        "aggregated_keyword": [
                            k
                            for k, t in zip(x, df_synonyms.loc[x.index, "tag_type"])
                            if not t.endswith("-PAA")
                        ],
                        "PAA_Keyword": [
                            k
                            for k, t in zip(x, df_synonyms.loc[x.index, "tag_type"])
                            if t.endswith("-PAA")
                        ],
                    },
                    "page_text_txt": "first",
                    "h1-1_text": "first",
                    "h2-1_text": "first",
                    "h2-2_text": "first",
                }
            )
            .reset_index()
        )

        # Split `keyword` column dictionary into two separate columns
        aggregated_syn_df_bigquery[["aggregated_keyword", "PAA_Keyword"]] = (
            pd.DataFrame(
                aggregated_syn_df_bigquery["keyword"].tolist(),
                index=aggregated_syn_df_bigquery.index,
            )
        )

        # Drop the original 'keyword' column as it has been split into two
        aggregated_syn_df_bigquery.drop(columns=["keyword"], inplace=True)

        aggregated_syn_df_bigquery = aggregated_syn_df_bigquery.rename(
            columns={"page_text_txt": "page_context"}
        )

        aggregated_syn_df_bigquery["aggregated_keyword"] = aggregated_syn_df_bigquery[
            "aggregated_keyword"
        ].astype("str")
        aggregated_syn_df_bigquery["PAA_Keyword"] = aggregated_syn_df_bigquery[
            "PAA_Keyword"
        ].astype("str")
    except Exception as e:
        logging.error(f"Error in similarity: {e}")
        print(f"Error in similarity score: {e}")

    outlines_df = process_row_for_outlines(row_data_for_outlines)
    outlines_df = outlines_df.astype(str)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(
            process_outline, [row for _, row in outlines_df.iterrows()]
        )

    content_summary_metrics = [result for result in results if result is not None]
    outlines_df["aggregate_outlines"] = outlines_df.apply(
        lambda row: [row["keyword"], row["priority"], row["tag_type"]], axis=1
    )

    # # Group by 'url_slug' and create a new DataFrame with aggregated lists
    aggregated_df = (
        outlines_df.groupby("url_slug")
        .agg({"aggregate_outlines": lambda x: list(x)})
        .reset_index()
    )

    if "aggregated_syn_df" not in locals() or aggregated_syn_df.empty:
        aggregated_syn_df = pd.DataFrame(columns=["url_slug"])
    agg_syn_outlines = pd.merge(
        aggregated_syn_df, aggregated_df, on="url_slug", how="inner"
    )

    #     # creating new df for aggregated syn outline df
    aggregated_outline_df_bigquery = (
        outlines_df.groupby("url_slug")
        .agg({"keyword": lambda x: list(x)})
        .reset_index()
    )
    try:

        aggregated_outline_syn_df_bigquery = pd.merge(
            aggregated_syn_df_bigquery,
            aggregated_outline_df_bigquery,
            on="url_slug",
            how="inner",
        )
        aggregated_outline_syn_df_bigquery = aggregated_outline_syn_df_bigquery.rename(
            columns={"keyword": "aggregate_outlines"}
        )
        aggregated_outline_syn_df_bigquery["aggregate_outlines"] = (
            aggregated_outline_syn_df_bigquery["aggregate_outlines"].astype("str")
        )
    except Exception as e:
        logging.error(f"Error in aggregated_outline_syn_df_bigquery: {e}")

    optimize_content_df = optimize_content(agg_syn_outlines)
    final_content_df = final_optimize_content(optimize_content_df)
    extract_optimization_metrics_df = extract_optimization_metrics(optimize_content_df)
    extract_optimization_metrics_df.to_csv("optimize_content_df.csv")
    extract_optimization_metrics_df = extract_optimization_metrics_df.dropna(how="any")
    extract_optimization_metrics_df.dropna(inplace=True)
    extract_optimization_metrics_df = extract_optimization_metrics_df.astype(str)

    extract_optimization_metrics_df.dropna(inplace=True)
    extract_optimization_metrics_df["keywords_incorporated"] = (
        extract_optimization_metrics_df["keywords_incorporated"].apply(
            lambda x: x.strip("[]")
        )
    )
    extract_optimization_metrics_df["outlines_incorporated"] = (
        extract_optimization_metrics_df["outlines_incorporated"].apply(
            lambda x: x.strip("[]")
        )
    )

    def convert_numeric_keys_to_strings(data):
        if isinstance(data, dict):
            return {str(k): convert_numeric_keys_to_strings(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [convert_numeric_keys_to_strings(item) for item in data]
        return data

    # Before returning the response, convert the keys
    output = {
        "keyword_metrics": keyword_metrics,
        "topic_ai_cluster": convert_numeric_keys_to_strings(topic_ai_cluster),
        "content_summary": content_summary_metrics,
        "modified_content": final_content_df["modified_content_v1"][0],
        "modified_content_metrics": convert_numeric_keys_to_strings(
            extract_optimization_metrics_df.to_dict()
        ),
        "competitor_ranking": competitor_ranking,
    }

    return ProcessRowResponse(
        keyword_metrics=output["keyword_metrics"],
        topic_ai_cluster=output["topic_ai_cluster"],
        content_summary=output["content_summary"],
        competitor_ranking=output["competitor_ranking"],
        modified_content=output["modified_content"],
        modified_content_metrics=output["modified_content_metrics"],
    )
