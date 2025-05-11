from django.shortcuts import render
from django.contrib.auth import get_user_model, authenticate
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from ai_models.serializers.serializer_user import LoginSerializer, RegisterSerializer, UserSerializer
from ai_models.models import FacialEmbedding, DetectionEvent
from rest_framework.parsers import MultiPartParser, FormParser
import cv2
import torch
import numpy as np
from facenet_pytorch import InceptionResnetV1
from ultralytics import YOLO
from rest_framework.pagination import PageNumberPagination

User = get_user_model()

# User Views
class RegisterUser(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = request.data
            serializer = RegisterSerializer(data=data)
            
            #Checking if valid inputs are provided
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            
            email = serializer.data['email_address']
            username = serializer.data['username']
            password = serializer.data['password']
            
            #Checking if email already exists
            user = User.objects.filter(email = email).exists()
            if user:
                return Response({'error' : 'Email already exists'}, status=status.HTTP_409_CONFLICT)
            
            #Creating User
            User.objects.create_user(email=email, username=username, password=password)
            return Response({'success' : 'User created successfully'}, status=status.HTTP_201_CREATED)

        except Exception as err:
            print(err)
            return Response({'error' : 'Internal Server Error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)     

class LoginUser(APIView):
    permission_classes = [AllowAny]        

    def post(self, request):
        try:
            data = request.data
            serializer = LoginSerializer(data=data)

            #Checking if valid inputs are provided
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            
            email = serializer.data['email_address']
            password = serializer.data['password'] 

            #Validating email and password
            user = authenticate(email=email, password=password)
            if not user:
                return Response({'error' : 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)
            
            #Generating refresh and access token
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh' : str(refresh),
                'access' : str(refresh.access_token) 
            })
        
        except Exception as err:
            print(err)
            return Response({'error' : 'Internal Server Error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user(request):
    try:
        user = User.objects.get(id = request.user.id)
        if not user:
            return Response({'error' : 'User not found'}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as err:
        print(err)
        return Response({'error' : 'Internal Server Error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GenerateFacialEmbedding(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        try:
            if 'image' not in request.FILES:
                return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)

            # Initialize models
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            facenet = InceptionResnetV1(pretrained='vggface2').eval().to(device)
            model = YOLO('ai_models/ai/authorized_person_detection/face_detection.pt')

            # Read and process image
            image_file = request.FILES['image']
            img_array = np.frombuffer(image_file.read(), np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            if img is None:
                return Response({'error': 'Could not read image'}, status=status.HTTP_400_BAD_REQUEST)

            # Detect face
            results = model(img)
            face_detected = False
            face_embedding = None

            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    face = img[y1:y2, x1:x2]
                    
                    if face.size == 0:
                        continue

                    # Preprocess face
                    face = cv2.resize(face, (160, 160))
                    face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
                    face = face / 255.0
                    face = (face - 0.5) / 0.5
                    face_tensor = torch.tensor(face.transpose(2, 0, 1)).unsqueeze(0).float().to(device)

                    # Generate embedding
                    with torch.no_grad():
                        embedding = facenet(face_tensor)
                        face_embedding = embedding.cpu().numpy().tolist()
                        face_detected = True
                        break
                if face_detected:
                    break

            if not face_detected:
                return Response({'error': 'No face detected in the image'}, status=status.HTTP_400_BAD_REQUEST)

            # Save embedding to database
            embedding_obj = FacialEmbedding.objects.create(
                user=request.user,
                embedding_vector=face_embedding
            )

            return Response({
                'message': 'Facial embedding generated and stored successfully',
                'embedding_id': str(embedding_obj.id)
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"Error generating embedding: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DetectionHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get all detection events for the user
            events = DetectionEvent.objects.filter(owner=request.user).order_by('-timestamp')
            print(events)
            
            if not events.exists():
                return Response({
                    'count': 0,
                    'next': None,
                    'previous': None,
                    'results': []
                }, status=status.HTTP_200_OK)
            
            # Manual pagination
            page = request.query_params.get('page', 1)
            page_size = request.query_params.get('page_size', 10)
            
            try:
                page = int(page)
                page_size = int(page_size)
            except ValueError:
                page = 1
                page_size = 10
            
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            
            total_count = events.count()
            paginated_events = events[start_index:end_index]
            
            # Prepare response data
            events_data = []
            for event in paginated_events:
                vehicle_data = None
                if event.vehicle:
                    vehicle_data = {
                        'id': str(event.vehicle.id),
                        'vehicle_name': event.vehicle.vehicle_name,
                        'registration_number': event.vehicle.registration_number
                    }
                
                event_data = {
                    'id': str(event.id),
                    'event_type': event.event_type,
                    'timestamp': event.timestamp,
                    'description': event.description or '',
                    'is_alert_sent': event.is_alert_sent,
                    'video_frame': event.video_frame or None,
                    'vehicle': vehicle_data
                }
                events_data.append(event_data)
            
            # Prepare pagination response
            response_data = {
                'count': total_count,
                'next': f"?page={page + 1}" if end_index < total_count else None,
                'previous': f"?page={page - 1}" if page > 1 else None,
                'results': events_data
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as err:
            print(f"Error in DetectionHistoryView: {str(err)}")
            return Response(
                {'error': 'Failed to fetch detection history'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    
        