#!/usr/bin/env python3
"""
Comprehensive script to expand all personality assessments to 90 questions each
"""

import re
import json

def generate_mbti_questions_90():
    """Generate 90 MBTI questions with balanced dimensions"""
    questions = []
    question_id = 1

    # E-I Questions (23 total)
    e_i_questions = [
        ("At parties, do you:", "Talk to many people, including strangers", "Talk to a few people you know well"),
        ("After a long week, do you prefer to:", "Go out with friends to socialize", "Stay home with a book or movie"),
        ("When solving a problem, do you:", "Talk it through with others", "Think it through by yourself"),
        ("In meetings, do you:", "Speak up and participate actively", "Listen and process before speaking"),
        ("At work, do you:", "Enjoy working in teams and brainstorming with others", "Prefer working independently and concentrating deeply"),
        ("When you're stressed, do you:", "Seek out people to talk to", "Need quiet time alone to recharge"),
        ("In a new city, do you:", "Make friends and explore social scene", "Explore museums and parks alone"),
        ("Do you get your energy from:", "Being around people and activities", "Quiet reflection and solitude"),
        ("When making decisions, do you:", "Seek input from others first", "Think it through privately first"),
        ("In group projects, do you prefer:", "Leading discussions and collaboration", "Working independently on your portion"),
        ("When learning, do you prefer:", "Group discussions and study sessions", "Individual research and reading"),
        ("At social gatherings, do you typically:", "Circulate and meet many people", "Find a few people for deep conversation"),
        ("When traveling, do you prefer:", "Group tours and shared experiences", "Solo exploration and reflection"),
        ("When faced with a challenge, do you:", "Brainstorm with others", "Research and analyze alone"),
        ("Do you prefer work environments that are:", "Collaborative and interactive", "Quiet and focused"),
        ("When celebrating achievements, do you:", "Share news with many people", "Celebrate privately with close friends"),
        ("In conversations, do you tend to:", "Think out loud", "Process internally before speaking"),
        ("When networking, do you:", "Approach strangers easily", "Prefer introductions through others"),
        ("In brainstorming sessions, do you:", "Build on others' ideas immediately", "Reflect before contributing"),
        ("When dining out, do you prefer:", "Lively restaurants with ambiance", "Quiet, intimate settings"),
        ("Do you consider yourself more:", "Outgoing and expressive", "Reserved and thoughtful"),
        ("In team sports, do you prefer:", "Collaborative team play", "Individual performance roles"),
        ("When giving presentations, do you:", "Engage with the audience", "Focus on the content"),
        ("In casual conversations, do you:", "Initiate discussions with strangers", "Wait for others to approach")
    ]

    # S-N Questions (22 total)
    s_n_questions = [
        ("Do you prefer to:", "Focus on the real world and practical matters", "Imagine possibilities and think about abstract concepts"),
        ("When learning something new, do you:", "Prefer step-by-step instructions with concrete examples", "Like to understand the overall concept first"),
        ("When reading, do you prefer:", "Factual information and practical guides", "Theoretical concepts and symbolic meanings"),
        ("At work, do you focus more on:", "What is actual and present", "What could be possible"),
        ("When someone explains something, do you prefer:", "Specific details and step-by-step process", "The big picture and underlying principles"),
        ("Do you trust more:", "Past experience and concrete data", "Your intuition and future possibilities"),
        ("When making a purchase, do you focus on:", "Practical features and proven reliability", "How it could enhance your future lifestyle"),
        ("In problem-solving, do you:", "Use proven methods and facts", "Explore innovative approaches"),
        ("When planning, do you focus on:", "Realistic, immediate needs", "Long-term possibilities"),
        ("Do you prefer information that is:", "Concrete and specific", "Abstract and conceptual"),
        ("When analyzing situations, do you:", "Focus on what actually happened", "Consider what might have been"),
        ("In presentations, do you prefer:", "Data, facts, and examples", "Concepts and future possibilities"),
        ("When giving feedback, do you:", "Provide specific, observable examples", "Discuss potential and possibilities"),
        ("Do you notice more:", "Specific details and facts", "Patterns and connections"),
        ("When making career choices, do you consider:", "Practical benefits and stability", "Growth potential and meaning"),
        ("In relationships, do you value:", "Shared experiences and realities", "Intellectual and emotional connections"),
        ("When facing uncertainty, do you:", "Seek concrete information", "Trust your intuition"),
        ("Do you prefer art that is:", "Realistic and representational", "Abstract and symbolic"),
        ("When learning history, do you prefer:", "Specific dates, events, and facts", "Themes, patterns, and meanings"),
        ("In debates, do you focus on:", "Factual accuracy and evidence", "Conceptual validity and possibilities"),
        ("When traveling, do you prefer:", "Detailed itineraries with specific activities", "Flexible plans that allow for discovery"),
        ("When solving puzzles, do you prefer:", "Logic-based challenges", "Creative problem-solving")
    ]

    # T-F Questions (23 total)
    t_f_questions = [
        ("When making decisions, do you:", "Rely on logic and objective analysis", "Consider how it will affect people involved"),
        ("When giving feedback, do you:", "Focus on facts and logical improvements", "Consider feelings and how to deliver it gently"),
        ("In a disagreement, do you focus more on:", "Finding the logical truth", "Maintaining harmony in relationships"),
        ("When evaluating a job offer, do you prioritize:", "Objective criteria like salary and advancement", "Company culture and your gut feeling"),
        ("Do you make decisions based on:", "Universal principles and fairness", "Individual circumstances and relationships"),
        ("When someone asks for advice, do you:", "Give direct, analytical solutions", "Offer emotional support and understanding"),
        ("In group discussions, do you value more:", "Logical analysis and objective truth", "Consensus and everyone's feelings"),
        ("Do you admire people more for being:", "Consistently logical and fair", "Compassionate and understanding"),
        ("When mediating conflicts, do you:", "Focus on finding the logical solution", "Consider everyone's emotional needs"),
        ("In hiring decisions, do you prioritize:", "Skills and qualifications", "Cultural fit and personality"),
        ("When setting goals, do you focus on:", "Achievement and success metrics", "Personal growth and fulfillment"),
        ("Do you believe justice should be:", "Consistent and impartial", "Compassionate and contextual"),
        ("When evaluating arguments, do you look for:", "Logical consistency and evidence", "Emotional authenticity and sincerity"),
        ("In leadership, do you prioritize:", "Efficiency and results", "Team morale and satisfaction"),
        ("When giving compliments, do you:", "Acknowledge specific achievements", "Express appreciation for character"),
        ("Do you prefer to solve problems by:", "Analyzing the system", "Understanding the people involved"),
        ("In ethical dilemmas, do you follow:", "Universal moral principles", "The impact on relationships"),
        ("When receiving criticism, do you:", "Analyze the logic and validity", "Consider the person's intentions"),
        ("Do you value truth more when it's:", "Objective and verifiable", "Emotionally resonant and meaningful"),
        ("In time management, do you prioritize:", "Maximum efficiency", "Maintaining relationships"),
        ("When making rules, do you focus on:", "Consistency and fairness", "Flexibility and compassion"),
        ("Do you believe decisions should be based on:", "Cost-benefit analysis", "Human impact assessment"),
        ("In negotiations, do you aim for:", "The most logical agreement", "A relationship-preserving outcome")
    ]

    # J-P Questions (22 total)
    j_p_questions = [
        ("Do you prefer to:", "Plan things in advance and stick to the plan", "Be spontaneous and adapt to new situations"),
        ("For weekends, do you:", "Plan activities and have a schedule", "Leave options open and decide spontaneously"),
        ("When starting a project, do you:", "Create a detailed plan first", "Start and figure it out as you go"),
        ("How do you feel about deadlines?", "They help me stay organized and focused", "They feel restrictive and I work best when flexible"),
        ("When traveling, do you prefer to:", "Have a detailed itinerary", "Explore freely and be spontaneous"),
        ("Do you prefer your work environment to be:", "Structured and predictable", "Flexible and adaptable"),
        ("When making decisions, do you:", "Make quick decisions to move forward", "Keep options open as long as possible"),
        ("In managing tasks, do you prefer:", "Completing one thing at a time", "Juggling multiple projects"),
        ("When shopping, do you:", "Make lists and stick to them", "Browse and discover new options"),
        ("Do you prefer your living space to be:", "Organized and tidy", "Comfortable and lived-in"),
        ("When approaching problems, do you:", "Follow established procedures", "Try various approaches"),
        ("In conversations, do you:", "Drive toward conclusions", "Explore possibilities and tangents"),
        ("When setting boundaries, do you:", "Establish clear rules", "Keep options flexible"),
        ("Do you prefer to finish projects:", "Before starting new ones", "Even as new ideas emerge"),
        ("When managing time, do you:", "Stick to schedules religiously", "Adapt to changing priorities"),
        ("In relationships, do you prefer:", "Clear definitions and expectations", "Spontaneous development"),
        ("When learning, do you:", "Follow structured curricula", "Explore topics as they interest you"),
        ("Do you approach life with:", "A clear plan and direction", "Openness to unexpected opportunities"),
        ("In social planning, do you:", "Organize events in advance", "Spontaneously get together"),
        ("When working on creative projects, do you:", "Work toward a defined outcome", "Follow inspiration wherever it leads"),
        ("Do you prefer endings that are:", "Clear and definitive", "Open to continuation"),
        ("In decision-making, do you value:", "Closure and finality", "Possibility and flexibility")
    ]

    # Add all questions
    for q_text, opt1, opt2 in e_i_questions:
        questions.append({
            "id": question_id,
            "question_text": q_text,
            "dimension": "E-I",
            "options": [
                {"text": opt1, "value": "E"},
                {"text": opt2, "value": "I"}
            ]
        })
        question_id += 1

    for q_text, opt1, opt2 in s_n_questions:
        questions.append({
            "id": question_id,
            "question_text": q_text,
            "dimension": "S-N",
            "options": [
                {"text": opt1, "value": "S"},
                {"text": opt2, "value": "N"}
            ]
        })
        question_id += 1

    for q_text, opt1, opt2 in t_f_questions:
        questions.append({
            "id": question_id,
            "question_text": q_text,
            "dimension": "T-F",
            "options": [
                {"text": opt1, "value": "T"},
                {"text": opt2, "value": "F"}
            ]
        })
        question_id += 1

    for q_text, opt1, opt2 in j_p_questions:
        questions.append({
            "id": question_id,
            "question_text": q_text,
            "dimension": "J-P",
            "options": [
                {"text": opt1, "value": "J"},
                {"text": opt2, "value": "P"}
            ]
        })
        question_id += 1

    return questions[:90]  # Ensure exactly 90 questions

