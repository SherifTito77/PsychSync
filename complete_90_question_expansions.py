#!/usr/bin/env python3
"""
Complete 90-question expansions for all personality assessments
This script properly adds all questions with correct syntax
"""

def generate_complete_mbti_questions():
    """Generate complete 90 MBTI questions"""

    # E-I Questions (23)
    ei_questions = [
        (1, "At social gatherings, I:", "Energize by interacting with many people", "Energize by having meaningful conversations with a few people"),
        (2, "When I'm tired, I:", "Feel energized by being with others", "Need quiet time alone to recharge"),
        (3, "I prefer to:", "Talk through problems with others", "Think through problems alone"),
        (4, "In meetings, I tend to:", "Speak up frequently and readily", "Listen more than I speak"),
        (5, "My ideal weekend involves:", "Social activities with friends", "Quiet activities alone or with close family"),
        (6, "I work best:", "With people around me", "In a quiet environment by myself"),
        (7, "When making decisions, I:", "Like to talk things through", "Prefer to reflect internally"),
        (8, "I feel most comfortable:", "In familiar social situations", "In one-on-one conversations"),
        (9, "I approach new situations by:", "Jumping in and engaging", "Observing before participating"),
        (10, "I prefer my workspace to be:", "Open and collaborative", "Private and quiet"),
        (11, "After a long day, I recharge by:", "Socializing or being active", "Having quiet time to myself"),
        (12, "In group projects, I:", "Take an active leadership role", "Contribute my ideas thoughtfully"),
        (13, "I prefer learning:", "Through discussion and interaction", "Through reading and reflection"),
        (14, "When stressed, I:", "Seek out social support", "Need time to process alone"),
        (15, "I feel more energized:", "After social interactions", "After time alone"),
        (16, "I prefer communication to be:", "Expressive and animated", "Measured and thoughtful"),
        (17, "In brainstorming sessions, I:", "Generate ideas out loud", "Think before sharing ideas"),
        (18, "I approach networking by:", "Meeting many new people", "Building deeper connections with few"),
        (19, "I prefer parties where I:", "Know many people", "Can have intimate conversations"),
        (20, "I express my thoughts:", "Freely and openly", "After careful consideration"),
        (21, "I feel most confident:", "When speaking to groups", "When speaking one-on-one"),
        (22, "I prefer to resolve conflicts by:", "Discussing openly", "Reflecting before responding"),
        (23, "I approach new challenges by:", "Seeking others' perspectives", "Analyzing independently")
    ]

    # S-N Questions (22)
    sn_questions = [
        (24, "I trust:", "My practical experience", "My intuition and possibilities"),
        (25, "I prefer to focus on:", "Concrete facts and details", "The big picture and possibilities"),
        (26, "When learning something new, I prefer:", "Step-by-step instructions", "Understanding the overall concept first"),
        (27, "I'm more interested in:", "What actually exists", "What could be possible"),
        (28, "I approach problems by:", "Following established methods", "Exploring innovative solutions"),
        (29, "I prefer conversations that are:", "Literal and straightforward", "Figurative and conceptual"),
        (30, "I remember:", "Specific details and facts", "General impressions and patterns"),
        (31, "I'm more attracted to:", "Practical, realistic applications", "Theoretical possibilities"),
        (32, "I prefer to:", "Work with tangible things", "Work with ideas and concepts"),
        (33, "When reading, I focus on:", "The actual text and details", "The underlying meaning and themes"),
        (34, "I prefer instructions that are:", "Specific and detailed", "General and flexible"),
        (35, "I'm more comfortable with:", "The present reality", "Future possibilities"),
        (36, "I make decisions based on:", "Past experience and facts", "Potential outcomes and possibilities"),
        (37, "I prefer:", "Proven methods", "Creative approaches"),
        (38, "I'm more interested in:", "How things work", "Why things work"),
        (39, "I prefer to communicate:", "Literally and directly", "Metaphorically and creatively"),
        (40, "I trust information that is:", "Concrete and verifiable", "Conceptual and insightful"),
        (41, "I prefer learning:", "Hands-on experience", "Conceptual understanding"),
        (42, "I'm more focused on:", "The actual situation", "The possibilities within the situation"),
        (43, "I prefer tasks that are:", "Practical and useful", "Innovative and inspiring"),
        (44, "I approach creativity by:", "Improving existing methods", "Generating entirely new concepts"),
        (45, "I value:", "Realism and practicality", "Imagination and innovation")
    ]

    # T-F Questions (23)
    tf_questions = [
        (46, "When making decisions, I prioritize:", "Logic and objective analysis", "Personal values and impact on others"),
        (47, "I prefer to be known as:", "Logical and reasonable", "Compassionate and understanding"),
        (48, "In conflicts, I focus on:", "Finding the logical solution", "Maintaining harmony and relationships"),
        (49, "I evaluate others based on:", "Their competence and achievements", "Their character and intentions"),
        (50, "When giving feedback, I:", "Focus on objective facts and improvement", "Consider feelings and encourage positively"),
        (51, "I make judgments based on:", "Universal principles and logic", "Personal circumstances and values"),
        (52, "I prefer leaders who are:", "Fair and logical", "Supportive and inspiring"),
        (53, "When solving problems, I:", "Analyze the pros and cons", "Consider how it affects people"),
        (54, "I value:", "Truth and accuracy", "Harmony and goodwill"),
        (55, "I approach rules as:", "Guidelines to be applied consistently", "Flexible based on circumstances"),
        (56, "In debates, I focus on:", "The logical validity of arguments", "Understanding different perspectives"),
        (57, "I prefer to make decisions:", "Impartially and objectively", "Based on personal values"),
        (58, "I'm more concerned with:", "Being right and correct", "Being kind and helpful"),
        (59, "When evaluating ideas, I look for:", "Logical consistency", "Human impact and value"),
        (60, "I prefer communication that is:", "Direct and logical", "Tactful and considerate"),
        (61, "I approach justice by:", "Applying rules consistently", "Considering individual circumstances"),
        (62, "I value people who are:", "Competent and intelligent", "Loyal and caring"),
        (63, "When criticized, I:", "Analyze whether it's factually correct", "Consider the relationship and context"),
        (64, "I prefer to organize my life based on:", "Logical principles", "Personal values"),
        (65, "I approach teamwork by:", "Focusing on efficiency and results", "Building relationships and morale"),
        (66, "I make important decisions by:", "Weighing logical options", "Following my heart"),
        (67, "I prefer to be:", "Objective and analytical", "Empathetic and supportive"),
        (68, "I approach truth by:", "Seeking factual accuracy", "Understanding deeper meaning")
    ]

    # J-P Questions (22)
    jp_questions = [
        (69, "I prefer to:", "Make decisions quickly", "Keep my options open"),
        (70, "When planning, I like to:", "Have things decided and settled", "Remain flexible and adaptable"),
        (71, "I work best with:", "Clear deadlines and structure", "Flexible timelines and autonomy"),
        (72, "I approach projects by:", "Planning before starting", "Starting and adapting as I go"),
        (73, "I prefer my environment to be:", "Organized and structured", "Spontaneous and flexible"),
        (74, "When faced with new information, I:", "Quickly reach conclusions", "Continue gathering information"),
        (75, "I feel most comfortable when:", "Things are decided and planned", "Things remain open-ended"),
        (76, "I prefer to:", "Complete tasks early", "Work well under pressure"),
        (77, "I approach life with:", "A structured plan", "Adaptable flexibility"),
        (78, "I make travel plans by:", "Booking everything in advance", "Keeping options open"),
        (79, "I prefer work that allows me to:", "Complete one project before starting another", "Juggle multiple projects"),
        (80, "When shopping, I:", "Make quick decisions", "Consider all options before buying"),
        (81, "I feel stressed when:", "Plans change unexpectedly", "Too many decisions are pending"),
        (82, "I prefer to:", "Finish current tasks before taking on new ones", "Start new tasks even if others aren't complete"),
        (83, "I approach deadlines by:", "Working steadily toward them", "Working best close to the deadline"),
        (84, "I prefer my schedule to be:", "Set and organized", "Flexible and spontaneous"),
        (85, "I approach new opportunities by:", "Evaluating them systematically", "Exploring them spontaneously"),
        (86, "I feel most productive when:", "Following a clear plan", "Responding to emerging needs"),
        (87, "I prefer to:", "Make lists and follow them", "Keep things flexible in my mind"),
        (88, "I approach change by:", "Planning for it systematically", "Adapting as it happens"),
        (89, "I feel uncomfortable when:", "Too many things are undecided", "Too much structure is imposed"),
        (90, "I complete tasks by:", "Working methodically to completion", "Finding last-minute inspiration")
    ]

    # Combine all questions
    all_questions = []
    all_questions.extend(ei_questions)
    all_questions.extend(sn_questions)
    all_questions.extend(tf_questions)
    all_questions.extend(jp_questions)

    return all_questions

