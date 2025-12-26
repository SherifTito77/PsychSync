#!/usr/bin/env python3
"""
Script to expand Enneagram assessment from 30 to 90 questions
"""

import json

def generate_additional_enneagram_questions():
    """Generate 60 additional Enneagram questions (31-90)"""
    questions = []

    # Additional questions for Types 1-3 (20 questions)
    type1_additional = [
        ("I struggle with accepting that:", "Good enough is often sufficient", "I must constantly improve"),
        ("In leadership roles, I:", "Set high standards for everyone", "Encourage others' authentic development"),
        ("My inner critic is loudest when:", "I or others make mistakes", "I feel I'm not living up to potential"),
        ("I find it hardest to:", "Forgive my own imperfections", "Accept others' flaws"),
        ("In relationships, I need:", "Mutual growth and improvement", "Unconditional acceptance"),
        ("People who know me would say I'm:", "Overly critical of myself and others", "Principled and dedicated"),
        ("I express anger through:", "Resentment and frustration", "Direct communication"),
        ("I feel most anxious when:", "Things aren't done correctly", "I can't control outcomes"),
        ("My greatest strength is:", "My integrity and high standards", "My ability to see what's right"),
        ("I relax best when:", "Everything is in its proper place", "I can let go of control")
    ]

    type2_additional = [
        ("In relationships, I often:", "Give more than I receive", "Maintain healthy boundaries"),
        ("My biggest challenge is:", "Recognizing my own needs", "Asking for help when needed"),
        ("People take advantage of my:", "Generosity and willingness to help", "Trust and openness"),
        ("I feel most valuable when:", "Others need my help", "I can care for myself properly"),
        ("In conflicts, I tend to:", "Mediate and seek harmony", "State my own needs clearly"),
        ("My greatest fear is:", "Being unloved or unwanted", "Being abandoned"),
        ("I struggle with:", "Feeling worthy without helping", "Setting appropriate limits"),
        ("Others see me as:", "Overly involved in their problems", "Empathetic and supportive"),
        ("I express love by:", "Being helpful and available", "Respecting others' autonomy"),
        ("At my best, I am:", "Unconditionally loving", "Self-aware and balanced")
    ]

    type3_additional = [
        ("I measure success by:", "External achievements and recognition", "Inner fulfillment and growth"),
        ("My biggest fear is:", "Being seen as a failure", "Being worthless without achievements"),
        ("I struggle with:", "Separating my worth from my success", "Being vulnerable and authentic"),
        ("People would describe me as:", "Image-conscious and competitive", "Ambitious and capable"),
        ("In relationships, I:", "Project success and confidence", "Show my authentic self"),
        ("I feel most anxious when:", "I'm not achieving or progressing", "Others might see my flaws"),
        ("My core drive is:", "To be valuable and admired", "To be genuine and loved"),
        ("I find it hard to:", "Admit when I don't know something", "Just be without performing"),
        ("Others criticize me for being:", "Inauthentic or superficial", "Too focused on success"),
        ("At my best, I am:", "Authentic and inspiring", "Truly successful and fulfilled")
    ]

    # Add type 1-3 questions
    for i, (q_text, opt1, opt2) in enumerate(type1_additional):
        questions.append({
            "id": 31 + i,
            "question_text": q_text,
            "type": "Self-Image",
            "options": [
                {"text": opt1, "value": "type1"},
                {"text": opt2, "value": "type1"}
            ]
        })

    for i, (q_text, opt1, opt2) in enumerate(type2_additional):
        questions.append({
            "id": 41 + i,
            "question_text": q_text,
            "type": "Relationship Style",
            "options": [
                {"text": opt1, "value": "type2"},
                {"text": opt2, "value": "type2"}
            ]
        })

    for i, (q_text, opt1, opt2) in enumerate(type3_additional):
        questions.append({
            "id": 51 + i,
            "question_text": q_text,
            "type": "Success Identity",
            "options": [
                {"text": opt1, "value": "type3"},
                {"text": opt2, "value": "type3"}
            ]
        })

    # Additional questions for Types 4-6 (20 questions)
    type4_additional = [
        ("I feel most misunderstood when:", "Others don't see my depth", "I seem too dramatic"),
        ("My greatest struggle is:", "Feeling ordinary or mundane", "Managing my emotional intensity"),
        ("People would describe me as:", "Overly sensitive or dramatic", "Deep and creative"),
        ("I find beauty in:", "Melancholy and suffering", "Authentic emotional expression"),
        ("In relationships, I:", "Seek deep, intense connection", "Fear abandonment and rejection"),
        ("My core fear is:", "Having no identity or significance", "Being common or ordinary"),
        ("I struggle with:", "Envy of others' happiness", "Feeling fundamentally flawed"),
        ("I express myself through:", "Art and creativity", "Deep emotional conversations"),
        ("Others criticize me for being:", "Too moody or self-absorbed", "Overly dramatic"),
        ("At my best, I am:", "Creatively inspired and authentic", "Emotionally balanced and grounded")
    ]

    type5_additional = [
        ("I feel safest when:", "I understand how things work", "I have time to myself"),
        ("My biggest challenge is:", "Engaging with the emotional world", "Sharing my inner thoughts"),
        ("People see me as:", "Detached or overly analytical", "Intelligent and perceptive"),
        ("I prefer to:", "Observe rather than participate", "Understand before engaging"),
        ("In relationships, I:", "Need intellectual connection", "Require lots of personal space"),
        ("My greatest fear is:", "Being helpless or incompetent", "Having no privacy or autonomy"),
        ("I struggle with:", "Expressing my feelings", "Being emotionally vulnerable"),
        ("I feel most drained when:", "I have too much social interaction", "I can't research enough"),
        ("Others describe me as:", "Too reserved or distant", "Knowledgeable and insightful"),
        ("At my best, I am:", "Wise and understanding", "Engaged and connected")
    ]

    type6_additional = [
        ("I approach life with:", "Careful planning and risk assessment", "Trust in supportive relationships"),
        ("My biggest challenge is:", "Trusting myself and others", "Making decisions without doubt"),
        ("People would describe me as:", "Anxious or overly cautious", "Loyal and committed"),
        ("I feel most anxious when:", "I don't have a safety net", "I have to act independently"),
        ("In decision-making, I:", "Seek guidance from trusted sources", "Question everything thoroughly"),
        ("My core fear is:", "Being without support or guidance", "Facing danger alone"),
        ("I struggle with:", "Self-doubt and second-guessing", "Trusting my instincts"),
        ("I find security in:", "Clear rules and authorities", "Personal relationships and loyalty"),
        ("Others criticize me for being:", "Too dependent or fearful", "Overly analytical"),
        ("At my best, I am:", "Courageous and supportive", "Confident and self-trusting")
    ]

    # Add type 4-6 questions
    for i, (q_text, opt1, opt2) in enumerate(type4_additional):
        questions.append({
            "id": 61 + i,
            "question_text": q_text,
            "type": "Emotional Depth",
            "options": [
                {"text": opt1, "value": "type4"},
                {"text": opt2, "value": "type4"}
            ]
        })

    for i, (q_text, opt1, opt2) in enumerate(type5_additional):
        questions.append({
            "id": 71 + i,
            "question_text": q_text,
            "type": "Knowledge Seeking",
            "options": [
                {"text": opt1, "value": "type5"},
                {"text": opt2, "value": "type5"}
            ]
        })

    for i, (q_text, opt1, opt2) in enumerate(type6_additional):
        questions.append({
            "id": 81 + i,
            "question_text": q_text,
            "type": "Security Seeking",
            "options": [
                {"text": opt1, "value": "type6"},
                {"text": opt2, "value": "type6"}
            ]
        })

    # Ensure exactly 60 questions (limit if needed)
    return questions[:60]

def main():
    """Main function to generate additional Enneagram questions"""
    questions = generate_additional_enneagram_questions()
    print(f"Generated {len(questions)} additional Enneagram questions")

    # Display first few questions as examples
    for i, q in enumerate(questions[:5]):
        print(f"\nQuestion {q['id']}:")
        print(f"  Text: {q['question_text']}")
        print(f"  Type: {q['type']}")
        print(f"  Options: {len(q['options'])}")

    return questions

if __name__ == "__main__":
    main()