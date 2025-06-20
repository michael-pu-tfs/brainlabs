import pandas as pd
from ast import literal_eval
import logging
from openai import OpenAI
import re
from bs4 import BeautifulSoup
import pandas as pd
import ast
import re
import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
total_tokens_used = 0


def validate_and_fix_html(content: str) -> str:
    """
    Validates and fixes HTML content, ensuring proper heading structure.

    Args:
        content: String containing HTML content
    Returns:
        Properly formatted HTML string
    """
    # Clean up potential markdown headings
    content = re.sub(r"^#{1,6}\s", "", content, flags=re.MULTILINE)

    # Ensure proper HTML heading tags
    heading_patterns = [
        (r"(?i)title:\s*(.*?)(?=\n|$)", r"<h1>\1</h1>"),
        (r"(?i)heading 1:\s*(.*?)(?=\n|$)", r"<h1>\1</h1>"),
        (r"(?i)heading 2:\s*(.*?)(?=\n|$)", r"<h2>\1</h2>"),
        (r"(?i)h1:\s*(.*?)(?=\n|$)", r"<h1>\1</h1>"),
        (r"(?i)h2:\s*(.*?)(?=\n|$)", r"<h2>\1</h2>"),
        (r"(?i)h3:\s*(.*?)(?=\n|$)", r"<h3>\1</h3>"),
    ]

    for pattern, replacement in heading_patterns:
        content = re.sub(pattern, replacement, content)

    # Convert paragraphs
    paragraphs = content.split("\n\n")
    formatted_paragraphs = []
    for p in paragraphs:
        if p.strip() and not any(
            tag in p.lower() for tag in ["<h1", "<h2", "<h3", "<p"]
        ):
            formatted_paragraphs.append(f"<p>{p.strip()}</p>")
        else:
            formatted_paragraphs.append(p.strip())

    content = "\n".join(formatted_paragraphs)

    # Clean up any double HTML tags
    content = re.sub(r"<p>\s*<p>", "<p>", content)
    content = re.sub(r"</p>\s*</p>", "</p>", content)

    return content


