import logging
from openai import OpenAI
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


def run_openai_api(raw_content):
    client = OpenAI(api_key=OPENAI_API_KEY)

    try:
        prompt = generate_prompt(raw_content)

        response = client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",  # Update this to your specific model
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert SEO content optimizer with deep knowledge of search engine optimization of contents/articles and content writing.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,  # Lower temperature for more consistent output
            # max_tokens=4000   # Adjust based on your needs
        )

        optimized_content = response.choices[0].message.content.strip()
        print("@@@@@@@@@@@@@@@@@@2@@@@@@@", optimized_content)
        tokens_used = response.usage.total_tokens
        print("################################tokens_used : ", tokens_used)

        logging.info(f"Tokens used for content optimization: {tokens_used}")

        return optimized_content, tokens_used

    except Exception as e:
        logging.error(f"Error in OpenAI API call: {str(e)}")
        return None, 0

    #            **ANALYZE THE CONTENT BEFORE WRITING AND IT SHOULD BE HIGHLY STRUCTURED AND FORMATTED SO THAT THE CONTENT CAN BE UTILIZED FURTHER WITHOUT MODIFICATION**


def generate_prompt(raw_content):
    # Prepare prompt for GPT-4
    prompt = f"""Act as an expert content formatter. Transform the provided HTML content into a clean, well-structured text format that maintains hierarchy and readability while explicitly labeling content elements.
            INPUT DATA:
            {raw_content}
            TRANSFORMATION REQUIREMENTS:
            1. Text Formatting and Labeling Rules:
            - Convert HTML tags to explicit labeled elements (Title, H1, H2, etc.)
            - Each element should be labeled with its type followed by a hyphen, e.g., "Title- [title text]"
            - Headings should maintain their hierarchy (H1, H2, H3, etc.)
            - Remove all HTML tags and metadata
            - Remove navigation elements like "Top", "Search", etc.
            - Remove redundant elements and unnecessary spacing
            - Remove CTA buttons and links
            - Maintain proper paragraph spacing (one blank line between sections)
            2. Structure Format:
            Title- [Main title text]
            [blank line]
            H1- [Main heading text]
            [blank line]
            Paragraph- [Content text]
            [blank line]
            H2- [Section heading text]
            [blank line]
            Paragraph- [Section content]
            [blank line]
            H3- [Subsection heading text]
            [blank line]
            Paragraph- [Subsection content]
            3. Content Organization:
            - Start with the title/main title
            - Follow with main description/introduction
            - Present each section with its labeled heading followed by labeled content
            - Group related content together
            - Maintain logical flow between sections
            - Remove any redundant navigation or website-specific elements
            4. Cleaning Requirements:
            - Remove HTML formatting while preserving content hierarchy
            - Remove metadata
            - Remove navigation links
            - Remove button text
            - Remove redundant headings
            - Clean up any special characters
            - Fix any spacing issues
            - Remove website-specific elements (like "SearchThermo Fisher Scientific")
            OUTPUT EXAMPLE:
            Title- INTACT PROTEIN ANALYSIS WORKFLOWS
            H1- PROTEIN ANALYSIS SOLUTIONS
            Paragraph- [Main introduction paragraph about protein analysis]
            H2- Confident protein characterization methods
            Paragraph- [Content about characterization methods]
            H2- Featured chromatography solutions
            Paragraph- [Relevant content about chromatography solutions]
            [Continue with other sections...]
            CONSTRAINTS:
            1. Maintain all technical information accurately
            2. Preserve the meaning and context
            3. Keep product descriptions intact
            4. Maintain proper content hierarchy with explicit labeling
            5. Ensure readability and flow
            6. Do not add any content that wasn't in the original HTML
            Please transform the content into clean text format with explicit element labeling while maintaining its original meaning, technical accuracy, and logical structure."""
    return prompt


import re


def clean_text(input_text):
    # Remove leading/trailing spaces and special characters like `*` from each line
    text = re.sub(r"\*\*", "", input_text)  # Remove all asterisks `**`
    text = re.sub(r"\s*\n\s*", "\n", text)  # Remove excessive spaces around newlines
    text = re.sub(
        r"\n{2,}", "\n\n", text
    )  # Replace multiple newlines with a single paragraph break

    # Remove additional characters if present, like leading spaces after removing characters
    text = text.strip()

    return text


def final_optimize_content(df):
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

        result = run_openai_api(row["modified_content"])
        # try:
        #     result = clean_text(result)
        # except:
        #     pass
        return result

    # Apply the optimization function to each row
    df["modified_content_v1"] = df.apply(process_row, axis=1)

    return df
