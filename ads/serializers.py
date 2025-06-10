from rest_framework import serializers
from .models import Ad, ExchangeProposal

class AdSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = Ad
        fields = ['id', 'user', 'title', 'description', 'image_url', 
                 'category', 'condition', 'created_at']

class ExchangeProposalSerializer(serializers.ModelSerializer):
    sender_username = serializers.ReadOnlyField(source='ad_sender.user.username')
    receiver_username = serializers.ReadOnlyField(source='ad_receiver.user.username')
    
    class Meta:
        model = ExchangeProposal
        fields = ['id', 'ad_sender', 'ad_receiver', 'sender_username',
                 'receiver_username', 'comment', 'status', 'created_at']
