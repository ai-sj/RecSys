import argparse
import json
import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import quote

def get_scholar_data(query):
    """
    Scrape Google Scholar organic search results for a given query.
    The query is expected to be a string (e.g. a paper title enclosed in quotes).
    """
    url = "https://www.google.com/scholar?q=" + quote(query)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        for el in soup.select(".gs_r"):
            try:
                result = {}
                # Get title and title link
                title_el = el.select_one(".gs_rt")
                if title_el:
                    result["title"] = title_el.get_text()
                    a_tag = title_el.find("a")
                    if a_tag and 'href' in a_tag.attrs:
                        result["title_link"] = a_tag["href"]
                        result["id"] = a_tag.get("id", "")
                # Displayed link and snippet
                displayed_link = el.select_one(".gs_a")
                if displayed_link:
                    result["displayed_link"] = displayed_link.get_text()
                snippet = el.select_one(".gs_rs")
                if snippet:
                    result["snippet"] = snippet.get_text(strip=True)
                # Cited by info
                cited_a = el.select_one(".gs_nph+ a")
                if cited_a:
                    result["cited_by_count"] = cited_a.get_text()
                    result["cited_link"] = "https://scholar.google.com" + cited_a.get("href", "")
                # Versions info (if available)
                versions_el = el.select("a ~ a")
                if versions_el and len(versions_el) >= 1:
                    ver_el = versions_el[0].find_next_sibling("a")
                    if ver_el:
                        result["versions_count"] = ver_el.get_text()
                        result["versions_link"] = "https://scholar.google.com" + ver_el.get("href", "")
                # Remove empty fields
                result = {k: v for k, v in result.items() if v}
                results.append(result)
            except Exception as e:
                print("Error parsing a scholar result:", e)
        return results
    except Exception as e:
        print("Error fetching Google Scholar data:", e)
        return []

def get_scholar_profiles(author_name):
    """
    Scrape Google Scholar author search results for a given author name.
    Returns a list of profile dictionaries.
    """
    base_url = "https://scholar.google.com/citations?hl=en&view_op=search_authors&mauthors="
    query = quote(author_name)
    url = base_url + query
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    profiles = []
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        for el in soup.select('.gsc_1usr'):
            profile = {}
            name_el = el.select_one('.gs_ai_name')
            if name_el:
                profile['name'] = name_el.get_text()
                a_tag = name_el.find("a")
                if a_tag and 'href' in a_tag.attrs:
                    profile['name_link'] = "https://scholar.google.com" + a_tag['href']
            pos_el = el.select_one('.gs_ai_aff')
            if pos_el:
                profile['position'] = pos_el.get_text()
            email_el = el.select_one('.gs_ai_eml')
            if email_el:
                profile['email'] = email_el.get_text()
            dept_el = el.select_one('.gs_ai_int')
            if dept_el:
                profile['departments'] = dept_el.get_text()
            cited_el = el.select_one('.gs_ai_cby')
            if cited_el:
                profile['cited_by_count'] = cited_el.get_text().split()[-1]
            # Remove empty fields
            profile = {k: v for k, v in profile.items() if v}
            profiles.append(profile)
        return profiles
    except Exception as e:
        print("Error fetching scholar profiles for author:", author_name, e)
        return []

