"""
Codeforces Problem Scraper with Cloudflare Bypass
Uses cloudscraper to handle Cloudflare JS challenges automatically.
"""

import cloudscraper
from bs4 import BeautifulSoup
import asyncio
import copy
from typing import Optional, List, Dict

# Initialize scraper globally to reuse session (faster subsequent requests)
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)


def _clean_pre_text(tag) -> str:
    """Extract text from <pre> tag, replacing <br> with newlines."""
    pre = tag.find('pre')
    if not pre:
        return ""
    # Replace <br> tags with newlines before extracting text
    for br in pre.find_all('br'):
        br.replace_with('\n')
    return pre.get_text().strip()


def _scrape_problem_sync(contest_id: str, problem_index: str) -> Optional[Dict]:
    """
    Synchronous scraping function that handles Cloudflare challenge.
    """
    url = f"https://codeforces.com/contest/{contest_id}/problem/{problem_index}"
    
    try:
        # This blocks while solving Cloudflare challenge (2-4s first time)
        response = scraper.get(url, timeout=30)
        if response.status_code != 200:
            print(f"Error {response.status_code} for {url}")
            return None
    except Exception as e:
        print(f"Scraper Exception: {e}")
        return None

    soup = BeautifulSoup(response.text, 'lxml')
    
    # Extract Sample Tests
    examples = []
    sample_test_div = soup.find('div', class_='sample-test')
    
    if sample_test_div:
        inputs = sample_test_div.find_all('div', class_='input')
        outputs = sample_test_div.find_all('div', class_='output')
        
        for inp, out in zip(inputs, outputs):
            examples.append({
                "input": _clean_pre_text(inp),
                "output": _clean_pre_text(out)
            })

    # Extract time and memory limits
    time_limit = ""
    memory_limit = ""
    header = soup.find('div', class_='header')
    if header:
        time_div = header.find('div', class_='time-limit')
        if time_div:
            time_limit = time_div.get_text().replace("time limit per test", "").strip()
        memory_div = header.find('div', class_='memory-limit')
        if memory_div:
            memory_limit = memory_div.get_text().replace("memory limit per test", "").strip()

    # Extract Problem Statement
    statement_text = ""
    problem_statement_div = soup.find('div', class_='problem-statement')
    if problem_statement_div:
        # Clone and remove unwanted sections to get clean text
        stmt = copy.copy(problem_statement_div)
        for junk in stmt.find_all('div', class_=['sample-tests', 'sample-test', 'header', 'input-specification', 'output-specification', 'note']):
            junk.decompose()
        statement_text = stmt.get_text(" ", strip=True)

    # Extract input/output specification
    input_spec = ""
    output_spec = ""
    input_spec_div = soup.find('div', class_='input-specification')
    if input_spec_div:
        input_spec = input_spec_div.get_text(" ", strip=True).replace("Input", "", 1).strip()
    output_spec_div = soup.find('div', class_='output-specification')
    if output_spec_div:
        output_spec = output_spec_div.get_text(" ", strip=True).replace("Output", "", 1).strip()

    # Extract note if present
    note = ""
    note_div = soup.find('div', class_='note')
    if note_div:
        note = note_div.get_text(" ", strip=True).replace("Note", "", 1).strip()

    return {
        "id": f"{contest_id}{problem_index}",
        "contestId": int(contest_id),
        "index": problem_index.upper(),
        "url": url,
        "timeLimit": time_limit,
        "memoryLimit": memory_limit,
        "statement": statement_text[:2000] if len(statement_text) > 2000 else statement_text,
        "inputSpecification": input_spec,
        "outputSpecification": output_spec,
        "note": note,
        "examples": examples
    }


def _scrape_examples_sync(contest_id: str, problem_index: str) -> Optional[List[Dict[str, str]]]:
    """
    Lightweight synchronous scraping - only fetches test cases.
    """
    url = f"https://codeforces.com/contest/{contest_id}/problem/{problem_index}"
    
    try:
        response = scraper.get(url, timeout=30)
        if response.status_code != 200:
            return None
    except Exception:
        return None

    soup = BeautifulSoup(response.text, 'lxml')
    sample_test_div = soup.find('div', class_='sample-test')
    
    if not sample_test_div:
        return None

    examples = []
    inputs = sample_test_div.find_all('div', class_='input')
    outputs = sample_test_div.find_all('div', class_='output')

    for inp, out in zip(inputs, outputs):
        examples.append({
            "input": _clean_pre_text(inp),
            "output": _clean_pre_text(out)
        })

    return examples if examples else None


# Async wrappers so we don't block FastAPI's event loop
async def scrape_problem_data(contest_id: str, problem_index: str) -> Optional[Dict]:
    """
    Async wrapper for full problem scraping.
    Uses asyncio.to_thread to run blocking cloudscraper in thread pool.
    """
    return await asyncio.to_thread(_scrape_problem_sync, contest_id, problem_index)


async def scrape_examples_only(contest_id: str, problem_index: str) -> Optional[List[Dict[str, str]]]:
    """
    Async wrapper for lightweight example-only scraping.
    """
    return await asyncio.to_thread(_scrape_examples_sync, contest_id, problem_index)
