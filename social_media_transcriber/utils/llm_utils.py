# social_media_transcriber/utils/llm_utils.py
"""
Utilities for interacting with Large Language Models (LLMs) via OpenRouter
to enhance and format transcripts.
"""
import logging
import re
import requests
import subprocess
from typing import Dict, Any

from social_media_transcriber.config.settings import Settings

logger = logging.getLogger(__name__)

def format_mdx_with_prettier(mdx_text: str) -> str:
    """
    Formats a string of MDX text using a locally installed Prettier.

    Args:
        mdx_text: The raw MDX content string.

    Returns:
        The formatted MDX content string. Returns original on error.
    """
    try:
        process = subprocess.run(
            ["npx", "prettier", "--parser", "mdx"],
            input=mdx_text,
            capture_output=True,
            text=True,
            check=True,
        )
        return process.stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.warning("Could not format with Prettier. Is it installed? (npm install prettier)")
        logger.warning("Prettier error: %s", e)
        return mdx_text # Return original text if formatting fails

# --- FINAL REVISED SYSTEM PROMPT ---
SYSTEM_PROMPT = """
You are an expert technical editor. Your task is to take a raw, verbatim video transcript and reformat it into a clean, well-structured, and readable MDX document.

The primary goal is to **structure and polish the existing content, NOT to summarize or rewrite it**. The entire original transcript must be preserved.

Follow this step-by-step process precisely:
1.  **Analyze the <TRANSCRIPT> to identify logical sections and topics.** Use existing headings in the transcript (like "Data/Colab Intro") as strong cues for document structure.
2.  **Create Metadata:**
    - Generate 4-6 relevant, lowercase `tags` for the key topics.
    - Write a concise, one-sentence `summary` describing the document's content.
3.  **Create a YAML frontmatter block** containing `title`, `date`, `tags`, and `summary`. Use the exact title from the <TITLE> tag.
4.  **Format the Transcript Body:**
    - **Preserve All Content:** Do NOT summarize, condense, or omit any of the speaker's original points. The final output must be the complete, full-length transcript.
    - **Remove Extraneous Information:** Delete all timestamps (e.g., `0:46 -`) and source tags (e.g., ``).
    - **IMPOSE STRUCTURE:** Raw transcripts are often a continuous stream of text. It is your most important task to parse this stream and create a logical structure.
        - **Create Thematic Headings:** Identify recurring keywords and themes (e.g., `AI`, `Storage`, `APIs`, `Developer Experience`). Create `##` headings for these themes and group all related sentences under the appropriate heading.
        - **Use Paragraphs:** Under each heading, group sentences into short, focused paragraphs (2-5 sentences). **You must not output a single, large block of text.**
    - **Clean the Text:** Correct spelling, grammar, and punctuation errors.
    - **Improve Readability:** Combine short, fragmented sentences into fluent paragraphs. Break up long, run-on sentences. Use **bolding** for key terms and format file names or code snippets using `backticks`.
5.  **Add a "Key Takeaways" Section:**
    - At the very **end** of the full, formatted transcript, add a `## Key Takeaways` section.
    - Create a bulleted list of the 3-5 most important high-level points covered in the document. This section is the ONLY place where summarization is allowed.
6.  **Assemble the final MDX file.** Your response MUST begin directly with the frontmatter's opening `---`.

---
<EXAMPLE_INPUT>
<TITLE>Getting Started with the Data</TITLE>
<TRANSCRIPT>
So with that, let's just dive right in.
Data/Colab Intro
0:58 - Without wasting any time, let's just dive straight into the code and I will be teaching you guys concepts as we go. So this here is the UCI machine learning repository. And basically, 1:11 - they just have a ton of data sets that we can access. And I found this really cool one called the magic gamma telescope data set. Now over here, I have a colab 2:28 - notebook open. So you go to colab dot research dot google.com, you start a new notebook. And in order to import that downloaded file that we we got from the computer, we're going to go 3:40 - over here to this folder thing. And I am literally just going to drag and drop that file into here.
</TRANSCRIPT>
</EXAMPLE_INPUT>
---
<EXAMPLE_OUTPUT>
---
title: "Getting Started with the Data"
date: "2025-07-31"
tags: ["machine learning", "colab", "pandas", "data loading"]
summary: "A guide on how to load and inspect the 'Magic Gamma Telescope' dataset from the UCI Machine Learning Repository into a Google Colab notebook using Pandas."
---

# Getting Started with the Data

Let's dive straight into the code, and I will introduce concepts as we go.

## Data Source and Colab Setup

The dataset for this project comes from the **UCI Machine Learning Repository**, which hosts a large number of datasets for public use. The specific one we'll be using is the **Magic Gamma Telescope dataset**.

To begin, open a new notebook in Google Colab by navigating to `colab.research.google.com`. To import the downloaded data file, you can simply drag and drop it into the file explorer panel on the left side of the Colab interface.

## Key Takeaways
- The project uses the Magic Gamma Telescope dataset from the UCI Repository.
- Data can be easily uploaded to a Google Colab environment via drag-and-drop.
- The course will cover concepts alongside practical coding examples.
</EXAMPLE_OUTPUT>
---

FINAL RULES:
- Your entire response must be the complete, raw MDX file content.
- Do NOT wrap your response in Markdown code fences (```mdx ... ```).
- Do NOT add any conversational text, notes, or apologies.
"""

def _clean_mdx_output(llm_text: str) -> str:
    """
    Cleans and standardizes the LLM output to ensure valid MDX format.
    """
    start_fm_index = llm_text.find("---")
    if start_fm_index == -1:
        return llm_text.strip()

    text = llm_text[start_fm_index:]
    text = re.sub(r"^\s*```(mdx|yaml)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*```\s*", "", text, flags=re.MULTILINE)
    return text.strip()


def enhance_transcript_with_llm(raw_text: str, settings: Settings, title: str) -> str:
    """
    Sends a raw transcript to an LLM via OpenRouter for formatting.
    """
    if not settings.llm_api_key:
        raise ValueError("OpenRouter API key is not configured.")

    user_content = f"""
<TITLE>{title}</TITLE>
<TRANSCRIPT>
{raw_text}
</TRANSCRIPT>
"""

    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content.strip()},
        ],
        "temperature": 0.2,
    }

    try:
        logger.info("Sending request to OpenRouter API...")
        logger.info("Model: %s", settings.llm_model)
        logger.info("Raw text length: %d characters", len(raw_text))
        
        response = requests.post(
            settings.llm_api_url,
            headers=headers,
            json=payload,
            timeout=180
        )
        response.raise_for_status()
        
        data = response.json()
        logger.info("Received response from OpenRouter API")
        
        enhanced_text = data['choices'][0]['message']['content']
        logger.info("Enhanced text length: %d characters", len(enhanced_text))
        
        return enhanced_text.strip()

    except requests.exceptions.RequestException as e:
        logger.error("API request to OpenRouter failed: %s", e)
        if e.response:
            logger.error("Response status: %d", e.response.status_code)
            logger.error("Response body: %s", e.response.text)
        api_error = e.response.json().get("error", {}).get("message", str(e)) if e.response else str(e)
        raise IOError(f"Failed to communicate with OpenRouter API: {api_error}")