from ai_models.lib.supabase_client import supabase

def uploadFileToSupabase(file_name, file_ext, file):
    try:
        print("Inside this func")

        try:
            # Try to get the bucket
            bucket = supabase.storage.get_bucket("videos")
            print("Bucket exists:", bucket)

        except Exception as e:
            # If not found, create the bucket
            if e.message == "Bucket not found":
                print("Bucket not found. Creating bucket...")
                supabase.storage.create_bucket("videos", options={"public": True})
                print("bucket created")
            else:
                raise  # re-raise other storage errors

        # Upload file after ensuring bucket exists
        result = supabase.storage.from_("videos").upload(file_name, file, {
            "content-type" : f"video/{file_ext}"
        })

        print("Upload success")
        return {"status": "success", "data": result}

    except Exception as err:
        raise Exception(f"Upload Error: {str(err)}")


def getSupabaseFilePath(file_name, bucket_name):
    public_url = supabase.storage.from_('videos').get_public_url(file_name)
    return public_url