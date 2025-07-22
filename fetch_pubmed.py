import requests
import xml.etree.ElementTree as ET
import csv
from datetime import datetime

def fetch_pubmed(query, max_results=5, start_year=None, end_year=None):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    search_url = f"{base_url}esearch.fcgi"
    search_params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json"
    }

    if start_year and end_year:
        search_params["mindate"] = start_year
        search_params["maxdate"] = end_year
        search_params["datetype"] = "pdat"

    try:
        search_response = requests.get(search_url, params=search_params)
        search_response.raise_for_status()
        ids = search_response.json().get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        print(f"Search failed: {e}")
        return

    if not ids:
        print("No articles found for your search.")
        return

    fetch_url = f"{base_url}efetch.fcgi"
    fetch_params = {
        "db": "pubmed",
        "id": ",".join(ids),
        "retmode": "xml"
    }

    try:
        fetch_response = requests.get(fetch_url, params=fetch_params)
        fetch_response.raise_for_status()
        root = ET.fromstring(fetch_response.content)
    except Exception as e:
        print(f"Fetching details failed: {e}")
        return

    articles = []
    for article in root.findall(".//PubmedArticle"):
        title = article.findtext(".//ArticleTitle", default="No title")
        abstract = article.findtext(".//AbstractText", default="No abstract")
        pub_date = article.findtext(".//PubDate/Year") or "Unknown"

        # 🔎 Try to find the DOI
        doi = "Not available"
        for id_elem in article.findall(".//ArticleId"):
            if id_elem.attrib.get("IdType") == "doi":
                doi = id_elem.text
                break

        articles.append({
            "Title": title.strip(),
            "Abstract": abstract.strip(),
            "Publication Year": pub_date,
            "DOI": doi
        })

        print(f"\nTitle: {title}\nYear: {pub_date}\nDOI: {doi}\nAbstract: {abstract}\n{'-'*60}")

        print(f"\nTitle: {title}\nYear: {pub_date}\nAbstract: {abstract}\n{'-'*60}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"pubmed_results_{timestamp}.csv"
    try:
        with open(filename, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Title", "Abstract", "Publication Year", "DOI"])
            writer.writeheader()
            writer.writerows(articles)
        print(f"\n✅ Results saved to: {filename}")
    except Exception as e:
        print(f"❌ Could not save CSV: {e}")

if __name__ == "__main__":
    query = input("🔎 Enter search query: ").strip()
    max_results = input("📄 Number of articles to fetch (default 5): ").strip()
    start_year = input("📅 Start year (optional): ").strip()
    end_year = input("📅 End year (optional): ").strip()

    max_results = int(max_results) if max_results.isdigit() else 5
    start_year = start_year if start_year else None
    end_year = end_year if end_year else None

    fetch_pubmed(query, max_results=max_results, start_year=start_year, end_year=end_year)