def generate_big_five_questions_90():
    """Generate 90 Big Five questions (18 per trait)"""
    questions = []
    question_id = 1

    traits = ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"]

    # Sample statements for each trait (will generate 18 per trait)
    trait_statements = {
        "Openness": [
            "I see myself as someone who is original and comes up with new ideas",
            "I see myself as someone who is curious about many different things",
            "I see myself as someone who is inventive and finds new ways to do things",
            "I see myself as someone who values artistic and aesthetic experiences",
            "I see myself as someone who prefers variety over routine",
            "I see myself as someone who thinks about and discusses abstract concepts",
            "I see myself as someone who enjoys wild flights of fantasy",
            "I see myself as someone who believes in the importance of art",
            "I see myself as someone who often hears a little voice inside that questions the way things are",
            "I see myself as someone who tends to vote for liberal candidates",
            "I see myself as someone who identifies with unconventional points of view",
            "I see myself as someone who is abstract and theoretical",
            "I see myself as someone who has a vivid imagination",
            "I see myself as someone who is clever",
            "I see myself as someone who is ingenious",
            "I see myself as someone who prefers work that is original and creative",
            "I see myself as someone who is inventive",
            "I see myself as someone who is sophisticated in art and music"
        ],
        "Conscientiousness": [
            "I see myself as someone who does a thorough job",
            "I see myself as someone who can be somewhat careless (reverse scored)",
            "I see myself as someone who is a reliable worker",
            "I see myself as someone who tends to be organized",
            "I see myself as someone who perseveres until the task is finished",
            "I see myself as someone who can be somewhat lazy (reverse scored)",
            "I see myself as someone who does things according to a plan",
            "I see myself as someone who pays attention to details",
            "I see myself as someone who immediately starts doing the chores",
            "I see myself as someone who likes order",
            "I see myself as someone who follows a schedule",
            "I see myself as someone who exerts the proper amount of effort",
            "I see myself as someone who continues until everything is perfect",
            "I see myself as someone who does more than what's required",
            "I see myself as someone who works hard",
            "I see myself as someone who spends time preparing",
            "I see myself as someone who is exact in my work",
            "I see myself as someone who is thoughtful",
            "I see myself as someone who is persistent in achieving goals"
        ],
        "Extraversion": [
            "I see myself as someone who is talkative",
            "I see myself as someone who is reserved (reverse scored)",
            "I see myself as someone who is full of energy",
            "I see myself as someone who generates enthusiasm in others",
            "I see myself as someone who is assertive and takes charge",
            "I see myself as someone who prefers working independently (reverse scored)",
            "I see myself as someone who has an active imagination",
            "I see myself as someone who is quiet and shy (reverse scored)",
            "I see myself as someone who is enthusiastic",
            "I see myself as someone who has a assertive personality",
            "I see myself as someone who is outgoing and sociable",
            "I see myself as someone who creates a lot of excitement",
            "I see myself as someone who has a lot of energy",
            "I see myself as someone who is the life of the party",
            "I see myself as someone who likes to be where the action is",
            "I see myself as someone who is easy to get along with",
            "I see myself as someone who starts conversations",
            "I see myself as someone who has no difficulty making friends"
        ],
        "Agreeableness": [
            "I see myself as someone who tends to find fault with others (reverse scored)",
            "I see myself as someone who is helpful and unselfish with others",
            "I see myself as someone who starts arguments with others (reverse scored)",
            "I see myself as someone who has a forgiving nature",
            "I see myself as someone who is generally trusting",
            "I see myself as someone who can be cold and aloof (reverse scored)",
            "I see myself as someone who is considerate and kind to almost everyone",
            "I see myself as someone who likes to cooperate with others",
            "I see myself as someone who accepts others without judgment",
            "I see myself as someone who respects authority",
            "I see myself as someone who accepts people as they are",
            "I see myself as someone who makes people feel at ease",
            "I see myself as someone who has respect for others",
            "I see myself as someone who believes that people are basically good",
            "I see myself as someone who is patient",
            "I see myself as someone who is polite",
            "I see myself as someone who likes to do things for others",
            "I see myself as someone who is warm and friendly",
            "I see myself as someone who is soft-hearted"
        ],
        "Neuroticism": [
            "I see myself as someone who is depressed, blue",
            "I see myself as someone who is relaxed, handles stress well (reverse scored)",
            "I see myself as someone who can be tense",
            "I see myself as someone who worries a lot",
            "I see myself as someone who can get easily upset",
            "I see myself as someone who remains calm in tense situations (reverse scored)",
            "I see myself as someone who gets nervous easily",
            "I see myself as someone who is easily disturbed",
            "I see myself as someone who gets moody",
            "I see myself as someone who uses experience to guide my behavior",
            "I see myself as someone who gets overwhelmed by emotions",
            "I see myself as someone who has frequent mood swings",
            "I see myself as someone who feels anxious",
            "I see myself as someone who feels blue",
            "I see myself as someone who worries about things",
            "I see myself as someone who is sensitive",
            "I see myself as someone who can be tense",
            "I see myself as someone who feels threatened easily"
        ]
    }

    # Generate 18 questions per trait
    for trait in traits:
        statements = trait_statements[trait]
        for i in range(18):  # 18 questions per trait
            if i < len(statements):
                question_text = statements[i]
            else:
                # Generate additional generic statements if needed
                question_text = f"I see myself as someone who is {trait.lower()} in various situations"

            questions.append({
                "id": question_id,
                "question_text": question_text,
                "trait": trait,
                "scale": "1-5",
                "options": [
                    {"text": "Strongly Disagree", "value": 1},
                    {"text": "Disagree", "value": 2},
                    {"text": "Neutral", "value": 3},
                    {"text": "Agree", "value": 4},
                    {"text": "Strongly Agree", "value": 5}
                ]
            })
            question_id += 1

    return questions[:90]  # Ensure exactly 90 questions

def main():
    """Generate all expanded assessments"""
    print("🚀 Generating 90-Question Assessments for All Personality Frameworks...")

    mbti_questions = generate_mbti_questions_90()
    big_five_questions = generate_big_five_questions_90()

    print(f"✅ Generated {len(mbti_questions)} MBTI questions")
    print(f"✅ Generated {len(big_five_questions)} Big Five questions")

    # Generate sample output files
    with open('/Users/sheriftito/Downloads/psychsync/mbti_90_questions.json', 'w') as f:
        json.dump(mbti_questions, f, indent=2)

    with open('/Users/sheriftito/Downloads/psychsync/big_five_90_questions.json', 'w') as f:
        json.dump(big_five_questions, f, indent=2)

    print(f"📁 Saved question files for reference")
    print(f"🎯 Ready to integrate into API endpoints!")

    return {
        "mbti": mbti_questions,
        "big_five": big_five_questions
    }

if __name__ == "__main__":
    main()
