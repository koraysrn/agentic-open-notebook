"""Default agent definitions.

The initial set mirrors PROJE MİMARİSİ.md. Tool names listed here are resolved
against the tool registry at run time (Road_Map Step 4); referencing a tool
that is not yet registered is a configuration error, not a registration one.
"""

from open_notebook.agents.agent import Agent

DEFAULT_AGENTS: list[Agent] = [
    Agent(
        name="orchestrator",
        description="Plans and routes user goals to specialized agents and tools.",
        capabilities=["planning", "routing"],
        tools=[],
        system_prompt="You decompose a user goal into concrete agent/tool steps.",
    ),
    Agent(
        name="research",
        description="Investigates topics across the knowledge base and external sources.",
        capabilities=["research", "search"],
        tools=["list_notebooks", "search_sources", "get_source_content", "list_notes"],
        system_prompt="You gather and synthesize evidence from available sources.",
    ),
    Agent(
        name="education",
        description="Builds study plans, explanations, quizzes, and flashcards.",
        capabilities=["education", "study"],
        tools=["get_source_content", "list_notes"],
        system_prompt="You turn source material into structured learning artifacts.",
    ),
    Agent(
        name="presentation",
        description="Produces slide outlines and speaker notes.",
        capabilities=["presentation", "content"],
        tools=["get_source_content"],
        system_prompt="You structure information into a presentation flow.",
    ),
    Agent(
        name="report",
        description="Synthesizes structured, source-cited reports.",
        capabilities=["report", "content"],
        tools=["search_sources", "get_source_content"],
        system_prompt="You produce reports where every claim is traceable to a source.",
    ),
    Agent(
        name="podcast",
        description="Generates podcast briefings and transcripts.",
        capabilities=["podcast", "audio"],
        tools=["get_source_content"],
        system_prompt="You convert source material into a conversational audio script.",
    ),
    Agent(
        name="fact_checker",
        description="Verifies claims against available evidence.",
        capabilities=["verification", "control"],
        tools=["search_sources", "get_source_content"],
        system_prompt="You check each claim and label unsupported statements explicitly.",
    ),
    Agent(
        name="control",
        description="Enforces evidence, citation, and hallucination checks on outputs.",
        capabilities=["control", "verification"],
        tools=[],
        system_prompt="You audit an output and tag verified, external, inferred, or unverified claims.",
    ),
    Agent(
        name="persona",
        description="Reinterprets information from a chosen expert perspective.",
        capabilities=["persona", "analysis"],
        tools=["get_source_content"],
        system_prompt="You reframe source facts for a specific audience without changing them.",
    ),
    Agent(
        name="action",
        description="Turns approved outputs into external actions.",
        capabilities=["action", "integration"],
        tools=[],
        system_prompt="You draft external actions that require explicit user approval to execute.",
    ),
]
