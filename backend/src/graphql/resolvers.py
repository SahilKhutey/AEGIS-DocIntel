"""
AMDI-OS GraphQL API: Resolvers and Query Engine
===============================================

Parses GraphQL queries, matches them to resolvers (Queries, Mutations, 
and Subscriptions), and uses DataLoaders to prevent N+1 query patterns.
"""

import re
import asyncio
from typing import Dict, List, Any, Optional, Union, Callable, Awaitable
from .dataloader import DataLoader
from .schema import PERSISTED_QUERIES


# Mock authors db
AUTHORS_DB = {
    "auth_1": {"id": "auth_1", "name": "Alice Vance", "role": "Senior Engineer"},
    "auth_2": {"id": "auth_2", "name": "Bob Vance", "role": "VP Analytics"},
}


class FieldNode:
    """
    AST node for a parsed GraphQL field selection.
    """
    def __init__(self, name: str, args: Optional[Dict[str, Any]] = None, selections: Optional[List["FieldNode"]] = None):
        self.name = name
        self.args = args or {}
        self.selections = selections or []


class Lexer:
    """
    Simple token generator for GraphQL query syntax.
    """
    def __init__(self, query: str):
        token_specification = [
            ("VAR",      r"\$[a-zA-Z_][a-zA-Z0-9_]*"),
            ("NUMBER",   r"-?\d+(\.\d+)?"),
            ("STRING",   r'"[^"\\]*(?:\\.[^"\\]*)*"'),
            ("NAME",     r"[a-zA-Z_][a-zA-Z0-9_]*"),
            ("BRACE_L",  r"\{"),
            ("BRACE_R",  r"\}"),
            ("PAREN_L",  r"\("),
            ("PAREN_R",  r"\)"),
            ("COLON",    r":"),
            ("SKIP",     r"[ \t\r\n,!]+"),  # Skip spaces, commas, and exclamation marks
            ("MISMATCH", r"."),
        ]
        tok_regex = "|".join(f"(?P<{name}>{pattern})" for name, pattern in token_specification)
        self.tokens = []
        for mo in re.finditer(tok_regex, query):
            kind = mo.lastgroup
            value = mo.group()
            if kind == "SKIP":
                continue
            elif kind == "MISMATCH":
                raise SyntaxError(f"Unexpected character: {value}")
            self.tokens.append((kind, value))
        self.pos = 0

    def peek(self) -> Optional[tuple]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def next(self) -> tuple:
        tok = self.peek()
        self.pos += 1
        return tok

    def expect(self, kind: str) -> str:
        tok = self.next()
        if not tok or tok[0] != kind:
            raise SyntaxError(f"Expected token type '{kind}', got '{tok}'")
        return tok[1]


