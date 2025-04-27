from django.shortcuts import render
from django.contrib.auth import get_user_model, authenticate
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from ai_models.serializers.serializer_user import LoginSerializer, RegisterSerializer, UserSerializer

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

    
        