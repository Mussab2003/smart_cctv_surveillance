from rest_framework import serializers
from ai_models.models import Vehicle

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['vehicle_name', 'registration_number']
        
class VehicleLocationUpdateSerializer(serializers.Serializer):
    vehicle_id = serializers.CharField()
    vehicle_location_x = serializers.FloatField()
    vehicle_location_y = serializers.FloatField()
    reference_image = serializers.ImageField()
    