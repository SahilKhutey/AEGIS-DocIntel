import os
import json

def generate():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    categories = {
        "scientific_papers": 250,
        "invoices": 200,
        "reports": 200,
        "manuals": 150,
        "books": 100,
        "engineering_drawings": 100
    }
    
    # Create category directories
    for cat in categories.keys():
        os.makedirs(os.path.join(base_dir, cat), exist_ok=True)
        
    os.makedirs(os.path.join(base_dir, "ground_truth", "per_category"), exist_ok=True)
    
    # We will write the per-category ground truth lists
    master_gt_path = os.path.join(base_dir, "ground_truth", "master_ground_truth.json")
    with open(master_gt_path, "r", encoding="utf-8") as f:
        master_gt = json.load(f)
        
    # Generate mock documents and write metadata
    for cat, count in categories.items():
        cat_gt_entries = {}
        # Find matching master ground truth if any
        matching_key = None
        for k, v in master_gt["documents"].items():
            if v["category"] == cat:
                matching_key = k
                break
                
        for i in range(1, count + 1):
            doc_id = f"{cat[:3]}_{i:03d}"
            # Create a mock document file (as a text file representing a pdf/doc)
            doc_filename = f"{doc_id}.pdf"
            doc_filepath = os.path.join(base_dir, cat, doc_filename)
            
            # Simple mock content
            content = f"AMDI-OS Mock Document {doc_id}\nCategory: {cat}\nThis is a placeholder for a production benchmark file."
            if i == 1 and matching_key:
                content += f"\nTitle: {master_gt['documents'][matching_key]['title']}\n"
                for entry in master_gt["documents"][matching_key]["entries"]:
                    content += f"Q: {entry['question']}\nA: {entry['expected_answer']}\n"
                    
            with open(doc_filepath, "w", encoding="utf-8") as f_doc:
                f_doc.write(content)
                
            # Create ground truth metadata file
            meta_filepath = os.path.join(base_dir, cat, f"{doc_id}.json")
            meta_content = {
                "document_id": doc_id,
                "category": cat,
                "entries": []
            }
            
            if i == 1 and matching_key:
                meta_content["entries"] = master_gt["documents"][matching_key]["entries"]
            else:
                # Generate a default factual entry
                meta_content["entries"] = [
                    {
                        "question": f"What is the ID of this {cat[:-1]}?",
                        "expected_answer": f"The ID of this {cat[:-1]} is {doc_id}.",
                        "expected_pages": [1],
                        "expected_citations": [
                            {"doc_id": doc_id, "page": 1, "excerpt": f"Mock Document {doc_id}"}
                        ],
                        "expected_entities": [doc_id],
                        "difficulty": "easy",
                        "type": "factual"
                    }
                ]
                
            with open(meta_filepath, "w", encoding="utf-8") as f_meta:
                json.dump(meta_content, f_meta, indent=2)
                
            cat_gt_entries[doc_id] = meta_content
            
        # Write per-category ground truth file
        per_cat_path = os.path.join(base_dir, "ground_truth", "per_category", f"{cat}.json")
        with open(per_cat_path, "w", encoding="utf-8") as f_per_cat:
            json.dump(cat_gt_entries, f_per_cat, indent=2)
            
    print(f"Generated 1,000 mock documents and per-category ground truth mappings.")

if __name__ == "__main__":
    generate()
