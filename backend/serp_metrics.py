import requests
from typing import Dict, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")


class SerpAPI:
    def __init__(self):
        self.api_token = API_TOKEN
        self.base_url = "https://api.ahrefs.com/v3"
        self.headers = {
            "Accept": "application/json, application/xml",
            "Authorization": f"Bearer {self.api_token}",
        }

    def get_serp_data(self, keyword: str, country: str = "us") -> Optional[Dict]:
        """Get SERP overview data for a keyword"""
        url = f"{self.base_url}/serp-overview/serp-overview"

        querystring = {
            "select": "backlinks,position,type,url,url_rating,top_keyword_volume",
            "country": country,
            "keyword": keyword,
            "output": "json",
        }

        try:
            response = requests.get(url, headers=self.headers, params=querystring)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching SERP data for {keyword}: {e}")
            return None


def process_serp_data(serp_data: Dict, keyword: str, target_url: str = None) -> tuple:
    """
    Process SERP data to extract both keyword metrics and competitor rankings
    Returns: (keyword_metrics, competitor_rankings)
    """
    if not serp_data:
        return None, None

    # Initialize data structures
    keyword_metrics = {
        "keyword": keyword,
        "search_volume": 0,
        "position": 0,
        "cpc": 0,
        "difficulty": 0,
        "serp_feature": [],
    }

    competitor_data = {
        "keyword": keyword,
        "target_url": target_url,
        "target_rank": "NA",
        "tf_url": "NA",
        "tf_rank": "NA",
    }

    competitors = []

    # Process positions
    for position in serp_data.get("positions", []):
        url = position.get("url", "")
        current_position = position.get("position", 0)

        # Handle TF metrics
        if url and "thermofisher" in url.lower():
            keyword_metrics["search_volume"] = position.get("top_keyword_volume", 0)
            keyword_metrics["position"] = current_position
            keyword_metrics["serp_feature"] = position.get("type", [])

            competitor_data["tf_url"] = url
            competitor_data["tf_rank"] = current_position

        # Handle target URL metrics
        if target_url and url == target_url:
            competitor_data["target_rank"] = current_position

        # Collect competitor data (non-TF URLs)
        if len(competitors) < 3 and url and "thermofisher" not in url.lower() and current_position not in [c["competitor_rank"] for c in competitors]:
            competitors.append(
                {"competitor_url": url, "competitor_rank": current_position}
            )

    # Add competitor data to the result
    for i, competitor in enumerate(competitors, 1):
        domain_url = competitor["competitor_url"].replace("https://","").replace("http://","").split("/")[0]
        if domain_url not in str(competitor_data):
            competitor_data[f"competitor{i}_url"] = competitor["competitor_url"]
            competitor_data[f"competitor{i}_rank"] = competitor["competitor_rank"]

    return keyword_metrics, [competitor_data]


def get_difficulty_metrics(df):
    """Get difficulty metrics for multiple keywords in bulk"""
    url = "https://api.ahrefs.com/v3/keywords-explorer/overview"
    keywords = df.keyword.to_list()

    querystring = {
        "select": "keyword,difficulty,cpc",
        "country": "us",
        "keywords": ",".join(keywords),
    }

    headers = {
        "Accept": "application/json, application/xml",
        "Authorization": f"Bearer {API_TOKEN}",
    }

    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching difficulty metrics: {e}")
        return {"keywords": []}


def get_metrics_and_ranking(keyword: str, target_url: str = None):
    """
    Combined function to get both keyword metrics and competitor rankings
    """
    api = SerpAPI()
    serp_data = api.get_serp_data(keyword)

    if not serp_data:
        return None, None

    return process_serp_data(serp_data, keyword, target_url)
