from rest_framework import serializers

from newsapp.models import News


class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ['id', 'title', 'author', 'content', 'category', 'image_url', 'telegram_author']

    def create(self, validated_data):
        validated_data['moderation_status'] = 'pending'
        return super().create(validated_data)