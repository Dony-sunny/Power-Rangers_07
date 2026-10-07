import json
import asyncio
import time
from fastapi import HTTPException
from backend.auth import cargo_access, permission
from backend.models import CargoRequest, Vessel
from backend.repositories.common import require
from backend.services.planning import compare_modes
from optimization.matching.engine import match
from optimization.pooling.solver import optimize_pool
from optimization.backhaul.search import find_backhaul
from intelligence.document_intake.parser import parse_cargo
from intelligence.provider.llm import provider, ProviderUnavailable


async def broker(db, actor, text, cargo_id=None):
    """LLM-selected bounded tool calls; never delegates physical or financial math."""
    permission(actor, "plan")
    trace = []
    results = {}
    if not cargo_id:
        extraction = await parse_cargo(text)
        return {
            "mode": "llm_intake"
            if extraction["is_ai"]
            else "deterministic_demo_orchestrator",
            "trace": [{"tool": "parse_cargo_text", "status": "completed"}],
            "extraction": extraction,
            "requires_confirmation": True,
        }
    cargo = require(db, CargoRequest, cargo_id)
    cargo_access(actor, cargo)

    async def call(name, args):
        if name == "rank_matches":
            result = match(db, cargo, args.get("profile", "BALANCED"))
        else:
            matched = results.get("rank_matches") or match(db, cargo)
            requested = args.get("vessel_id")
            allowed = {m["vessel_id"] for m in matched["recommendations"]}
            vessel_id = requested or (
                matched["recommendations"][0]["vessel_id"]
                if matched["recommendations"]
                else None
            )
            if requested and requested not in allowed:
                return {
                    "status": "FAIL",
                    "reasons": [
                        "Tool refused an infeasible vessel. The LLM cannot override this failure."
                    ],
                }
            if name == "compare_transport_modes":
                result = compare_modes(db, cargo, vessel_id)
            elif name == "optimize_load_pool" and vessel_id:
                result = optimize_pool(
                    db,
                    cargo,
                    require(db, Vessel, vessel_id),
                    None
                    if actor.role_id in {"admin", "control"}
                    else actor.organization_id,
                    persist=False,
                )
            elif name == "find_backhaul" and vessel_id:
                result = find_backhaul(
                    db, cargo, require(db, Vessel, vessel_id), persist=False
                )
            else:
                return {
                    "status": "FAIL",
                    "reasons": ["Unknown tool or no feasible vessel."],
                }
        results[name] = result
        trace.append(
            {
                "tool": name,
                "status": "completed",
                "source": "deterministic_validated_service",
            }
        )
        return result

    mode = "deterministic_demo_orchestrator"
    warnings = []
    tool_names = [
        "rank_matches",
        "compare_transport_modes",
        "optimize_load_pool",
        "find_backhaul",
    ]
    if provider.configured:
        schemas = [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": "Call the authoritative Jalayatra planning tool. Read-only; does not book.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "vessel_id": {"type": "string"},
                            "profile": {
                                "type": "string",
                                "enum": [
                                    "BALANCED",
                                    "CHEAPEST",
                                    "FASTEST",
                                    "GREENEST",
                                    "MOST_RELIABLE",
                                ],
                            },
                        },
                        "additionalProperties": False,
                    },
                },
            }
            for name in tool_names
        ]
        messages = [
            {
                "role": "system",
                "content": "You are a freight broker. Select only available tools to understand and plan this cargo. Physical feasibility, prices and optimization come only from tools. Never override tool failures or create bookings. Gather rank, modes, pool and backhaul when possible. Cargo ID is scoped by the server.",
            },
            {"role": "user", "content": text},
        ]
        try:
            started = time.monotonic()
            for _ in range(4):
                remaining = 16 - (time.monotonic() - started)
                if remaining <= 0:
                    raise ProviderUnavailable("Broker provider time budget exceeded.")
                turn = await asyncio.wait_for(
                    provider.tool_turn(messages, schemas), timeout=remaining
                )
                calls = turn.get("tool_calls") or []
                if not calls:
                    break
                messages.append(turn)
                for invocation in calls[:4]:
                    name = invocation["function"]["name"]
                    if name not in tool_names:
                        raise ValueError("Unknown tool")
                    args = json.loads(invocation["function"].get("arguments", "{}"))
                    if not isinstance(args, dict) or not set(args) <= {
                        "vessel_id",
                        "profile",
                    }:
                        raise ValueError("Invalid tool arguments")
                    try:
                        output = await call(name, args)
                    except (HTTPException, ValueError) as error:
                        output = {
                            "status": "FAIL",
                            "reasons": [str(getattr(error, "detail", error))],
                        }
                        trace.append({"tool": name, "status": "failed"})
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": invocation["id"],
                            "content": json.dumps(output, ensure_ascii=False),
                        }
                    )
            mode = "llm_tool_orchestration"
        except (ProviderUnavailable, ValueError, KeyError, TypeError, TimeoutError):
            warnings.append(
                "Provider unavailable or invalid tool call; deterministic tool orchestration completed the plan."
            )
    for name in tool_names:
        if name not in results:
            try:
                await call(name, {})
            except HTTPException as error:
                results[name] = {"status": "FAIL", "reasons": [str(error.detail)]}
                trace.append({"tool": name, "status": "failed"})
    return {
        "mode": mode,
        "trace": trace,
        "results": results,
        "warnings": warnings,
        "requires_booking_approval": True,
        "explanation": results.get("compare_transport_modes", {}).get(
            "explanation", "Review the validated tool results."
        ),
    }
