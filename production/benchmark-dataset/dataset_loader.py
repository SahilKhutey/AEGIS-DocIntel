import os
import json
from pathlib import Path
from typing import Dict, List, Any

class LoadedCategory:
    def __init__(self, name: str, documents: List[Dict[str, Any]]):
        self.name = name
        self.documents = documents

    def __len__(self) -> int:
        return len(self.documents)

    def total_questions(self) -> int:
        return sum(len(doc.get("entries", [])) for doc in self.documents)

class DatasetLoader:
    """Utility to load and partition the AMDI-OS Benchmark Dataset."""
    
    def __init__(self, dataset_path: str):
        self.dataset_path = Path(dataset_path)
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset path not found: {self.dataset_path}")
            
    def load_category(self, category: str, max_documents: int = None) -> LoadedCategory:
        category_dir = self.dataset_path / category
        if not category_dir.exists():
            raise FileNotFoundError(f"Category directory not found: {category_dir}")
            
        loaded_docs = []
        meta_files = sorted(category_dir.glob("*.json"))
        
        if max_documents:
            meta_files = meta_files[:max_documents]
            
        for meta_file in meta_files:
            doc_id = meta_file.stem
            pdf_file = category_dir / f"{doc_id}.pdf"
            
            with open(meta_file, "r", encoding="utf-8") as f:
                meta_data = json.load(f)
                
            text_content = ""
            if pdf_file.exists():
                with open(pdf_file, "r", encoding="utf-8") as f_pdf:
                    text_content = f_pdf.read()
                    
            loaded_docs.append({
                "document_id": doc_id,
                "text": text_content,
                "entries": meta_data.get("entries", []),
                "category": category
            })
            
        return LoadedCategory(category, loaded_docs)
