from langchain_core.tools import tool


@tool(parse_docstring=True)
def think_tool(reflection: str) -> str:
    """Tool for strategic reflection on investigation progress and decision-making.

    Use this tool after each investigation stage to analyze results and plan next steps systematically.
    This creates a deliberate pause in the investigation workflow for quality decision-making.

    When to use:
    - After investigating each stage: What key information did I find?
    - Before deciding next steps: Do I have enough to answer comprehensively?
    - When assessing investigation gaps: What specific information am I still missing?
    - Before concluding investigation: Can I provide a complete answer now?

    Reflection should address:
    1. Analysis of current findings - What concrete information have I gathered?
    2. Gap assessment - What crucial information is still missing?
    3. Quality evaluation - Do I have sufficient evidence?
    4. Strategic decision - Should I continue investigating or provide my answer?

    Args:
        reflection: Your detailed reflection on investigation progress, findings, gaps, and next steps

    Returns:
        Confirmation that reflection was recorded for decision-making
    """
    return f"Reflection recorded: {reflection}"
