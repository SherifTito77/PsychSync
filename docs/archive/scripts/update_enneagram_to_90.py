#!/usr/bin/env python3
"""
Script to update the Enneagram assessment to 90 questions
"""

import re


def update_enneagram_assessment():
    """Update the Enneagram assessment in the API file"""

    # Read the current API file
    with open(
        "/Users/sheriftito/Downloads/psychsync/app/api/v1/endpoints/assessment_results.py",
        "r",
    ) as f:
        content = f.read()

    # Import the additional questions
    import sys

    sys.path.append("/Users/sheriftito/Downloads/psychsync")
    from expand_enneagram_to_90 import generate_additional_enneagram_questions

    additional_questions = generate_additional_enneagram_questions()

    # Find the Enneagram section
    enneagram_start = content.find("get_enneagram_assessment_questions():")
    if enneagram_start == -1:
        print("Enneagram assessment function not found!")
        return

    # Find the questions array start
    questions_start = content.find('"questions": [', enneagram_start)
    if questions_start == -1:
        print("Enneagram questions array not found!")
        return

    # Find the end of the questions array (the closing bracket before types_info)
    questions_end = content.find(
        '            ],\n            "types_info": {', questions_start
    )
    if questions_end == -1:
        print("End of Enneagram questions not found!")
        return

    # Generate the new questions content
    new_questions_content = []

    # Get current questions (first 30)
    current_section = content[questions_start:questions_end]

    # Find where the actual questions start (after the opening bracket)
    first_question_start = current_section.find("                {")
    current_questions_text = current_section[first_question_start:]

    new_questions_content.append(current_questions_text.rstrip())

    # Add the additional questions
    for q in additional_questions:
        # Properly escape quotes in text
        question_text = q["question_text"].replace('"', '\\"')
        opt1_text = q["options"][0]["text"].replace('"', '\\"')
        opt2_text = q["options"][1]["text"].replace('"', '\\"')

        q_json = f"""
                {{
                    "id": {q["id"]},
                    "question_text": "{question_text}",
                    "type": "{q["type"]}",
                    "options": [
                        {{"text": "{opt1_text}", "value": "{q["options"][0]["value"]}"}},
                        {{"text": "{opt2_text}", "value": "{q["options"][1]["value"]}"}}
                    ]
                }}"""
        new_questions_content.append(q_json.rstrip())

    # Combine all questions
    all_questions = (
        '"questions": [\n' + ",\n".join(new_questions_content) + "\n            ]"
    )

    # Replace the questions section in the content
    updated_content = (
        content[:questions_start] + all_questions + content[questions_end:]
    )

    # Write the updated content back to the file
    with open(
        "/Users/sheriftito/Downloads/psychsync/app/api/v1/endpoints/assessment_results.py",
        "w",
    ) as f:
        f.write(updated_content)

    print(f"✅ Updated Enneagram assessment to 90 questions!")
    print(f"   - Added {len(additional_questions)} new questions")
    print(
        f"   - Total questions: 30 + {len(additional_questions)} = {30 + len(additional_questions)}"
    )


if __name__ == "__main__":
    update_enneagram_assessment()
