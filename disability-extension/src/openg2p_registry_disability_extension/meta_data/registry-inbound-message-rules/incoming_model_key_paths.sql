INSERT INTO "public"."incoming_model_key_paths" ("key_path_id","data_model_id","key_path_for_message_id","key_path_for_sender","key_path_for_signature","key_path_for_signature_payload","is_list","key_path_for_list_elements") VALUES
('KP1','DM1','$.body.header.message_id','$.body.header.sender_id','$.body.signature','$.body.message','FALSE','$.body.message')
ON CONFLICT ("key_path_id") DO NOTHING;