def get_author_profile_data(profile_url):
    """
    Scrape detailed author profile data from a Google Scholar profile URL.
    This includes basic info, published articles, and citation metrics.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        response = requests.get(profile_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        profile_data = {}
        # Basic info extraction
        name_el = soup.select_one("#gsc_prf_in")
        if name_el:
            profile_data["name"] = name_el.get_text()
        pos_el = soup.select_one("#gsc_prf_inw+ .gsc_prf_il")
        if pos_el:
            profile_data["position"] = pos_el.get_text()
        email_el = soup.select_one("#gsc_prf_ivh")
        if email_el:
            profile_data["email"] = email_el.get_text()
        dept_el = soup.select_one("#gsc_prf_int")
        if dept_el:
            profile_data["departments"] = dept_el.get_text()
        
        # Articles extraction
        articles = []
        for el in soup.select("#gsc_a_b .gsc_a_t"):
            article = {}
            title_el = el.select_one(".gsc_a_at")
            if title_el:
                article["title"] = title_el.get_text()
                article_link = title_el.get("href", "")
                if article_link:
                    article["link"] = "https://scholar.google.com" + article_link
            authors_el = el.select_one(".gs_gray")
            if authors_el:
                article["authors"] = authors_el.get_text()
            pubs = el.select(".gs_gray")
            if len(pubs) > 1:
                article["publication"] = pubs[1].get_text()
            article = {k: v for k, v in article.items() if v}
            articles.append(article)
        profile_data["articles"] = articles
        
        # Citation metrics extraction
        table = []
        try:
            # Total citations
            row = {}
            total_cites = soup.select_one("tr:nth-child(1) .gsc_rsb_std")
            if total_cites:
                row['citations'] = {"all": total_cites.get_text()}
            table.append(row)
            # h-index
            row = {}
            h_index_all = soup.select_one("tr:nth-child(2) .gsc_rsb_std")
            if h_index_all:
                row['h_index'] = {"all": h_index_all.get_text()}
            table.append(row)
            # i-index
            row = {}
            i_index_all = soup.select_one("tr:nth-child(3) .gsc_rsb_std")
            if i_index_all:
                row['i_index'] = {"all": i_index_all.get_text()}
            table.append(row)
        except Exception as e:
            print("Error parsing citation metrics:", e)
        profile_data["citation_metrics"] = table
        
        return profile_data
    except Exception as e:
        print("Error fetching author profile data from", profile_url, e)
        return {}

def main():
    parser = argparse.ArgumentParser(
        description="Build a database from arXiv data with additional Google Scholar scraping."
    )
    parser.add_argument('--arxiv_data', type=str, default="arxiv_data.json", help="Input arXiv data JSON file")
    parser.add_argument('--output', type=str, default="final_database.json", help="Output final database JSON file")
    args = parser.parse_args()
    
    # Load arXiv data
    try:
        with open(args.arxiv_data, "r", encoding="utf-8") as f:
            arxiv_papers = json.load(f)
    except Exception as e:
        print("Error loading arXiv data:", e)
        return
    
    final_database = []
    
    # Process each arXiv paper
    for paper in arxiv_papers:
        print("Processing paper:", paper.get("title", ""))
        paper_entry = {"arxiv": paper}
        
        # Google Scholar search using the paper title (enclosed in quotes)
        query = f'"{paper.get("title", "")}"'
        scholar_results = get_scholar_data(query)
        paper_entry["scholar_search"] = scholar_results
        
        # Process authors from arXiv data (assumed comma-separated string)
        authors_list = [a.strip() for a in paper.get("authors", "").split(",") if a.strip()]
        authors_details = []
        for author in authors_list:
            print("  Processing author:", author)
            author_entry = {"author_name": author}
            profiles = get_scholar_profiles(author)
            detailed_profiles = []
            for profile in profiles:
                if "name_link" in profile:
                    profile_url = profile["name_link"]
                    profile_data = get_author_profile_data(profile_url)
                    combined_profile = {**profile, **profile_data}
                    detailed_profiles.append(combined_profile)
                    # Sleep briefly to avoid being blocked
                    time.sleep(1)
            author_entry["profiles"] = detailed_profiles
            authors_details.append(author_entry)
            time.sleep(1)
        paper_entry["authors_details"] = authors_details
        
        final_database.append(paper_entry)
        time.sleep(2)
    
    # Save the final database to a JSON file
    try:
        with open(args.output, "w", encoding="utf-8") as out_file:
            json.dump(final_database, out_file, ensure_ascii=False, indent=4)
        print(f"Final database saved to {args.output}")
    except Exception as e:
        print("Error saving final database:", e)

if __name__ == "__main__":
    main()