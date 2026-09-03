#!/usr/bin/env python3
"""Demo script for Board Strategy Service"""

import json
from datetime import datetime

from monitoring.services.board_strategy_service import board_strategy


def main():
    print("=" * 60)
    print("BOARD STRATEGY SERVICE DEMO")
    print("=" * 60)

    # Generate board pack for next meeting
    print("\n📋 BOARD MEETING PACK")
    print("-" * 60)
    pack = board_strategy.generate_board_pack(datetime(2025, 2, 15))

    print(f"Meeting Type: {pack['meeting_overview']['meeting_type']}")
    print(f"Date: {pack['meeting_overview']['date']}")
    print(f"Duration: {pack['meeting_overview']['duration']}")
    print(f"Location: {pack['meeting_overview']['location']}")
    print(f"\nBoard Members: {len(pack['attendees']['board_members'])}")
    for member in pack["attendees"]["board_members"]:
        print(f"  • {member}")

    print(f"\nExecutive Team: {len(pack['attendees']['executive_team'])}")
    for member in pack["attendees"]["executive_team"]:
        print(f"  • {member}")

    print(f"\n📊 Decision Items: {len(pack['decision_items'])}")
    for item in pack["decision_items"]:
        print(f"\n  {item['item']}")
        print(f"    ↳ Financial Impact: {item['financial_impact']}")
        print(f"    ↳ {item['recommendation']}")

    # Strategic Roadmap
    print("\n\n🎯 STRATEGIC ROADMAP")
    print("-" * 60)
    roadmap = board_strategy.strategic_roadmap
    print(f"\nStrategic Initiatives: {len(roadmap.strategic_initiatives)}")
    for i, initiative in enumerate(roadmap.strategic_initiatives, 1):
        print(f"  {i}. {initiative}")

    print("\n📅 Quarterly Milestones:")
    for quarter, milestones in roadmap.quarterly_milestones.items():
        print(f"\n  {quarter}:")
        for milestone in milestones:
            print(f"    • {milestone}")

    print("\n💰 Investment Allocation:")
    for category, percentage in roadmap.investment_allocation.items():
        print(f"  • {category.replace('_', ' ').title()}: {percentage*100:.0f}%")

    # Investor Update
    print("\n\n💹 INVESTOR UPDATE")
    print("-" * 60)
    update = board_strategy.generate_investor_update("Q1", 2025)

    print(
        f"\n{update['executive_summary']['quarter']} {update['executive_summary']['year']} {update['executive_summary']['headline']}"
    )
    print("\nKey Highlights:")
    for highlight in update["executive_summary"]["key_highlights"]:
        print(f"  • {highlight}")

    print("\n📈 Financial Performance:")
    financials = update["financial_performance"]
    print(f"  • Quarterly Revenue: ${financials['quarterly_revenue']:,}")
    print(f"  • Annual Recurring Revenue: ${financials['annual_recurring_revenue']:,}")
    print(f"  • Quarterly Growth Rate: {financials['quarterly_growth_rate']}%")
    print(f"  • Annual Growth Rate: {financials['annual_growth_rate']}%")
    print(f"  • Gross Margin: {financials['gross_margin']*100:.0f}%")
    print(f"  • Net Revenue Retention: {financials['net_revenue_retention']*100:.0f}%")

    # Governance Framework
    print("\n\n🏛️  GOVERNANCE FRAMEWORK")
    print("-" * 60)
    governance = board_strategy.governance_framework
    board_structure = governance.board_structure["board_composition"]

    print(f"\nBoard Composition:")
    print(f"  • Total Members: {board_structure['total_members']}")
    print(f"  • Independent Directors: {board_structure['independent_directors']}")
    print(f"  • Founder Representatives: {board_structure['founder_representatives']}")

    print("\nBoard Committees:")
    for committee, details in governance.board_structure["board_committees"].items():
        print(f"\n  {committee.replace('_', ' ').title()}:")
        print(f"    • Purpose: {details['purpose']}")
        print(f"    • Members: {details['members']}")
        print(f"    • Frequency: {details['meeting_frequency']}")
        print(f"    • Chair: {details['chair']}")

    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
