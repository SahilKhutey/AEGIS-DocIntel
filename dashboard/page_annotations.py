"""
AEGIS-AMDI-OS — Annotation Dashboard Page
===========================================
Page for manual annotation CRUD, AI-assisted auto-annotations,
JSON import/export, and collaborative threads.
"""
from __future__ import annotations

import streamlit as st
import json


def page_annotations():
    st.markdown('<p class="main-header">✏️ Annotation Toolkit</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Manual, collaborative, and AI-assisted document annotation</p>',
                unsafe_allow_html=True)

    from app import api_get, api_post, api_delete

    # 1. Fetch document stats to check if active doc exists
    stats = api_get("/v1/stats")
    if not stats:
        st.warning("⚠️ No document ingested. Go to Upload first.")
        return

    doc_id = stats.get("doc_id")
    filename = stats.get("filename", "document")
    st.success(f"📄 Active Document: **{filename}** (ID: `{doc_id[:8]}...`)")

    # 2. Main interface split
    col1, col2 = st.columns([2, 3])

    with col1:
        st.markdown("### ➕ Create Annotation")
        
        ann_type = st.selectbox(
            "Annotation Type",
            ["Note", "Highlight", "Correction", "Question", "Tag", "Verification", "Bookmark"]
        )

        with st.form("create_ann_form"):
            page = st.number_input("Page Number", min_value=1, value=1)
            user_id = st.text_input("Author / User ID", value="default")
            color = st.color_picker("Display Color", value="#fbbf24")

            # Dynamic fields based on type
            original_text = ""
            corrected_text = ""
            bbox_str = ""
            tags_str = ""
            claim = ""
            is_correct = True
            
            content = ""

            if ann_type == "Note":
                content = st.text_area("Note Content", placeholder="Write your note here...")
                bbox_str = st.text_input("Bounding Box (x0,y0,x1,y1) [Optional]", placeholder="0.1,0.2,0.3,0.4")
                tags_str = st.text_input("Tags (comma separated) [Optional]")
            
            elif ann_type == "Highlight":
                content = st.text_input("Highlighted Text [Optional]")
                bbox_str = st.text_input("Bounding Box (x0,y0,x1,y1) [Required]", placeholder="0.1,0.2,0.3,0.4")
                color = st.color_picker("Display Color", value="#fde047") # yellow highlight default
            
            elif ann_type == "Correction":
                original_text = st.text_area("Original Text")
                corrected_text = st.text_area("Corrected Text / Modification")
                bbox_str = st.text_input("Bounding Box (x0,y0,x1,y1) [Optional]")
            
            elif ann_type == "Question":
                content = st.text_area("Question Content", placeholder="What requires clarification?")
                bbox_str = st.text_input("Bounding Box (x0,y0,x1,y1) [Optional]")
            
            elif ann_type == "Tag":
                tags_str = st.text_input("Tags (comma separated) [Required]")
                element_id = st.text_input("Reference Element ID [Optional]")
            
            elif ann_type == "Verification":
                claim = st.text_area("Claim to Verify")
                is_correct = st.checkbox("Claim is Correct (Verified)", value=True)
                element_id = st.text_input("Reference Element ID [Optional]")
            
            elif ann_type == "Bookmark":
                content = st.text_input("Bookmark Label", value=f"Bookmark Page {page}")

            submit = st.form_submit_button("🚀 Add Annotation", use_container_width=True)

        if submit:
            # Parse bounding box
            bbox = None
            if bbox_str:
                try:
                    bbox = [float(x.strip()) for x in bbox_str.split(",")]
                    if len(bbox) != 4:
                        st.error("Bounding box must be 4 comma-separated values (x0,y0,x1,y1)")
                        return
                except ValueError:
                    st.error("Invalid bounding box values. Must be numeric.")
                    return

            # Parse tags
            tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []

            # Prepare Payload and Call API
            with st.spinner("Saving annotation..."):
                result = None
                if ann_type == "Note":
                    result = api_post("/v1/annotations/note", {
                        "doc_id": doc_id, "page": page, "content": content,
                        "bbox": bbox, "color": color, "tags": tags, "user_id": user_id
                    })
                elif ann_type == "Highlight":
                    if not bbox:
                        st.error("Highlight requires bounding box coordinates!")
                        return
                    result = api_post("/v1/annotations/highlight", {
                        "doc_id": doc_id, "page": page, "bbox": bbox,
                        "text": content, "color": color, "user_id": user_id
                    })
                elif ann_type == "Correction":
                    result = api_post("/v1/annotations/correction", {
                        "doc_id": doc_id, "page": page, "original_text": original_text,
                        "corrected_text": corrected_text, "bbox": bbox, "user_id": user_id
                    })
                elif ann_type == "Question":
                    result = api_post("/v1/annotations/", {
                        "doc_id": doc_id, "type": "question", "user_id": user_id,
                        "position": {"page": page, "bbox": bbox},
                        "content": content, "color": color, "metadata": {"resolved": False}
                    })
                elif ann_type == "Tag":
                    if not tags:
                        st.error("Tag annotation requires at least one tag!")
                        return
                    result = api_post("/v1/annotations/", {
                        "doc_id": doc_id, "type": "tag", "user_id": user_id,
                        "position": {"page": page},
                        "content": ", ".join(tags), "color": color, "tags": tags
                    })
                elif ann_type == "Verification":
                    result = api_post("/v1/annotations/verify", {
                        "doc_id": doc_id, "page": page, "claim": claim,
                        "is_correct": is_correct, "user_id": user_id
                    })
                elif ann_type == "Bookmark":
                    result = api_post("/v1/annotations/", {
                        "doc_id": doc_id, "type": "bookmark", "user_id": user_id,
                        "position": {"page": page}, "content": content, "color": color
                    })

                if result:
                    st.success(f"Annotation created successfully! ID: `{result.get('id', '')[:8]}`")
                    st.rerun()

        # Export & Import Panel
        st.markdown("---")
        st.markdown("### 📥 Import / Export Annotations")
        
        col_exp, col_imp = st.columns(2)
        with col_exp:
            if st.button("📤 Export to JSON", use_container_width=True):
                exp_data = api_get(f"/v1/annotations/export/{doc_id}")
                if exp_data:
                    st.download_button(
                        label="💾 Download JSON File",
                        data=exp_data.get("json_data", "{}"),
                        file_name=f"annotations_{doc_id[:8]}.json",
                        mime="application/json",
                        use_container_width=True
                    )
        
        with col_imp:
            uploaded_file = st.file_uploader("Upload JSON annotations", type=["json"])
            if uploaded_file:
                json_content = uploaded_file.getvalue().decode("utf-8")
                if st.button("📥 Import Now", use_container_width=True):
                    res = api_post(f"/v1/annotations/import/{doc_id}", {"json_data": json_content})
                    if res:
                        st.success(f"Imported {res.get('imported_count', 0)} annotations!")
                        st.rerun()

    with col2:
        # 3. AI Assistant Trigger Section
        st.markdown("### 🤖 AI-Assisted Annotations")
        st.info("""
        AI Assistant scans the document using rule-based parsing and pattern detection to:
        - Auto-tag elements by categories (financial, technical, legal, etc.)
        - Highlight potential numerical claims and suggest verification checks
        - Detect ambiguous sections and generate clarification questions
        - Flag magnitude inconsistencies in numerical datasets
        """)
        
        col_ai1, col_ai2 = st.columns([2, 1])
        with col_ai1:
            enable_insights = st.checkbox("Generate LLM section-level insights (slow)", value=False)
        with col_ai2:
            if st.button("💡 Auto-Annotate", type="primary", use_container_width=True):
                with st.spinner("AI Assistant analyzing document elements..."):
                    res = api_post("/v1/annotations/auto-annotate", {
                        "doc_id": doc_id,
                        "enable_insights": enable_insights
                    })
                    if res:
                        counts = res.get("counts", {})
                        st.success(f"""
                        AI Annotations populated:
                        - {counts.get('tags', 0)} Tags created
                        - {counts.get('numerical_flags', 0)} Numerical claims flagged
                        - {counts.get('questions', 0)} Questions suggested
                        - {counts.get('inconsistencies', 0)} Inconsistencies detected
                        - {counts.get('insights', 0)} LLM Insights added
                        """)
                        st.rerun()

        st.markdown("---")
        
        # 4. View and filter annotations
        st.markdown("### 📋 Active Annotations")
        
        # Fetch existing annotations
        anns_response = api_get(f"/v1/annotations/?doc_id={doc_id}")
        annotations = anns_response.get("annotations", []) if anns_response else []
        
        if not annotations:
            st.info("No active annotations for this document.")
            return

        # Simple filters
        st.caption(f"Showing {len(annotations)} annotations")
        
        # Display list of annotations grouped by page
        pages_annotated = sorted(list(set(a["position"]["page"] for a in annotations)))
        
        for p in pages_annotated:
            st.markdown(f"#### Page {p}")
            page_anns = [a for a in annotations if a["position"]["page"] == p]
            
            for a in page_anns:
                color = a.get("color", "#fbbf24")
                atype = a["type"].upper()
                author = a.get("user_id", "default")
                
                # Render card
                st.markdown(
                    f'<div style="border-left: 5px solid {color}; padding: 0.8rem; '
                    f'background-color: rgba(30, 41, 59, 0.4); border-radius: 4px; margin-bottom: 0.5rem">'
                    f'<span style="font-weight:bold; font-size:0.8rem; color:{color}">{atype}</span> '
                    f'<span style="color:#8b95a7; font-size:0.75rem">by {author}</span>'
                    f'<p style="margin: 0.3rem 0; font-size:0.9rem">{a["content"]}</p>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                
                # Action buttons (Resolve/Delete)
                c_act1, c_act2, c_empty = st.columns([1, 1, 4])
                
                if a["status"] != "resolved":
                    if c_act1.button("✓ Resolve", key=f"res_{a['id']}"):
                        api_post(f"/v1/annotations/{a['id']}/resolve")
                        st.rerun()
                else:
                    st.caption("Resolved ✓")
                
                if c_act2.button("🗑️ Delete", key=f"del_{a['id']}"):
                    api_delete(f"/v1/annotations/{a['id']}")
                    st.rerun()