class GraphQLParser:
    """
    Parses token stream into a list of FieldNode AST nodes.
    """
    def __init__(self, lexer: Lexer):
        self.lexer = lexer

    def parse(self) -> List[FieldNode]:
        tok = self.lexer.peek()
        if not tok:
            return []

        # Consume outer metadata: query/mutation keyword, operation name, and variable list
        if tok[0] == "NAME" and tok[1] in ("query", "mutation", "subscription"):
            self.lexer.next()
            # Consume optional operation name
            next_tok = self.lexer.peek()
            if next_tok and next_tok[0] == "NAME":
                self.lexer.next()
            # Consume variable definitions list: e.g. ($id: ID!)
            next_tok = self.lexer.peek()
            if next_tok and next_tok[0] == "PAREN_L":
                self.lexer.expect("PAREN_L")
                while self.lexer.peek() and self.lexer.peek()[0] != "PAREN_R":
                    self.lexer.next()
                self.lexer.expect("PAREN_R")

        self.lexer.expect("BRACE_L")
        selections = self.parse_selections()
        self.lexer.expect("BRACE_R")
        return selections

    def parse_selections(self) -> List[FieldNode]:
        selections = []
        while True:
            tok = self.lexer.peek()
            if not tok or tok[0] == "BRACE_R":
                break

            field_name = self.lexer.expect("NAME")
            args = {}

            # Parse arguments: e.g. (id: "tenant_abc")
            next_tok = self.lexer.peek()
            if next_tok and next_tok[0] == "PAREN_L":
                self.lexer.expect("PAREN_L")
                while True:
                    name = self.lexer.expect("NAME")
                    self.lexer.expect("COLON")
                    val_tok = self.lexer.next()
                    val = val_tok[1]
                    if val_tok[0] == "STRING":
                        val = val[1:-1]  # strip quotes
                    elif val_tok[0] == "NUMBER":
                        val = float(val) if "." in val else int(val)
                    elif val_tok[0] == "VAR":
                        val = val_tok[1]  # Keep var reference string
                    args[name] = val

                    peek_tok = self.lexer.peek()
                    if peek_tok and peek_tok[0] == "PAREN_R":
                        break
                self.lexer.expect("PAREN_R")

            # Parse nested selection block
            sub_selections = []
            next_tok = self.lexer.peek()
            if next_tok and next_tok[0] == "BRACE_L":
                self.lexer.expect("BRACE_L")
                sub_selections = self.parse_selections()
                self.lexer.expect("BRACE_R")

            selections.append(FieldNode(field_name, args, sub_selections))
        return selections


