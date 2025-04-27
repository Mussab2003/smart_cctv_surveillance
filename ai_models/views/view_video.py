import tempfile
import cv2
import base64
import random

from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from ai_models.serializers.serializer_video import VideoUploadSerializer, VideoStreamSerializer
from ai_models.utils.supabase_upload import uploadFileToSupabase, getSupabaseFilePath
from ai_models.models import Video



class VideoUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    
    def post(self, request):
        try:
            print(request.user.id)
            serializer = VideoUploadSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({'error' : serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
            video_file = serializer.validated_data['video']
            
            # File properties
            file_name = f"user_{request.user.id}_{video_file.name}"
            file_ext = video_file.name.split('.')[-1]
            
            try:
                response = uploadFileToSupabase('videos', 'video', file_name, file_ext, video_file.read())
                print(response)
            except Exception as upload_error:
                print("Upload failed:", upload_error)
                return Response({'error': str(upload_error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            file_path = getSupabaseFilePath(file_name, 'videos')
            print(file_path)
            # Saving Video Path to database
            print("saving file to db")
            video = Video.objects.create(
                owner = request.user,
                video_type = 'upload',
                video_url = file_path,
            )
            print("Saved file to db")
            
            return Response({
                "message": "Video uploaded successfully.",
                "video_url": file_path
            }, status=status.HTTP_201_CREATED)
        
        except Exception as err:
            print(err)
            return Response({'error' : err}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class VideoStreamView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = VideoStreamSerializer()
            if not serializer.is_valid():
               return Response({'error' : serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
           
            stream_url = serializer.validated_data['stream_url']
            
            video = Video.objects.create(
                owner=request.user,
                video_type='stream',
                video_url=stream_url
            )

            return Response({
                "message": "Stream registered successfully.",
                "video_id": video.id,
                "video_url": stream_url
            }, status=status.HTTP_201_CREATED)
           
            
        except Exception as err:
            print(err)
            return Response({'error' : err}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 
        
class FrameExtractView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            
            video = Video.objects.filter(owner = user).first()
            print(video)
            if video is None:
                return Response({'error' : 'no video or stream linked with the user'}, status=status.HTTP_400_BAD_REQUEST)

            if video.video_type == 'upload':
                cap = cv2.VideoCapture(video.video_url)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

                if total_frames == 0:
                    return Response({"error": "Could not read video"}, status=500)

                extracted = []

                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
                if ret:
                    _, buffer = cv2.imencode(".jpg", frame)
                    frame_base64 = base64.b64encode(buffer).decode("utf-8")
                    extracted.append(f"data:image/jpeg;base64,{frame_base64}")


                random_frames = random.sample(range(0, total_frames), 5)
                for frame_idx in random_frames:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                    ret, frame = cap.read()
                    if ret:
                        _, buffer = cv2.imencode(".jpg", frame)
                        frame_base64 = base64.b64encode(buffer).decode("utf-8")
                        extracted.append(f"data:image/jpeg;base64,{frame_base64}")

                cap.release()

                # Return the extracted frames
                return Response({"frames": extracted}, status=200)

            return Response({"error": "Live stream support not implemented yet."}, status=501)
        
        except Exception as err:
            print(err)
            return Response({'error' : err}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    


