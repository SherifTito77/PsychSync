from app.db.models.user import User
from app.services.mental_health_screening import MentalHealthScreeningService


def debug():
    # Check if the method exists on the instance/class
    methods = dir(MentalHealthScreeningService)
    print(f"Methods: {methods}")
    if "_get_or_create_clinical_assessment" in methods:
        print("Method found!")
    else:
        print("Method NOT found!")


if __name__ == "__main__":
    debug()
