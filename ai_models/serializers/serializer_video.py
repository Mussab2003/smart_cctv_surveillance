from rest_framework import serializers

class VideoUploadSerializer(serializers.Serializer):
    video = serializers.FileField()
    
    def validate_video(self, value):
        # restrict file types
        if not value.name.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            raise serializers.ValidationError("Unsupported file format. Only .mp4, .avi, .mov, .mkv are allowed.")
        
        # Optional: Restrict file size ( max 50MB)
        max_size_mb = 50
        if value.size > max_size_mb * 1024 * 1024:
            raise serializers.ValidationError(f"File too large. Max size is {max_size_mb}MB.")
        
        return value
    

class VideoStreamSerializer(serializers.Serializer):
    stream_url = serializers.URLField()
    