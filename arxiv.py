import argparse
import feedparser
from datetime import datetime
import json
import csv

def fetch_arxiv_data(category="cs.AI", max_results=100, start_index=0, sort_order="descending"):
    """
    Fetch arXiv data using the provided API parameters.
    
    Parameters:
        category (str): arXiv category (e.g., 'cs.AI')
        max_results (int): Number of results to fetch from the API.
        start_index (int): The starting index for the results.
        sort_order (str): Sorting order ('ascending' or 'descending').
    
    Returns:
        list: A list of dictionaries containing paper details.
    """
    base_url = "http://export.arxiv.org/api/query?"
    query = (f"search_query=cat:{category}&start={start_index}&max_results={max_results}"
             f"&sortBy=submittedDate&sortOrder={sort_order}")
    feed_url = base_url + query

    print(f"Fetching: {feed_url}")
    feed = feedparser.parse(feed_url)

    papers = []
    for entry in feed.entries:
        # Parse the published date as a datetime object
        published = datetime.strptime(entry.published, '%Y-%m-%dT%H:%M:%SZ')
        paper = {
            "id": entry.id.split('/abs/')[-1],
            "submitter": None,
            "published": published.strftime('%Y-%m-%d'),
            "authors": ', '.join(author.name for author in entry.authors),
            "title": entry.title.strip().replace('\n', ' '),
            "comments": entry.get("arxiv_comment", None),
            "journal-ref": entry.get("arxiv_journal_ref", None),
            "doi": entry.get("arxiv_doi", None),
            "report-no": entry.get("arxiv_report_no", None),
            "categories": entry.tags[0]['term'] if entry.tags else None,
            "license": entry.get("arxiv_license", None),
            "abstract": entry.summary.strip().replace('\n', ' ')
        }
        papers.append(paper)

    return papers

def save_data(papers, output_format="json", output_file="arxiv_data"):
    """
    Save the paper data to a file in JSON or CSV format.
    
    Parameters:
        papers (list): List of paper dictionaries.
        output_format (str): The file format to save (either 'json' or 'csv').
        output_file (str): Output file name without extension.
    """
    if output_format == "json":
        filename = f"{output_file}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(papers, f, ensure_ascii=False, indent=4)
    elif output_format == "csv":
        filename = f"{output_file}.csv"
        if papers:
            keys = papers[0].keys()
            with open(filename, "w", newline='', encoding="utf-8") as f:
                dict_writer = csv.DictWriter(f, keys)
                dict_writer.writeheader()
                dict_writer.writerows(papers)
        else:
            with open(filename, "w", newline='', encoding="utf-8") as f:
                f.write("")  # Create an empty file
    else:
        raise ValueError("Unsupported output format. Use 'json' or 'csv'.")
    print(f"Saved {len(papers)} papers to {filename}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Fetch arXiv AI papers and save them in the specified format."
    )
    
    parser.add_argument('--category', type=str, default="cs.AI", help="arXiv category (e.g., cs.AI)")
    parser.add_argument('--max_results', type=int, default=100, help="Number of results to fetch from the API")
    parser.add_argument('--start_index', type=int, default=0, help="Start index for fetching results")
    parser.add_argument('--sort_order', type=str, default="descending", help="Sort order (ascending or descending)")
    parser.add_argument('--output_format', type=str, choices=['json', 'csv'], default="json", help="Output file format")
    parser.add_argument('--output_file', type=str, default="arxiv_data", help="Output file name (without extension)")
    
    args = parser.parse_args()
    
    # Fetch arXiv data using the provided parameters
    papers = fetch_arxiv_data(category=args.category,
                              max_results=args.max_results,
                              start_index=args.start_index,
                              sort_order=args.sort_order)
    
    # Save results in JSON or CSV format
    save_data(papers, output_format=args.output_format, output_file=args.output_file)