class UserMapper:
    def map_user_to_dto(self, user):
        return user.__dict__

    def map_dto_to_user(self, dto):
        return dto
