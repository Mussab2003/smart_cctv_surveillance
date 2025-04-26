from rest_framework import serializers
from ai_models.models import Vehicle

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['vehicle_name', 'registration_number']
        
class VehicleLocationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['vehicle_location_x', 'vehicle_location_y']
