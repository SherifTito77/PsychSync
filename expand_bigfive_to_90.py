#!/usr/bin/env python3
"""
Script to expand Big Five assessment from 30 to 90 questions
18 questions per trait (OCEAN)
"""

def generate_additional_bigfive_questions():
    """Generate 60 additional questions for Big Five assessment"""

    # Additional Openness questions (questions 7-18)
    openness_questions = [
        (7, "I enjoy debating complex philosophical concepts", "Openness"),
        (8, "I seek out new and unconventional experiences", "Openness"),
        (9, "I find abstract theories fascinating", "Openness"),
        (10, "I prefer variety over routine in my daily life", "Openness"),
        (11, "I'm drawn to artistic and creative pursuits", "Openness"),
        (12, "I enjoy exploring different cultural perspectives", "Openness"),
        (13, "I'm comfortable with ambiguity and uncertainty", "Openness"),
        (14, "I like to analyze problems from multiple angles", "Openness"),
        (15, "I'm energized by learning new skills", "Openness"),
        (16, "I appreciate unconventional beauty in art and nature", "Openness"),
        (17, "I enjoy intellectual challenges that stretch my mind", "Openness"),
        (18, "I'm fascinated by how things work at a fundamental level", "Openness")
    ]

    # Additional Conscientiousness questions (questions 7-18)
    conscientiousness_questions = [
        (19, "I always double-check my work for accuracy", "Conscientiousness"),
        (20, "I prefer to plan ahead rather than be spontaneous", "Conscientiousness"),
        (21, "I keep my promises even when it's difficult", "Conscientiousness"),
        (22, "I'm methodical in my approach to tasks", "Conscientiousness"),
        (23, "I feel satisfied when I complete everything on my to-do list", "Conscientiousness"),
        (24, "I prefer organized environments over chaotic ones", "Conscientiousness"),
        (25, "I'm diligent about meeting deadlines", "Conscientiousness"),
        (26, "I pay attention to small details that others might miss", "Conscientiousness"),
        (27, "I believe in doing things right the first time", "Conscientiousness"),
        (28, "I maintain strict standards for myself", "Conscientiousness"),
        (29, "I feel uneasy when my workspace is disorganized", "Conscientiousness"),
        (30, "I prefer structured approaches to problem-solving", "Conscientiousness")
    ]

    # Additional Extraversion questions (questions 7-18)
    extraversion_questions = [
        (31, "I thrive in social situations with many people", "Extraversion"),
        (32, "I prefer working in teams rather than alone", "Extraversion"),
        (33, "I enjoy being the center of attention", "Extraversion"),
        (34, "I feel energized after social gatherings", "Extraversion"),
        (35, "I speak up in group discussions", "Extraversion"),
        (36, "I enjoy meeting new people regularly", "Extraversion"),
        (37, "I prefer active social activities over quiet ones", "Extraversion"),
        (38, "I express my thoughts and feelings openly", "Extraversion"),
        (39, "I enjoy taking leadership roles in groups", "Extraversion"),
        (40, "I feel comfortable striking up conversations with strangers", "Extraversion"),
        (41, "I prefer lively environments over calm ones", "Extraversion"),
        (42, "I enjoy entertaining and engaging others", "Extraversion")
    ]

    # Additional Agreeableness questions (questions 7-18)
    agreeableness_questions = [
        (43, "I prioritize harmony in group settings", "Agreeableness"),
        (44, "I'm quick to help others in need", "Agreeableness"),
        (45, "I avoid arguments and conflicts", "Agreeableness"),
        (46, "I consider others' feelings before acting", "Agreeableness"),
        (47, "I believe most people are fundamentally good", "Agreeableness"),
        (48, "I enjoy doing favors for others", "Agreeableness"),
        (49, "I'm patient with people's shortcomings", "Agreeableness"),
        (50, "I feel empathy for those less fortunate", "Agreeableness"),
        (51, "I prefer cooperation over competition", "Agreeableness"),
        (52, "I'm forgiving when others make mistakes", "Agreeableness"),
        (53, "I avoid criticizing others", "Agreeableness"),
        (54, "I value kindness over being right", "Agreeableness")
    ]

    # Additional Neuroticism questions (questions 7-18)
    neuroticism_questions = [
        (55, "I frequently worry about things that might go wrong", "Neuroticism"),
        (56, "I get upset easily over minor issues", "Neuroticism"),
        (57, "I feel anxious in unfamiliar situations", "Neuroticism"),
        (58, "I'm sensitive to criticism from others", "Neuroticism"),
        (59, "I often feel overwhelmed by stress", "Neuroticism"),
        (60, "I mood can change quickly", "Neuroticism"),
        (61, "I tend to expect the worst outcome", "Neuroticism"),
        (62, "I feel nervous before important events", "Neuroticism"),
        (63, "I get discouraged by setbacks easily", "Neuroticism"),
        (64, "I often feel tense or on edge", "Neuroticism"),
        (65, "I'm easily affected by negative news", "Neuroticism"),
        (66, "I frequently experience self-doubt", "Neuroticism")
    ]

    # Combine all questions
    all_questions = []
    all_questions.extend(openness_questions)
    all_questions.extend(conscientiousness_questions)
    all_questions.extend(extraversion_questions)
    all_questions.extend(agreeableness_questions)
    all_questions.extend(neuroticism_questions)

    return all_questions

def update_bigfive_assessment():
    """Update the Big Five assessment to 90 questions"""

    # Read the current API file
    with open('/Users/sheriftito/Downloads/psychsync/app/api/v1/endpoints/assessment_results.py', 'r') as f:
        content = f.read()

    # Find the Big Five section
    bigfive_start = content.find('get_big_five_assessment_questions():')
    if bigfive_start == -1:
        print("Big Five assessment function not found!")
        return

    # Find the questions array start
    questions_start = content.find('"questions": [', bigfive_start)
    if questions_start == -1:
        print("Big Five questions array not found!")
        return

    # Find the end of the questions array
    questions_end = content.find('            ],\n            "traits_info": {', questions_start)
    if questions_end == -1:
        print("End of Big Five questions not found!")
        return

    # Get additional questions
    additional_questions = generate_additional_bigfive_questions()

    # Generate the new questions content
    new_questions_content = []

    # Get current questions (first 30)
    current_section = content[questions_start:questions_end]
    first_question_start = current_section.find('                {')
    current_questions_text = current_section[first_question_start:]
    new_questions_content.append(current_questions_text.rstrip())

    # Add the additional questions
    for q_id, q_text, trait in additional_questions:
        # Properly escape quotes in text
        question_text = q_text.replace('"', '\\"')

        q_json = f'''
                {{
                    "id": {q_id},
                    "question_text": "{question_text}",
                    "trait": "{trait}",
                    "options": [
                        {{"text": "Strongly Disagree", "value": "1"}},
                        {{"text": "Disagree", "value": "2"}},
                        {{"text": "Neutral", "value": "3"}},
                        {{"text": "Agree", "value": "4"}},
                        {{"text": "Strongly Agree", "value": "5"}}
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

    print(f"✅ Updated Big Five assessment to 90 questions!")
    print(f"   - Added {len(additional_questions)} new questions")
    print(f"   - Total questions: 30 + {len(additional_questions)} = {30 + len(additional_questions)}")

if __name__ == "__main__":
    update_bigfive_assessment()