"""
PubMed E-utilities Service
Tìm kiếm bài báo y khoa từ PubMed/NCBI.
Reference: CLARA Section 5 — Data Sources (PubMed E-utilities)
API Docs: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/
"""
import httpx
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from config import get_settings

settings = get_settings()

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


async def search_pubmed(query: str, max_results: int = 5) -> List[Dict]:
    """
    Tìm kiếm PubMed theo keyword, trả về danh sách bài báo với PMID, title, abstract.
    Pipeline: esearch (tìm PMID) → efetch (lấy chi tiết)
    """
    try:
        pmids = await _esearch(query, max_results)
        if not pmids:
            return []
        articles = await _efetch(pmids)
        return articles
    except Exception as e:
        print(f"[PubMed] Error: {e}")
        return []


async def _esearch(query: str, max_results: int) -> List[str]:
    """Bước 1: Tìm kiếm PMIDs từ keyword"""
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
        "sort": "relevance",
    }
    if settings.pubmed_api_key:
        params["api_key"] = settings.pubmed_api_key

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f"{BASE_URL}/esearch.fcgi", params=params)
        resp.raise_for_status()
        data = resp.json()
        return data.get("esearchresult", {}).get("idlist", [])


async def _efetch(pmids: List[str]) -> List[Dict]:
    """Bước 2: Lấy chi tiết bài báo từ PMIDs"""
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        "rettype": "abstract",
    }
    if settings.pubmed_api_key:
        params["api_key"] = settings.pubmed_api_key

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(f"{BASE_URL}/efetch.fcgi", params=params)
        resp.raise_for_status()

        articles = []
        root = ET.fromstring(resp.text)

        for article_elem in root.findall(".//PubmedArticle"):
            article = _parse_article(article_elem)
            if article:
                articles.append(article)

        return articles


def _parse_article(elem) -> Optional[Dict]:
    """Parse XML element thành dict"""
    try:
        pmid_elem = elem.find(".//PMID")
        title_elem = elem.find(".//ArticleTitle")
        abstract_elems = elem.findall(".//AbstractText")

        pmid = pmid_elem.text if pmid_elem is not None else ""
        title = title_elem.text if title_elem is not None else ""

        # Gộp các phần abstract
        abstract_parts = []
        for ab in abstract_elems:
            label = ab.get("Label", "")
            text = ab.text or ""
            if label:
                abstract_parts.append(f"**{label}**: {text}")
            else:
                abstract_parts.append(text)
        abstract = "\n".join(abstract_parts)

        # Authors
        authors = []
        for author in elem.findall(".//Author"):
            last = author.findtext("LastName", "")
            first = author.findtext("ForeName", "")
            if last:
                authors.append(f"{last} {first}".strip())

        # Journal
        journal = elem.findtext(".//Journal/Title", "")
        year = elem.findtext(".//PubDate/Year", "")

        return {
            "source": "pubmed",
            "pmid": pmid,
            "title": title,
            "abstract": abstract[:1500],  # Giới hạn để không quá dài
            "authors": authors[:5],  # Top 5 authors
            "journal": journal,
            "year": year,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        }
    except Exception:
        return None

