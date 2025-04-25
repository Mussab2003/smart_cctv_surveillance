from django.shortcuts import render
from django.contrib.auth import get_user_model, authenticate
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import LoginSerializer, RegisterSerializer, CreateTaskSerializer, TaskSerializer, UserSerializer
from api.models import Task as TaskModel

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

#Tasks Views
class Task(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:   
            user_id = request.user.id
            tasks = TaskModel.objects.filter(user_id = user_id)
            serializer = TaskSerializer(tasks, many=True)
            return Response(serializer.data)
        except Exception as err:
            print(err)
            return Response({'error' : 'Internal Server Error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            data = request.data
            serializer = CreateTaskSerializer(data=data)
            
            #Checking if valid inputs are provided
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            
            task_name = serializer.data['name']
            task_due_date = serializer.data['due_date']

            #get the user instance
            user = User.objects.get(id = request.user.id)
            
            if not user:
                return Response({'error' : 'User not found'}, status=status.HTTP_401_UNAUTHORIZED)


            #Creating Task
            task = TaskModel.objects.create(name = task_name, due_date = task_due_date, user_id = user)
            
            description = request.data.get('description', None)
            if description:
                task.description = description
                task.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as err:
            print(err)
            return Response({'error' : 'Internal Server Error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def patch(self, request):
        try:
            data = request.data
            id = request.data.get('id', None)
            user_id = request.user.id

            #Check if task id is provided
            if not id:
                return Response({'error' : 'Task Id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            
            #check if task id is valid
            if not TaskModel.objects.filter(id = id).exists():
                return Response({'error' : 'Invalid task id'}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)
            
            task = TaskModel.objects.get(id = id)

            #Check if the user is the ownwer of the task
            if task.user_id != user_id:
                return Response({'error' : 'Invalid User'}, status=status.HTTP_401_UNAUTHORIZED)

            serializer = TaskSerializer(task, data = data, partial = True)

            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            
            #Updating task
            serializer.save()

            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as err:
            print(err)
            return Response({'error' : 'Internal Server Error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request):
        try:
            id = request.data.get('id', None)
            user_id = request.user.id
            #Check if task id is provided
            if not id:
                return Response({'error' : 'Task Id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            #check if task id is valid
            if not TaskModel.objects.filter(id = id).exists():
                return Response({'error' : 'Invalid task id'}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)
            
            task = TaskModel.objects.get(id = id)
            
            #Check if the user is the ownwer of the task
            if task.user_id != user_id:
                return Response({'error' : 'Invalid User'}, status=status.HTTP_401_UNAUTHORIZED)
            
            task.delete()
            return Response({'success' : 'Successfully deleted task'}, status=status.HTTP_200_OK)

        except Exception as err:
            print(err)
            return Response({'error' : 'Internal Server Error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def completed_task(request):
    try:
        task_id = request.data.get('id', None)
        user_id = request.user.id

        #Check if task id is provided
        if not task_id:
            return Response({'error' : 'Task Id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        #check if task id is valid
        if not TaskModel.objects.filter(id = task_id).exists():
            return Response({'error' : 'Invalid task id'}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)
        
        task = TaskModel.objects.get(id = task_id)
        
        #Check if the user is the ownwer of the task
        if task.user_id != user_id:
            return Response({'error' : 'Invalid User'}, status=status.HTTP_401_UNAUTHORIZED)
        
        #Updating the status to complete
        task.status = 'COMPLETED'
        task.save()
        return Response({'success' : 'Task status updated'}, status=status.HTTP_200_OK)
    except Exception as err:
        print(err)
        return Response({'error' : 'Internal Server Error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
        