class GraphQLEngine:
    """
    Executes a parsed GraphQL AST, running resolvers and binding variables.
    """
    def __init__(self, tenant_manager, tenant_billing, analytics_engine):
        self.tenant_manager = tenant_manager
        self.tenant_billing = tenant_billing
        self.analytics_engine = analytics_engine
        
        # DataLoader stats
        self.author_batch_calls = 0
        self.author_loader = DataLoader(self._batch_load_authors)

    async def _batch_load_authors(self, author_ids: List[str]) -> List[Optional[Dict[str, Any]]]:
        """
        DataLoader batch fetch function. Increments counter to prove batching happens.
        """
        self.author_batch_calls += 1
        # Fetch authors matching the keys
        return [AUTHORS_DB.get(aid) for aid in author_ids]

    def _resolve_variables(self, args: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Replaces variable placeholder keys (e.g. '$id') with actual parameter values.
        """
        resolved = {}
        for k, v in args.items():
            if isinstance(v, str) and v.startswith("$"):
                var_key = v[1:]
                resolved[k] = variables.get(var_key)
            else:
                resolved[k] = v
        return resolved

    async def execute(self, query: str, variables: Optional[Dict[str, Any]] = None, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes query/mutation string with variables.
        """
        variables = variables or {}
        
        # 1. Resolve Persisted Queries
        # If query is a hash registered in PERSISTED_QUERIES, swap it with the actual query
        if query in PERSISTED_QUERIES:
            query = PERSISTED_QUERIES[query]
        elif query.strip().startswith("sha256_"):
            return {
                "data": None,
                "errors": [{"message": "PersistedQueryNotFound"}]
            }

        try:
            lexer = Lexer(query)
            parser = GraphQLParser(lexer)
            selections = parser.parse()
            
            # Execute root fields
            data = {}
            for selection in selections:
                resolved_args = self._resolve_variables(selection.args, variables)
                data[selection.name] = await self._resolve_field(selection.name, resolved_args, selection.selections)
                
            return {"data": data}
        except Exception as e:
            return {
                "data": None,
                "errors": [{"message": str(e)}]
            }

    async def _resolve_field(self, field_name: str, args: Dict[str, Any], selections: List[FieldNode]) -> Any:
        """
        Root level field resolvers.
        """
        # --- QUERIES ---
        if field_name == "tenant":
            tenant_id = args.get("id")
            tenant = self.tenant_manager.get_tenant(tenant_id)
            if not tenant:
                return None
            return await self._resolve_object({
                "id": tenant.tenant_id,
                "name": tenant.name,
                "plan": tenant.plan.value,
                "status": tenant.status.value,
                "region": tenant.region,
                "billing_email": tenant.billing_email,
                "contact_name": tenant.contact_name,
            }, selections)

        elif field_name == "documents":
            # Simulate fetching documents belonging to tenant
            docs = [
                {"id": "doc_1", "title": "Math Theory", "author_id": "auth_1"},
                {"id": "doc_2", "title": "Data Structures", "author_id": "auth_2"},
                {"id": "doc_3", "title": "Neural Nets", "author_id": "auth_1"},
            ]
            
            # Resolve nested selections for list
            tasks = [self._resolve_object(doc, selections) for doc in docs]
            return await asyncio.gather(*tasks)

        elif field_name == "analytics":
            tenant_id = args.get("tenant_id")
            # Pull metrics
            usage = self.tenant_billing.get_current_period_usage(tenant_id)
            recs = self.analytics_engine.cost_optimizer.get_all_recommendations()
            ctr = self.analytics_engine.behavior_manager.calculate_ctr()
            mrr = self.analytics_engine.behavior_manager.calculate_mrr()
            
            report = {
                "total_documents": int(usage.get("documents_processed", 0)),
                "click_through_rate": ctr,
                "mean_reciprocal_rank": mrr,
                "monthly_savings_usd": sum(r.get("estimated_monthly_savings_usd", 0.0) for r in recs)
            }
            return await self._resolve_object(report, selections)

        # --- MUTATIONS ---
        elif field_name == "createTenant":
            name = args.get("name")
            plan_str = args.get("plan", "starter").upper()
            from backend.src.multitenancy.tenant_manager import TenantPlan
            plan = TenantPlan[plan_str] if plan_str in TenantPlan.__members__ else TenantPlan.STARTER
            email = args.get("email")
            
            tenant = self.tenant_manager.create_tenant(name=name, plan=plan, billing_email=email)
            return await self._resolve_object({
                "id": tenant.tenant_id,
                "name": tenant.name,
                "plan": tenant.plan.value,
                "status": tenant.status.value,
            }, selections)

        elif field_name == "recordUsage":
            tenant_id = args.get("tenant_id")
            metric_name = args.get("metric").upper()
            qty = args.get("quantity")
            
            from backend.src.multitenancy.tenant_billing import UsageMetric
            metric = UsageMetric[metric_name] if metric_name in UsageMetric.__members__ else UsageMetric.QUERIES
            self.tenant_billing.record(tenant_id, metric, qty)
            return True

        # --- SUBSCRIPTIONS ---
        elif field_name == "onEventTriggered":
            # For subscriptions, return a simulated asynchronous generator
            async def event_generator():
                for i in range(3):
                    await asyncio.sleep(0.01)
                    yield {
                        "id": f"evt_sub_{i}",
                        "topic": "document.processed",
                        "timestamp": 1234567.0
                    }
            return event_generator()

        raise KeyError(f"Unknown root field: {field_name}")

    async def _resolve_object(self, obj: Dict[str, Any], selections: List[FieldNode]) -> Dict[str, Any]:
        """
        Resolves sub-selections of an object, supporting nested fields like 'author' (with DataLoader).
        """
        resolved = {}
        for sel in selections:
            if sel.name == "author":
                # Prevent N+1: load via author_loader
                author_id = obj.get("author_id")
                if author_id:
                    # Async loader fetch
                    author_obj = await self.author_loader.load(author_id)
                    resolved["author"] = await self._resolve_object(author_obj, sel.selections) if author_obj else None
                else:
                    resolved["author"] = None
            elif sel.selections:
                # Nested object resolution (not loaded via DataLoader)
                nested = obj.get(sel.name)
                resolved[sel.name] = await self._resolve_object(nested, sel.selections) if nested else None
            else:
                resolved[sel.name] = obj.get(sel.name)
        return resolved
