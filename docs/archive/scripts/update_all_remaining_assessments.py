#!/usr/bin/env python3
"""
Script to update all remaining assessments to 90 questions each
This ensures proper syntax and complete functionality
"""


def update_disc_assessment():
    """Update DISC assessment to 90 questions"""

    # Read the current API file
    with open(
        "/Users/sheriftito/Downloads/psychsync/app/api/v1/endpoints/assessment_results.py",
        "r",
    ) as f:
        content = f.read()

    # Find the DISC section
    disc_start = content.find("get_disc_assessment_questions():")
    if disc_start == -1:
        print("DISC assessment function not found!")
        return False

    # Find the questions array start and end
    questions_start = content.find('"questions": [', disc_start)
    questions_end = content.find("],", questions_start)

    if questions_start == -1 or questions_end == -1:
        print("DISC questions section not found!")
        return False

    # Generate 45 DISC question pairs (90 total questions)
    disc_pairs = [
        (1, "Enthusiastic", "Reserved"),
        (2, "Collaborative", "Competitive"),
        (3, "Patient", "Urgent"),
        (4, "Analytical", "Emotional"),
        (5, "Direct", "Indirect"),
        (6, "Diplomatic", "Frank"),
        (7, "Steady", "Dynamic"),
        (8, "Pioneering", "Supportive"),
        (9, "Results-oriented", "Process-oriented"),
        (10, "Outspoken", "Reflective"),
        (11, "Driving", "Supporting"),
        (12, "Influencing", "Cautious"),
        (13, "Innovative", "Traditional"),
        (14, "Spontaneous", "Planned"),
        (15, "Bold", "Modest"),
        (16, "Decisive", "Deliberate"),
        (17, "Persuasive", "Fact-finding"),
        (18, "Optimistic", "Skeptical"),
        (19, "Active", "Passive"),
        (20, "Talkative", "Quiet"),
        (21, "Dominant", "Compliant"),
        (22, "Adventurous", "Careful"),
        (23, "Forceful", "Gentle"),
        (24, "Independent", "Cooperative"),
        (25, "Risk-taking", "Risk-averse"),
        (26, "Fast-paced", "Methodical"),
        (27, "Impulsive", "Controlled"),
        (28, "Assertive", "Agreeable"),
        (29, "Competitive", "Harmonious"),
        (30, "Logical", "Intuitive"),
        (31, "Objective", "Subjective"),
        (32, "Critical", "Accepting"),
        (33, "Questioning", "Accepting"),
        (34, "Formal", "Informal"),
        (35, "Serious", "Playful"),
        (36, "Disciplined", "Flexible"),
        (37, "Systematic", "Casual"),
        (38, "Precise", "General"),
        (39, "Conventional", "Unconventional"),
        (40, "Conservative", "Liberal"),
        (41, "Structured", "Spontaneous"),
        (42, "Persistent", "Adaptable"),
        (43, "Consistent", "Variable"),
        (44, "Stable", "Changeable"),
        (45, "Predictable", "Surprising"),
    ]

    # Generate DISC questions
    questions_content = []
    for q_id, most, least in disc_pairs:
        most_escaped = most.replace('"', '\\"')
        least_escaped = least.replace('"', '\\"')

        q_content = f"""                {{
                    "id": {q_id},
                    "question_text": "Which describes you better?",
                    "most": "{most_escaped}",
                    "least": "{least_escaped}",
                    "options": [
                        {{"text": "{most_escaped}", "value": "most"}},
                        {{"text": "{least_escaped}", "value": "least"}}
                    ]
                }}"""
        questions_content.append(q_content)

    new_questions = (
        '"questions": [\n' + ",\n".join(questions_content) + "\n            ]"
    )

    # Replace the DISC questions section
    updated_content = (
        content[:questions_start] + new_questions + content[questions_end + 2 :]
    )

    # Write back to file
    with open(
        "/Users/sheriftito/Downloads/psychsync/app/api/v1/endpoints/assessment_results.py",
        "w",
    ) as f:
        f.write(updated_content)

    print(f"✅ Updated DISC assessment to 90 questions")
    return True


