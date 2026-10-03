import os
import config

def create_user_session(user_id: str, dir_path="user_sessions"):
    os.makedirs(dir_path, exist_ok=True)
    filepath = os.path.join(dir_path, f"{user_id}.txt")
    with open(filepath, "w") as f:
        f.write(f"User ID: {user_id}")
    config.USER_ID = user_id
    response = config.supa.table("users") \
                    .select("full_name") \
                    .eq("user_id", user_id) \
                    .single() \
                    .execute()

    data = response.data
    if not data:
        print(f"No name found for user_id {user_id}")
        return None
    config.NAME = data.get("full_name")

def retrieve_gmail_creds(user_id: str):
    response = config.supa.table("email_credentials") \
                   .select("access_token, refresh_token") \
                   .eq("user_id", user_id) \
                   .single() \
                   .execute()

    data = response.data
    if not data:
        print(f"No credentials found for user_id {user_id}")
        return None

    def decode_bytea(value):
        """Decode a Supabase/Postgres bytea hex string to a UTF-8 string."""
        if isinstance(value, str) and value.startswith("\\x"):
            return bytes.fromhex(value[2:]).decode("utf-8")
        return value  # already plain string

    access_token = decode_bytea(data.get("access_token"))
    refresh_token = decode_bytea(data.get("refresh_token"))

    config.ACCESS_TOKEN = access_token
    config.REFRESH_TOKEN = refresh_token

    config.update_creds()

    return access_token, refresh_token
