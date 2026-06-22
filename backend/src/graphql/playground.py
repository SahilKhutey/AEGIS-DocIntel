"""
AMDI-OS GraphQL API: Interactive Playground
============================================

Serves the HTML/JS resources for the GraphiQL interactive playground interface,
allowing interactive testing of queries, mutations, and variables.
"""

from fastapi.responses import HTMLResponse


def get_playground_html(graphql_endpoint: str = "/graphql") -> HTMLResponse:
    """
    Returns an HTML page running the GraphiQL IDE, pointing to the designated endpoint.
    """
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <title>AMDI-OS GraphQL Playground</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <!-- GraphiQL CSS -->
    <link href="https://unpkg.com/graphiql/graphiql.min.css" rel="stylesheet" />
    <style>
        body {{
            margin: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            background-color: #0b0f19;
            font-family: system-ui, -apple-system, sans-serif;
        }}
        #graphiql {{
            height: 100vh;
        }}
        /* Dark Theme enhancements for premium aesthetic */
        .graphiql-container {{
            background: #0d1117 !important;
        }}
        .topBar {{
            background: #161b22 !important;
            border-bottom: 1px solid #30363d !important;
        }}
    </style>
</head>
<body>
    <div id="graphiql">Loading Playground...</div>

    <!-- React and GraphiQL Dependencies -->
    <script crossorigin src="https://unpkg.com/react@17/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@17/umd/react-dom.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/graphiql/graphiql.min.js"></script>

    <script>
        const fetcher = GraphiQL.createFetcher({{ url: '{graphql_endpoint}' }});
        ReactDOM.render(
            React.createElement(GraphiQL, {{ 
                fetcher: fetcher,
                defaultVariableEditorOpen: true,
                headerEditorEnabled: true
            }}),
            document.getElementById('graphiql')
        );
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content, status_code=200)
