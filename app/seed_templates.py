# app/seed_templates.py
"""
Seed official assessment templates
Run: python seed_templates.py
"""
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.models.template import AssessmentTemplate, TemplateCategory

# Add these lines at the very top of seed_templates.py
import sys
print("Python is looking for modules in these paths:")
for p in sys.path:
    print(p)
print("-" * 20)

def seed_templates():
    engine = create_engine(settings.DATABASE_URL)
    db = Session(engine)
    
    # Big Five Personality Template
    big_five_data = {
        'title': 'Big Five Personality Assessment',
        'description': 'Measure the five major dimensions of personality',
        'category': 'personality',
        'instructions': 'Rate each statement based on how accurately it describes you.',
        'estimated_duration': 15,
        'sections': [
            {
                'title': 'Openness to Experience',
                'description': 'Your imagination, curiosity, and willingness to try new things',
                'order': 0,
                'questions': [
                    {
                        'question_type': 'likert',
                        'question_text': 'I have a vivid imagination',
                        'order': 0,
                        'is_required': True,
                        'config': {
                            'scale': 5,
                            'labels': ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree']
                        }
                    },
                    {
                        'question_type': 'likert',
                        'question_text': 'I am interested in abstract ideas',
                        'order': 1,
                        'is_required': True,
                        'config': {
                            'scale': 5,
                            'labels': ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree']
                        }
                    }
                ]
            },
            {
                'title': 'Conscientiousness',
                'description': 'Your organization, responsibility, and reliability',
                'order': 1,
                'questions': [
                    {
                        'question_type': 'likert',
                        'question_text': 'I am always prepared',
                        'order': 0,
                        'is_required': True,
                        'config': {
                            'scale': 5,
                            'labels': ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree']
                        }
                    },
                    {
                        'question_type': 'likert',
                        'question_text': 'I pay attention to details',
                        'order': 1,
                        'is_required': True,
                        'config': {
                            'scale': 5,
                            'labels': ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree']
                        }
                    }
                ]
            }
        ]
    }
    
    big_five = AssessmentTemplate(
        name='Big Five Personality Assessment',
        description='Standard Big Five personality traits measurement',
        category=TemplateCategory.PERSONALITY,
        author='PsychSync Official',
        is_official=True,
        is_public=True,
        template_data=json.dumps(big_five_data)
    )
    db.add(big_five)
    
    # Cognitive Assessment Template
    cognitive_data = {
        'title': 'Basic Cognitive Assessment',
        'description': 'Evaluate basic cognitive abilities',
        'category': 'cognitive',
        'instructions': 'Answer each question to the best of your ability.',
        'estimated_duration': 20,
        'sections': [
            {
                'title': 'Memory',
                'description': 'Short-term and working memory evaluation',
                'order': 0,
                'questions': [
                    {
                        'question_type': 'rating_scale',
                        'question_text': 'Rate your ability to remember recent conversations',
                        'order': 0,
                        'is_required': True,
                        'config': {
                            'min': 1,
                            'max': 10,
                            'labels': {'1': 'Very Poor', '10': 'Excellent'}
                        }
                    }
                ]
            },
            {
                'title': 'Attention',
                'description': 'Sustained and selective attention',
                'order': 1,
                'questions': [
                    {
                        'question_type': 'rating_scale',
                        'question_text': 'Rate your ability to focus on tasks for extended periods',
                        'order': 0,
                        'is_required': True,
                        'config': {
                            'min': 1,
                            'max': 10,
                            'labels': {'1': 'Very Poor', '10': 'Excellent'}
                        }
                    }
                ]
            }
        ]
    }
    
    cognitive = AssessmentTemplate(
        name='Basic Cognitive Assessment',
        description='Evaluate memory, attention, and processing speed',
        category=TemplateCategory.COGNITIVE,
        author='PsychSync Official',
        is_official=True,
        is_public=True,
        template_data=json.dumps(cognitive_data)
    )
    db.add(cognitive)
    
    # Wellbeing Assessment
    wellbeing_data = {
        'title': 'Wellbeing Check-In',
        'description': 'Quick assessment of current wellbeing',
        'category': 'wellbeing',
        'instructions': 'Reflect on the past week and answer honestly.',
        'estimated_duration': 10,
        'sections': [
            {
                'title': 'Emotional Wellbeing',
                'order': 0,
                'questions': [
                    {
                        'question_type': 'rating_scale',
                        'question_text': 'Overall, how would you rate your mood this week?',
                        'order': 0,
                        'is_required': True,
                        'config': {
                            'min': 1,
                            'max': 10,
                            'labels': {'1': 'Very Poor', '5': 'Neutral', '10': 'Excellent'}
                        }
                    },
                    {
                        'question_type': 'rating_scale',
                        'question_text': 'How stressed have you felt?',
                        'order': 1,
                        'is_required': True,
                        'config': {
                            'min': 1,
                            'max': 10,
                            'labels': {'1': 'Not at all', '10': 'Extremely'}
                        }
                    }
                ]
            },
            {
                'title': 'Physical Wellbeing',
                'order': 1,
                'questions': [
                    {
                        'question_type': 'rating_scale',
                        'question_text': 'How would you rate your energy levels?',
                        'order': 0,
                        'is_required': True,
                        'config': {
                            'min': 1,
                            'max': 10,
                            'labels': {'1': 'Very Low', '10': 'Very High'}
                        }
                    },
                    {
                        'question_type': 'rating_scale',
                        'question_text': 'How well have you been sleeping?',
                        'order': 1,
                        'is_required': True,
                        'config': {
                            'min': 1,
                            'max': 10,
                            'labels': {'1': 'Very Poorly', '10': 'Excellently'}
                        }
                    }
                ]
            }
        ]
    }
    
    wellbeing = AssessmentTemplate(
        name='Wellbeing Check-In',
        description='Quick weekly wellbeing assessment',
        category=TemplateCategory.WELLBEING,
        author='PsychSync Official',
        is_official=True,
        is_public=True,
        template_data=json.dumps(wellbeing_data)
    )
    db.add(wellbeing)
    
    db.commit()
    print("✓ Seeded 3 official templates")
    print("  - Big Five Personality Assessment")
    print("  - Basic Cognitive Assessment")
    print("  - Wellbeing Check-In")

if __name__ == "__main__":
    print("Seeding official templates...")
    seed_templates()
    print("Template seeding complete!")
    
    