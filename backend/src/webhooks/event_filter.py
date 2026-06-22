"""
AMDI-OS Webhook & Event System: Event Filtering
===============================================

Handles topic matching for webhook subscriptions, including support for 
wildcards (e.g. 'document.*', '*').
"""

import re


def match_topic(pattern: str, topic: str) -> bool:
    """
    Checks if a subscription topic pattern matches an actual event topic.
    Supports wildcards:
      - '*' matches everything
      - 'document.*' matches 'document.processed', 'document.failed', etc.
      - 'document.processed' matches exactly 'document.processed'
    """
    pattern = pattern.strip()
    topic = topic.strip()
    
    if pattern == "*":
        return True
        
    if pattern == topic:
        return True

    # Escape all regex characters, then replace wildcard '*' with '.*'
    # Anchor the expression to make sure it matches the entire string.
    escaped_pattern = re.escape(pattern).replace(r"\*", ".*")
    regex_pattern = f"^{escaped_pattern}$"
    
    return bool(re.match(regex_pattern, topic))
