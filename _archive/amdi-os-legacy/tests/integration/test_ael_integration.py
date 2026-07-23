'''
AEGIS-AEL — Agent Export Layer Integration Tests
==================================================
Tests end-to-end UEO construction, agent routing, verification,
and REST API schema integration.
'''
from __future__ import annotations

import pytest

try:
    from fastapi.testclient import TestClient
    HAS_TEST_CLIENT = True
except ImportError:
    HAS_TEST_CLIENT = False

from src.api.api_server import app


@pytest.mark.skipif(not HAS_TEST_CLIENT, reason='FastAPI TestClient not available')
def test_ael_query_integration():
    with TestClient(app) as client:
        # 1. Ingest dummy document
        raw_content = (
            '# Document Title\n\n'
            'This is paragraph 1. It contains some text.\n\n'
            '| Column A | Column B |\n'
            '|---|---|\n'
            '| Value 1 | 100 |\n'
            '| Value 2 | 200 |\n\n'
            'Section 2:\n'
            'Operating expenses grew by 12% [page 1].'
        )
        
        response = client.post(
            '/ingest',
            files={'file': ('report.md', raw_content.encode('utf-8'), 'text/markdown')}
        )
        assert response.status_code == 201
        stats = response.json()
        doc_id = stats['doc_id']
        assert doc_id is not None
        assert stats['tables'] == 1
        
        # 2. Query with AEL agent export
        query_payload = {
            'question': 'What is the value in Column B and expenses growth?',
            'doc_id': doc_id,
            'export_agent': 'chatgpt',
            'export_format': 'json',
            'top_k': 5
        }
        
        from unittest.mock import patch, AsyncMock
        mock_send = AsyncMock(return_value={
            'agent': 'chatgpt',
            'model': 'gpt-4o',
            'answer': 'According to the report, Column B has 100 and expenses grew by 12% [page 1].',
            'input_tokens': 100,
            'output_tokens': 50,
        })
        with patch('src.ael.connectors.chatgpt.ChatGPTConnector.send', mock_send):
            q_resp = client.post('/query', json=query_payload)
            assert q_resp.status_code == 200
            res_data = q_resp.json()
        
        assert res_data['question'] == query_payload['question']
        assert len(res_data['answer']) > 0
        assert 'citations' in res_data
        assert 'confidence' in res_data
        assert 'grounded' in res_data
        assert res_data['model'] == 'gpt-4o'  # default ChatGPT model
        
        # 3. Export document UEO directly (JSON format)
        export_resp_json = client.get(f'/documents/{doc_id}/export?format=json')
        assert export_resp_json.status_code == 200
        ueo_json = export_resp_json.json()
        
        assert 'ueo_id' in ueo_json
        assert ueo_json['metadata']['document_name'] == 'report.md'
        assert ueo_json['metadata']['total_tables'] == 1
        assert len(ueo_json['matrix']['tables']) == 1
        
        # Check computed metrics exist
        table_meta = ueo_json['matrix']['tables'][0]
        assert 'computed_metrics' in table_meta
        
        # 4. Export document UEO (Markdown format)
        export_resp_md = client.get(f'/documents/{doc_id}/export?format=markdown')
        assert export_resp_md.status_code == 200
        ueo_md = export_resp_md.text
        
        assert '# report.md' in ueo_md or '# Document Title' in ueo_md
        assert '## Document Metadata' in ueo_md
        assert '## Tables' in ueo_md
        assert '## Confidence' in ueo_md