def update_mbti_complete():
    """Update MBTI with complete 90 questions"""

    questions = generate_complete_mbti_questions()

    # Generate questions array
    questions_array = []
    for q_id, q_text, opt1, opt2 in questions:
        q_text_escaped = q_text.replace('"', '\\"')
        opt1_escaped = opt1.replace('"', '\\"')
        opt2_escaped = opt2.replace('"', '\\"')

        question_json = f'''                {{
                    "id": {q_id},
                    "question_text": "{q_text_escaped}",
                    "dimension": "{get_dimension_from_id(q_id)}",
                    "options": [
                        {{"text": "{opt1_escaped}", "value": "{get_value_from_id(q_id, 'opt1')}"}},
                        {{"text": "{opt2_escaped}", "value": "{get_value_from_id(q_id, 'opt2')}"}}
                    ]
                }}'''
        questions_array.append(question_json)

    return '            "questions": [\n' + ',\n'.join(questions_array) + '\n            ]'

def get_dimension_from_id(q_id):
    """Get MBTI dimension from question ID"""
    if 1 <= q_id <= 23:
        return "E-I"
    elif 24 <= q_id <= 45:
        return "S-N"
    elif 46 <= q_id <= 68:
        return "T-F"
    elif 69 <= q_id <= 90:
        return "J-P"
    return "E-I"

def get_value_from_id(q_id, opt):
    """Get option value from question ID and option number"""
    dimension = get_dimension_from_id(q_id)
    if dimension == "E-I":
        return "E" if opt == "opt1" else "I"
    elif dimension == "S-N":
        return "S" if opt == "opt1" else "N"
    elif dimension == "T-F":
        return "T" if opt == "opt1" else "F"
    elif dimension == "J-P":
        return "J" if opt == "opt1" else "P"
    return "E"

if __name__ == "__main__":
    # Test the question generation
    questions = generate_complete_mbti_questions()
    print(f"Generated {len(questions)} MBTI questions")

    # Test the first few questions
    print("\nFirst 3 questions:")
    for i, (q_id, q_text, opt1, opt2) in enumerate(questions[:3]):
        print(f"Q{q_id}: {q_text}")
        print(f"  {opt1} vs {opt2}")
        print(f"  Dimension: {get_dimension_from_id(q_id)}")
        print()
