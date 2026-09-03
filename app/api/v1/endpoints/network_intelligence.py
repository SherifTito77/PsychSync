"""Network Intelligence API — 8 structural signals from relationship metadata."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

router = APIRouter(prefix="/network-intelligence", tags=["Network Intelligence"])


async def _load_network(db: AsyncSession, org_id: str):
    """Load network nodes and edges for an organization."""
    from sqlalchemy import select, text

    from app.services.network_intelligence import NetworkEdge, NetworkNode

    nodes: list[NetworkNode] = []
    edges: list[NetworkEdge] = []

    # Load users as nodes
    try:
        result = await db.execute(
            text(
                "SELECT u.id, u.email, tm.team_id "
                "FROM users u "
                "LEFT JOIN team_members tm ON tm.user_id = u.id "
                "WHERE u.organization_id = :oid"
            ),
            {"oid": org_id},
        )
        for row in result.fetchall():
            nodes.append(
                NetworkNode(
                    id=str(row[0]),
                    email=row[1] or "",
                    team_id=str(row[2]) if row[2] else None,
                    department=None,
                    role=None,
                )
            )
    except Exception:
        pass

    # Load collaboration edges from network_edges table (ONA)
    try:
        result = await db.execute(
            text(
                "SELECT source_user_id, target_user_id, weight, edge_type "
                "FROM network_edges "
                "WHERE organization_id = :oid"
            ),
            {"oid": org_id},
        )
        for row in result.fetchall():
            edges.append(
                NetworkEdge(
                    source=str(row[0]),
                    target=str(row[1]),
                    weight=float(row[2]) if row[2] else 0.5,
                    edge_type=row[3] or "collaboration",
                )
            )
    except Exception:
        pass

    return nodes, edges


@router.get("/{org_id}/analysis")
async def get_network_analysis(org_id: str, db: AsyncSession = Depends(get_db)):
    """Full 8-signal network intelligence analysis."""
    from dataclasses import asdict

    from app.services.network_intelligence import NetworkIntelligenceEngine

    nodes, edges = await _load_network(db, org_id)
    if not nodes:
        return {
            "org_id": org_id,
            "node_count": 0,
            "edge_count": 0,
            "density": 0,
            "health_score": 100,
            "signals": [],
            "team_interaction_matrix": {},
        }

    engine = NetworkIntelligenceEngine()
    analysis = engine.analyze(nodes, edges)
    return asdict(analysis)


@router.get("/{org_id}/signals")
async def get_network_signals(
    org_id: str,
    signal_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get specific network signals, optionally filtered by type."""
    from dataclasses import asdict

    from app.services.network_intelligence import NetworkIntelligenceEngine

    nodes, edges = await _load_network(db, org_id)
    engine = NetworkIntelligenceEngine()
    analysis = engine.analyze(nodes, edges)

    signals = [asdict(s) for s in analysis.signals]
    if signal_type:
        signals = [s for s in signals if s["signal_type"] == signal_type]
    return {"org_id": org_id, "signals": signals}


@router.get("/{org_id}/team-interaction-matrix")
async def get_team_interactions(org_id: str, db: AsyncSession = Depends(get_db)):
    """Cross-team interaction density matrix."""
    from dataclasses import asdict

    from app.services.network_intelligence import NetworkIntelligenceEngine

    nodes, edges = await _load_network(db, org_id)
    engine = NetworkIntelligenceEngine()
    analysis = engine.analyze(nodes, edges)
    return {
        "org_id": org_id,
        "matrix": analysis.team_interaction_matrix,
        "node_count": analysis.node_count,
        "edge_count": analysis.edge_count,
        "density": analysis.density,
    }


@router.get("/{org_id}/health")
async def get_network_health(org_id: str, db: AsyncSession = Depends(get_db)):
    """Network health score with breakdown."""
    from dataclasses import asdict

    from app.services.network_intelligence import NetworkIntelligenceEngine

    nodes, edges = await _load_network(db, org_id)
    engine = NetworkIntelligenceEngine()
    analysis = engine.analyze(nodes, edges)

    severity_counts = {}
    for s in analysis.signals:
        severity_counts[s.severity] = severity_counts.get(s.severity, 0) + 1

    return {
        "org_id": org_id,
        "health_score": analysis.health_score,
        "signal_count": len(analysis.signals),
        "severity_breakdown": severity_counts,
        "density": analysis.density,
        "node_count": analysis.node_count,
        "edge_count": analysis.edge_count,
    }
