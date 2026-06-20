"""Build and compile the project agent LangGraph."""

from __future__ import annotations

from langgraph.graph import StateGraph, END

from langgraph_project_agent.nodes import (
    classify_project_type,
    generate_implementation_plan,
    identify_missing_artifacts,
    return_scorecard,
    score_against_portfolio_thesis,
)
from langgraph_project_agent.state import ProjectState


def build_graph() -> StateGraph:
    graph = StateGraph(ProjectState)

    graph.add_node("classify_project_type", classify_project_type)
    graph.add_node("score_against_portfolio_thesis", score_against_portfolio_thesis)
    graph.add_node("identify_missing_artifacts", identify_missing_artifacts)
    graph.add_node("generate_implementation_plan", generate_implementation_plan)
    graph.add_node("return_scorecard", return_scorecard)

    graph.set_entry_point("classify_project_type")
    graph.add_edge("classify_project_type", "score_against_portfolio_thesis")
    graph.add_edge("score_against_portfolio_thesis", "identify_missing_artifacts")
    graph.add_edge("identify_missing_artifacts", "generate_implementation_plan")
    graph.add_edge("generate_implementation_plan", "return_scorecard")
    graph.add_edge("return_scorecard", END)

    return graph


compiled_graph = build_graph().compile()
