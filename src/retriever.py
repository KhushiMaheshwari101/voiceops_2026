import re
from typing import List, Dict, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from src.kb_indexer import (
    KBChunk,
    load_kb_chunks,
    load_products_catalog,
    load_pincodes_catalog,
)


class HybridRetriever:
    def __init__(self):
        self.chunks: List[KBChunk] = load_kb_chunks()
        self.products = load_products_catalog()
        self.pincodes = load_pincodes_catalog()

        # Build corpus texts
        self.corpus = []
        for c in self.chunks:
            # We enrich the text for indexing with metadata
            text = f"{c.doc_title} {c.section_id} {c.section_title} {c.content}"
            self.corpus.append(text)

        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
            max_df=0.85,
            sublinear_tf=True,
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(self.corpus)

    def find_referenced_products(self, query: str) -> List[Tuple[str, Dict[str, Any]]]:
        """Detect SKUs or product titles in query."""
        found = []
        # Check SKU pattern: e.g., ELE-0012, BKS-0056, APP-0001
        sku_matches = re.findall(r"\b([A-Z]{3}-\d{4})\b", query.upper())
        for sku in sku_matches:
            if sku in self.products:
                found.append((f"products.csv:{sku}", self.products[sku]))

        # Check titles if SKU not explicitly given
        if not found:
            q_lower = query.lower()
            for sku, prod in self.products.items():
                title = prod.get("title", "").lower()
                # Check significant title keywords
                # e.g., "gulmohar matte lipstick", "urbanthread slim fit jeans", "pagecraft"
                words = [w for w in re.split(r"\W+", title) if len(w) > 3]
                match_count = sum(1 for w in words if w in q_lower)
                if match_count >= 2 or (len(words) == 1 and words[0] in q_lower):
                    found.append((f"products.csv:{sku}", prod))
                    break

        return found

    def retrieve(
        self, query: str, top_k: int = 4, threshold: float = 0.08
    ) -> Dict[str, Any]:
        """Retrieve most relevant knowledge chunks respecting precedence rules."""
        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.tfidf_matrix)[0]

        # Product detection
        prod_matches = self.find_referenced_products(query)

        # Keyword boosts for specific high-value terms
        q_lower = query.lower()
        scored_candidates = []
        for idx, chunk in enumerate(self.chunks):
            score = float(sims[idx])

            # Precedence adjustment:
            # Policy (rank 1) gets preference over FAQ (rank 4)
            # Superseded chunks (rank 99) get heavily penalized unless user specifically asks about historical
            if "before 1 august" not in q_lower and "purani" not in q_lower and chunk.status == "superseded":
                score *= 0.15
            elif chunk.doc_type == "policy":
                score *= 1.25
            elif chunk.doc_type == "agent_guide":
                score *= 1.15
            elif chunk.doc_type == "faq":
                score *= 0.90
            elif chunk.doc_type == "marketing":
                score *= 0.80

            # Exact section or keyword boost
            if chunk.section_id.lower() in q_lower:
                score += 0.5

            if score >= threshold:
                scored_candidates.append((score, chunk))

        # Sort by score descending
        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        selected_chunks: List[KBChunk] = [c for _, c in scored_candidates[:top_k]]
        evidence_tokens = [c.section_id for c in selected_chunks]

        # Add products to evidence tokens and context
        product_contexts = []
        for prod_token, prod_data in prod_matches:
            evidence_tokens.append(prod_token)
            p_desc = (
                f"Product {prod_data.get('sku')}: {prod_data.get('title')} | "
                f"Category: {prod_data.get('return_category')} | Price: ₹{prod_data.get('price_inr')} | "
                f"Assured: {prod_data.get('assured')} | Warranty: {prod_data.get('warranty_months')} months | "
                f"Fulfilled by: {prod_data.get('fulfilled_by')}"
            )
            product_contexts.append(p_desc)

        # Determine answerable flag
        is_answerable = len(selected_chunks) > 0 or len(prod_matches) > 0
        max_score = scored_candidates[0][0] if scored_candidates else 0.0
        if max_score < threshold and not prod_matches:
            is_answerable = False

        # Format retrieved context
        context_lines = []
        for c in selected_chunks:
            context_lines.append(f"--- Section [{c.section_id}]: {c.section_title} ({c.doc_type}, status: {c.status}) ---\n{c.content}")

        if product_contexts:
            context_lines.append("--- Product Catalog Records ---\n" + "\n".join(product_contexts))

        formatted_context = "\n\n".join(context_lines)

        return {
            "query": query,
            "answerable": is_answerable,
            "max_score": max_score,
            "chunks": selected_chunks,
            "evidence_tokens": evidence_tokens,
            "context": formatted_context,
            "products": prod_matches,
        }
