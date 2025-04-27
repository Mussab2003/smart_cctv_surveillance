from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from ai_models.serializers.serializer_vehicle import VehicleSerializer, VehicleLocationUpdateSerializer
from ai_models.models import Vehicle
from ai_models.utils.supabase_upload import uploadFileToSupabase, getSupabaseFilePath

class VehicleView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Create a new vehicle"""
        try:
            user = request.user
            serializer = VehicleSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            
            vehicle_name = serializer.validated_data['vehicle_name']
            registration_number = serializer.validated_data.get('registration_number', None)
            
            # Check if vehicle already exists
            if Vehicle.objects.filter(owner=user, vehicle_name=vehicle_name).exists():
                return Response(
                    {"error": "You already have a vehicle with this name."},
                    status=status.HTTP_409_CONFLICT
                )
            
            vehicle = Vehicle.objects.create(
                owner=user,
                vehicle_name=vehicle_name,
                registration_number=registration_number
            )
            
            return Response({
                "message": "Vehicle added successfully.",
                "vehicle_name": vehicle.vehicle_name,
                "registration_number": vehicle.registration_number,
                "owner": user.username
            }, status=status.HTTP_201_CREATED)
        
        except Exception as err:
            print(err)
            return Response({'error': str(err)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, vehicle_id):
        """Update an existing vehicle"""
        try:
            user = request.user
            try:
                vehicle = Vehicle.objects.get(id=vehicle_id, owner=user)
            except Vehicle.DoesNotExist:
                return Response({"error": "Vehicle not found."}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = VehicleSerializer(vehicle, data=request.data, partial=True)
            
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            
            updated_vehicle_name = serializer.validated_data.get('vehicle_name')
            if updated_vehicle_name and Vehicle.objects.filter(owner=user, vehicle_name=updated_vehicle_name).exclude(id=vehicle_id).exists():
                return Response(
                    {"error": "You already have a different vehicle with this name."},
                    status=status.HTTP_409_CONFLICT
                )
            
            serializer.save()

            return Response({
                "message": "Vehicle updated successfully.",
                "vehicle": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as err:
            print(err)
            return Response({'error': str(err)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, vehicle_id):
        """Delete a vehicle"""
        try:
            user = request.user
            try:
                vehicle = Vehicle.objects.get(id=vehicle_id, owner=user)
            except Vehicle.DoesNotExist:
                return Response({"error": "Vehicle not found."}, status=status.HTTP_404_NOT_FOUND)
            
            vehicle.delete()
            return Response({"message": "Vehicle deleted successfully."}, status=status.HTTP_200_OK)

        except Exception as err:
            print(err)
            return Response({'error': str(err)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VehicleLocationUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    
    def post(self, request):
        """Update vehicle location"""
        try:
            user = request.user
            
            serializer = VehicleLocationUpdateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

            
            vehicle_id = serializer.validated_data['vehicle_id']
            image = serializer.validated_data['reference_image']
            vehicle_location_x = serializer.validated_data['vehicle_location_x']
            vehicle_location_y = serializer.validated_data['vehicle_location_y']
            
            try:
                vehicle = Vehicle.objects.get(id=vehicle_id, owner=user)
            except Vehicle.DoesNotExist:
                return Response({"error": "Vehicle not found."}, status=status.HTTP_404_NOT_FOUND)
            
            #File Properties
            file_name = f"vehicle_{vehicle_id}_{request.user.username}"
            file_ext = image.name.split('.')[-1]
            
            try:
                response = uploadFileToSupabase('reference_images', 'image', file_name, file_ext, image.read())
                print(response)
            except Exception as upload_error:
                print("Upload failed:", upload_error)
                return Response({'error': str(upload_error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            file_path = getSupabaseFilePath(file_name, 'reference_images')
            print(file_path)
            
            vehicle = Vehicle.objects.filter(id = vehicle_id).update(reference_image = file_path, vehicle_location_x = vehicle_location_x, vehicle_location_y = vehicle_location_y)
            
            return Response({
                "message": "Vehicle location updated successfully.",
                "vehicle_name": vehicle.vehicle_name,
                "registeration_number": vehicle.registeration_number,
                "vehicle_location_x" : vehicle.vehicle_location_x,
                "vehicle_location_x" : vehicle.vehicle_location_y,
                "reference_image" : vehicle.reference_image,
            }, status=status.HTTP_200_OK)

        except Exception as err:
            print(err)
            return Response({'error': str(err)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
