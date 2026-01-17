#!/usr/bin/env python3
"""
Script to update MBTI assessment from 30 to 90 questions
"""

import json

def update_mbti_assessment():
    """Update the MBTI assessment in the API file"""

    # Load the generated questions
    with open('/Users/sheriftito/Downloads/psychsync/mbti_90_questions.json', 'r') as f:
        mbti_questions = json.load(f)

    # Read the current API file
    with open('/Users/sheriftito/Downloads/psychsync/app/api/v1/endpoints/assessment_results.py', 'r') as f:
        content = f.read()

    # Find the MBTI section
    mbti_start = content.find('get_mbti_assessment_questions():')
    if mbti_start == -1:
        print("MBTI assessment function not found!")
        return

    # Find the questions array start
    questions_start = content.find('"questions": [', mbti_start)
    if questions_start == -1:
        print("MBTI questions array not found!")
        return

    # Find the end of the questions array
    questions_end = content.find('            ],\n            "dimensions_info": {', questions_start)
    if questions_end == -1:
        print("End of MBTI questions not found!")
        return

    # Generate the new questions content
    new_questions_content = []

    # Add all 90 questions
    for q in mbti_questions:
        # Properly escape quotes in text
        question_text = q["question_text"].replace('"', '\\"')
        opt1_text = q["options"][0]["text"].replace('"', '\\"')
        opt2_text = q["options"][1]["text"].replace('"', '\\"')

        q_json = f'''
                {{
                    "id": {q["id"]},
                    "question_text": "{question_text}",
                    "dimension": "{q["dimension"]}",
                    "options": [
                        {{"text": "{opt1_text}", "value": "{q["options"][0]["value"]}"}},
                        {{"text": "{opt2_text}", "value": "{q["options"][1]["value"]}"}}
                    ]
                }}'''
        new_questions_content.append(q_json.rstrip())

    # Combine all questions
    all_questions = '"questions": [\n' + ',\n'.join(new_questions_content) + '\n            ]'

    # Replace the questions section in the content
    updated_content = content[:questions_start] + all_questions + content[questions_end:]

    # Write the updated content back to the file
    with open('/Users/sheriftito/Downloads/psychsync/app/api/v1/endpoints/assessment_results.py', 'w') as f:
        f.write(updated_content)

    print(f"✅ Updated MBTI assessment to {len(mbti_questions)} questions!")

if __name__ == "__main__":
    update_mbti_assessment()
