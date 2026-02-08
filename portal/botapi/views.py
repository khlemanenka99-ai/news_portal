import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from botapi.serializers import NewsSerializer
from newsapp.models import TG_Author

logger = logging.getLogger('api')
class NewsCreateAPIView(APIView):

    def post(self, request):
        logger.info(f"=== ПОЛУЧЕН ЗАПРОС ОТ БОТА ===")
        logger.info(f"Все данные: {request.data}")
        try:
            data = request.data.copy()
            telegram_user_id = data.get('telegram_user_id')
            telegram_username = data.get('telegram_username')
            telegram_author_obj, created = TG_Author.objects.get_or_create(
                telegram_user_id=telegram_user_id,
                telegram_username=telegram_username
            )
            if created:
                logger.info(f"Создан новый TG_Author: {telegram_author_obj.id}")
            else:
                logger.info(f"Найден существующий TG_Author: {telegram_author_obj.id}")

            data['telegram_author'] = telegram_author_obj.id

        except Exception as e:
            logger.error(f"Ошибка при создании TG_Author: {e}")

        serializer = NewsSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.info(f"новость не прошла проверку сериалайзера {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
