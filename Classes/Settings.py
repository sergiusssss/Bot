# coding: utf8

class Settings:
    logger_name = ""
    path_to_logs = "Files/Logs"

    class AdminBot:
        token = "289349761:AAHSovQsmGnq1fvel5LyET9VZ6xaOEa9yPE"
        find_name = "@DearFriendAdminBot"
        name = u"Админ моего друга"
        id = 197525025
        chat = 197525025

    class UserBot:
        token = "214686709:AAFvkp_Hy57jiPJzPqpZE_6lvx4jul3hb_E"
        find_name = "@MyDearFriendBot"
        name = u"Мой друг"

    class MicrosoftAPI:
        class Face:
            url = "https://api.projectoxford.ai/face/v1.0/detect"
            subscription_key = "532e3ed0bd2f417d8c7510050807dab9"

            class Parameters:
                return_face_id = "true"
                return_face_landmarks = "true"
                return_face_attributes = "age,gender"

            class Headers:
                content_type = "application/octet-stream"

        class Emotion:
            url = "https://api.projectoxford.ai/emotion/v1.0/recognize"
            subscription_key = "b70c5660ed3d4b838d0475cd91fd02a6"

            class Headers:
                content_type = "application/octet-stream"

    class Photo:
        path = 'Files/Photo/'

    class Mail:
        username = 'bot-telegram@mail.ru'
        password = 'telemarafon'

    class Processes:
        max_count = 4

    class Networks:
        path_to_models = "Files/Models"