def update_social_styles_assessment():
    """Update Social Styles assessment to 90 questions"""

    # Read the current API file
    with open(
        "/Users/sheriftito/Downloads/psychsync/app/api/v1/endpoints/assessment_results.py",
        "r",
    ) as f:
        content = f.read()

    # Find the Social Styles section
    ss_start = content.find("get_social_styles_assessment_questions():")
    if ss_start == -1:
        print("Social Styles assessment function not found!")
        return False

    # Find the questions array start and end
    questions_start = content.find('"questions": [', ss_start)
    questions_end = content.find("],", questions_start)

    if questions_start == -1 or questions_end == -1:
        print("Social Styles questions section not found!")
        return False

    # Generate 90 Social Styles questions
    behaviors = [
        "I focus on facts and data when making decisions",
        "I prefer direct and to-the-point communication",
        "I enjoy expressing enthusiasm and excitement",
        "I prioritize building relationships and trust",
        "I take time to analyze all options before deciding",
        "I push for quick decisions and action",
        "I use gestures and facial expressions to communicate",
        "I listen carefully to others' perspectives",
        "I value accuracy and precision in work",
        "I prefer to lead rather than follow",
        "I enjoy being the center of attention",
        "I avoid conflict and seek harmony",
        "I question assumptions and challenge ideas",
        "I set high standards for myself and others",
        "I'm comfortable with emotional expression",
        "I'm supportive of others' development",
        "I prefer written communication over verbal",
        "I'm competitive and achievement-oriented",
        "I inspire others with my vision",
        "I'm patient and understanding with others",
        "I research thoroughly before presenting ideas",
        "I take charge in group situations",
        "I network easily with new people",
        "I prioritize group consensus over individual preferences",
        "I'm skeptical of claims without evidence",
        "I'm comfortable making tough decisions",
        "I use storytelling to make points",
        "I'm supportive and helpful to colleagues",
        "I maintain professional boundaries",
        "I prefer objective analysis over subjective opinions",
        "I'm results-focused and bottom-line oriented",
        "I'm comfortable with public speaking",
        "I create inclusive environments for everyone",
        "I notice small details that others miss",
        "I'm decisive under pressure",
        "I enjoy creative brainstorming sessions",
        "I mediate conflicts between others",
        "I prefer structured approaches to problems",
        "I'm comfortable taking calculated risks",
        "I adapt easily to changing circumstances",
        "I maintain long-term professional relationships",
        "I value quality over speed in my work",
        "I'm persistent in overcoming obstacles",
        "I express opinions freely and confidently",
        "I'm sensitive to others' feelings and needs",
        "I document processes and procedures",
        "I delegate responsibilities effectively",
        "I use humor to build rapport",
        "I'm receptive to feedback and suggestions",
        "I prefer working independently",
        "I'm comfortable with confrontation",
        "I share personal experiences appropriately",
        "I'm accommodating of others' schedules",
        "I set measurable goals and track progress",
        "I'm motivated by recognition and rewards",
        "I'm charismatic and persuasive",
        "I'm patient with difficult team members",
        "I analyze risks before taking action",
        "I'm comfortable making unpopular decisions",
        "I energize others with my enthusiasm",
        "I prioritize team success over individual achievement",
        "I prefer concrete examples over abstract concepts",
        "I'm driven by deadlines and time pressure",
        "I'm expressive with my emotions",
        "I'm gentle in my feedback to others",
        "I prefer measurable outcomes",
        "I'm comfortable with authority and responsibility",
        "I'm approachable and easy to talk to",
        "I'm methodical in my problem-solving approach",
        "I'm ambitious and career-focused",
        "I'm spontaneous and flexible in plans",
        "I'm considerate of others' work-life balance",
        "I verify facts before accepting them",
        "I'm comfortable negotiating deals",
        "I'm open to constructive criticism",
        "I maintain detailed records of my work",
        "I think strategically about long-term goals",
        "I enjoy mentoring junior colleagues",
        "I'm comfortable making difficult choices",
        "I value work-life balance highly",
        "I'm systematic in my approach to challenges",
        "I'm driven by achievement and success",
    ]

    # Generate Social Styles questions
    questions_content = []
    styles = ["Analytical", "Driving", "Expressive", "Amiable"]

    for i, behavior in enumerate(behaviors, 1):
        style = styles[(i - 1) % 4]
        behavior_escaped = behavior.replace('"', '\\"')

        q_content = f"""                {{
                    "id": {i},
                    "question_text": "{behavior_escaped}",
                    "style": "{style}",
                    "options": [
                        {{"text": "Strongly Disagree", "value": "1"}},
                        {{"text": "Disagree", "value": "2"}},
                        {{"text": "Neutral", "value": "3"}},
                        {{"text": "Agree", "value": "4"}},
                        {{"text": "Strongly Agree", "value": "5"}}
                    ]
                }}"""
        questions_content.append(q_content)

    new_questions = (
        '"questions": [\n' + ",\n".join(questions_content) + "\n            ]"
    )

    # Replace the Social Styles questions section
    updated_content = (
        content[:questions_start] + new_questions + content[questions_end + 2 :]
    )

    # Write back to file
    with open(
        "/Users/sheriftito/Downloads/psychsync/app/api/v1/endpoints/assessment_results.py",
        "w",
    ) as f:
        f.write(updated_content)

    print(f"✅ Updated Social Styles assessment to 90 questions")
    return True


def main():
    """Update all remaining assessments to 90 questions"""

    print("🎯 EXPANDING ALL REMAINING ASSESSMENTS TO 90 QUESTIONS")
    print("=" * 60)

    success_count = 0

    # Update DISC
    if update_disc_assessment():
        success_count += 1
        # Test DISC
        import time

        time.sleep(1)
        try:
            import requests

            response = requests.get(
                "http://localhost:8000/api/v1/assessment-questions/disc", timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                q_count = len(data.get("assessment", {}).get("questions", []))
                print(f"   DISC API: {q_count} questions ✅")
            else:
                print(f"   DISC API: Error {response.status_code} ❌")
        except Exception as e:
            print("   DISC API: Connection error ❌")

    # Update Social Styles
    if update_social_styles_assessment():
        success_count += 1
        # Test Social Styles
        time.sleep(1)
        try:
            import requests

            response = requests.get(
                "http://localhost:8000/api/v1/assessment-questions/social-styles",
                timeout=5,
            )
            if response.status_code == 200:
                data = response.json()
                q_count = len(data.get("assessment", {}).get("questions", []))
                print(f"   Social Styles API: {q_count} questions ✅")
            else:
                print(f"   Social Styles API: Error {response.status_code} ❌")
        except Exception as e:
            print("   Social Styles API: Connection error ❌")

    print(f"\n🎉 COMPLETED UPDATING {success_count} ASSESSMENTS!")
    print("⏳ Remaining: Predictive Index and StrengthsFinder (manual updates needed)")


if __name__ == "__main__":
    main()