def run_openai_api(keywords, content_structure, row):
    client = OpenAI(api_key=OPENAI_API_KEY)
    PROMPT = generate_prompt(keywords, content_structure, row)
    try:
        prompt = generate_prompt(keywords, content_structure, row)

        response = client.chat.completions.create(
            model="gpt-4.1",  # "gpt-4o-2024-05-13",  # Update this to your specific model
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert SEO content optimizer with deep knowledge of search engine optimization of contents/articles and content writing.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        optimized_content = response.choices[0].message.content.strip()

        tokens_used = response.usage.total_tokens

        logging.info(f"Tokens used for content optimization: {tokens_used}")

        # Validate and fix HTML formatting
        optimized_content = validate_and_fix_html(optimized_content)

        # Final validation
        soup = BeautifulSoup(optimized_content, "html.parser")
        headings = soup.find_all(["h1", "h2", "h3"])
        paragraphs = soup.find_all("p")

        if not headings:
            logging.warning(
                "No HTML headings found in response. Attempting to fix formatting..."
            )
            optimized_content = validate_and_fix_html(optimized_content)

        if not paragraphs:
            logging.warning(
                "No paragraph tags found in response. Attempting to fix formatting..."
            )
            optimized_content = validate_and_fix_html(optimized_content)

        return optimized_content, tokens_used

    except Exception as e:
        logging.error(f"Error in OpenAI API call: {str(e)}")
        return None, 0


def generate_prompt(keywords, content_structure, row):
    # Prepare prompt for GPT-4
    prompt = f"""
        Act as an expert SEO content optimizer with deep understanding of search intent and natural language processing. Your task is to optimize the following content while strictly maintaining the original HTML structure.
        ***IMPORTANT: ALL THE INPUT KEYWORDS AND OUTLINES ARE POTENTIAL ONE'S WITH SEARCH VOLUME THEREFORE INCLUDE THEM AS MUCH AS YOU CAN IN THE CONTENT***
        **ADD AS MANY KEYWORDS AND OUTLINES AS YOU CAN FROM THE INPUT DATA PROVIDED BELOW:**

        INPUT DATA:
        - Keywords: {keywords}  
        Format: [keyword, ranking_score, content_location]
        - Content Structure: {content_structure}
        Format: [outline, ranking_score, heading_type]
        - Original Content: {row['page_text_txt']}

        OPTIMIZATION REQUIREMENTS:

        1. HTML Structure Preservation
        - CRITICAL: Maintain the exact HTML tag structure from the original content
        - Do not add, remove, or modify any HTML tags
        - Only optimize the text content within existing tags
        - Keep all existing classes, IDs, and attributes unchanged

        2. Keyword Integration
        - Prioritize keywords based on their ranking_score
        - Place keywords in their specified content_location only if it matches the existing HTML structure
        - Maintain keyword density AS MUCH AS YOU CAN for primary keywords
        - Use semantic variations and LSI keywords naturally where they fit within existing structure
        - Avoid unnecessary keyword repetition and noise

        3. Content Structure Guidelines
        - Keep all existing headings in their original hierarchy
        - Preserve the original content flow and section organization
        - Optimize text within existing heading tags using provided outlines
        - Maintain all existing formatting and layout elements

        4. SEO Optimization Rules
        - Only optimize text content within existing HTML elements
        - Ensure natural keyword placement within current structure
        - Maintain readability while incorporating target keywords
        - Preserve technical accuracy and meaning
        - Keep professional tone and style consistent

        5. Quality Controls
        - Verify all original HTML tags remain unchanged
        - Maintain original content meaning and intent
        - Ensure factual accuracy
        - Check for grammar and spelling
        - Maintain natural language flow

        OUTPUT REQUIREMENTS:
        1. Return content with exactly the same HTML structure as input
        2. Only modify text content within existing tags
        3. Include all the necessary target keywords where they naturally fit
        4. Preserve all formatting and layout elements

        CONSTRAINTS:
        1. DO NOT modify any HTML tags or structure
        2. Only optimize text while keeping original formatting
        3. Maintain all technical terminology and accuracy


        Please optimize the content following these strict preservation guidelines.
        """
    return prompt


def optimize_content(df):
    print("Inside optimize content function")
    """
    Optimizes webpage content using provided SEO keywords and outlines.
    
    Parameters:
    df: DataFrame with columns:
        - aggregate_synonyms: List of tuples (keyword, importance, tag)
        - aggregate_outlines: List of tuples (outline, importance, heading_type)
        - page_text_txt: Original webpage content
    
    Returns:
    DataFrame with new column 'modified_content'
    """

    def process_row(row):
        # Convert string representations of lists to actual lists if needed
        try:
            synonyms = (
                literal_eval(row["aggregate_synonyms"])
                if isinstance(row["aggregate_synonyms"], str)
                else row["aggregate_synonyms"]
            )
            outlines = (
                literal_eval(row["aggregate_outlines"])
                if isinstance(row["aggregate_outlines"], str)
                else row["aggregate_outlines"]
            )
        except:
            return "Error: Invalid data format"

        # Extract and sort keywords by importance
        keywords = sorted(
            [(kw, imp, tag) for kw, imp, tag in synonyms], key=lambda x: x[1]
        )
        logging.info("*************Keywords**********", keywords)

        # Extract and sort outlines by heading type
        content_structure = sorted(
            [(outline, imp, type_) for outline, imp, type_ in outlines],
            key=lambda x: x[2],  # Sort by heading type (title, h1, h2, etc.)
        )
        logging.info("*************content_structure**********", content_structure)
        logging.info("*************row**********", row)
        result = run_openai_api(keywords, content_structure, row)
        return result

    # Apply the optimization function to each row
    df["modified_content"] = df.apply(process_row, axis=1)

    return df


def safe_parse(field_value):
    """
    Parses the field value into a list.
    If the field value looks like a Python literal list (starts with '[' and ends with ']'),
    then literal_eval is used.
    Otherwise, if common delimiters are found ('|' or ','), the string is split.
    """
    if pd.isna(field_value) or str(field_value).strip() == "":
        return []

    field_value = str(field_value).strip()
    # If it looks like a list literal, try literal_eval
    if field_value.startswith("[") and field_value.endswith("]"):
        try:
            return ast.literal_eval(field_value)
        except Exception as e:
            print("literal_eval failed on:", field_value, e)

    # Otherwise, check for common delimiters
    if "|" in field_value:
        return [x.strip() for x in field_value.split("|") if x.strip()]
    elif "," in field_value:
        return [x.strip() for x in field_value.split(",") if x.strip()]
    else:
        return [field_value]


def extract_optimization_metrics(df):
    """
    Analyzes the optimization results and provides metrics based on unique keyword/outline occurrences.

    For the modified content, the counts (and density) reflect only those keywords/outlines that
    are newly incorporated—that is, present in the modified text but not in the original.

    Parameters:
      df: DataFrame with original and modified content.

    Returns:
      DataFrame with optimization metrics.
    """
    metrics = []
    # df.to_csv('optimization_metricsinput.csv', index=False)

    for index, row in df.iterrows():
        # Convert row values to string if necessary
        row = row.astype(str)
        try:
            # Parse keywords from 'aggregate_synonyms'
            raw_synonyms = row.get("aggregate_synonyms", "")
            synonyms_parsed = safe_parse(raw_synonyms)
            if synonyms_parsed and isinstance(synonyms_parsed[0], (list, tuple)):
                keywords = {x[0].lower() for x in synonyms_parsed if x and len(x) > 0}
            else:
                keywords = {x.lower() for x in synonyms_parsed}
            print("Parsed Keywords:", keywords)

            # Parse outlines from 'aggregate_outlines'
            raw_outlines = row.get("aggregate_outlines", "")
            outlines_parsed = safe_parse(raw_outlines)
            if outlines_parsed and isinstance(outlines_parsed[0], (list, tuple)):
                outlines = {o[0].lower() for o in outlines_parsed if o and len(o) > 0}
            else:
                outlines = {o.lower() for o in outlines_parsed}
            print("Parsed Outlines:", outlines)

            # Extract texts and convert to lower-case
            modified_text = str(row.get("modified_content", "")).lower()
            original_text = str(row.get("page_text_txt", "")).lower()

            # Function to check if a multi-word phrase exists in text (using regex for whole word match)
            def phrase_exists(phrase, text):
                pattern = r"\b" + re.escape(phrase) + r"\b"
                return bool(re.search(pattern, text))

            # Identify unique keywords present in original and modified texts
            unique_kw_original = {
                kw for kw in keywords if phrase_exists(kw, original_text)
            }
            unique_kw_modified = {
                kw for kw in keywords if phrase_exists(kw, modified_text)
            }

            # Newly incorporated keywords: those that appear in modified but not in original
            new_keywords = sorted(list(unique_kw_modified - unique_kw_original))

            # Similarly, for outlines
            unique_outline_original = {ou for ou in outlines if ou in original_text}
            unique_outline_modified = {ou for ou in outlines if ou in modified_text}

            # Newly incorporated outlines: those that appear in modified but not in original
            new_outlines = sorted(
                list(unique_outline_modified - unique_outline_original)
            )

            # Word counts for content lengths
            original_words = original_text.split()
            modified_words = modified_text.split()

            # Counts for original remain as unique occurrences found in original text.
            unique_kw_count_original = len(unique_kw_original)
            unique_outline_count_original = len(unique_outline_original)

            # For modified, we now count only the new incorporations.
            new_kw_count_modified = len(new_keywords)
            new_outline_count_modified = len(new_outlines)

            # Density metrics: count of newly incorporated keywords/outlines divided by total words in modified text.
            keyword_density_modified = (
                new_kw_count_modified / len(modified_words) if modified_words else 0
            )

            metrics.append(
                {
                    "url_slug": row.get("url_slug", ""),
                    "keyword_count_original": unique_kw_count_original,
                    "keyword_count_modified": new_kw_count_modified,
                    "outline_count_original": unique_outline_count_original,
                    "outline_count_modified": new_outline_count_modified,
                    "content_length_original": len(original_words),
                    "content_length_modified": len(modified_words),
                    "keyword_density_original": (
                        unique_kw_count_original / len(original_words)
                        if original_words
                        else 0
                    ),
                    "keyword_density_modified": keyword_density_modified,
                    "keywords_incorporated": new_keywords,
                    "outlines_incorporated": new_outlines,
                }
            )
        except Exception as e:
            print(f"Error processing row {index}: {e}")
            metrics.append({})

    metrics_df = pd.DataFrame(metrics)
    metrics_df.to_csv("optimization_metrics.csv", index=False)
    return metrics_df


df = pd.read_csv("optimization_metricsinput.csv")
extract_optimization_metrics(df)
