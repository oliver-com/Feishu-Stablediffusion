import json
from util.app_config import AppConfig
from larksuiteoapi import Config
from feishu.message_sender import MessageSender
from store.chat_history import clean_chat
from util.logger import app_logger
from store.user_prompt import user_prompt
from service.image_configure import ImageConfiguration
from service.stablediffusion import send_api_request
class CommandHandler:
    def __init__(self, app_config: AppConfig, conf: Config):
        if not app_config:
            raise Exception("app_config is required")
        if not conf:
            raise Exception("conf is required")
        self.app_config = app_config
        self.conf = conf
        self.message_sender = MessageSender(self.conf)

    def handle_botmessage(self, body):
        user_id = body["user_id"]
        action_value = body["action"]["value"]

        # {"action": "newchat"}
        if "action" in action_value and action_value["action"] == "newchat":
            app_logger.info("new chat")
            clean_chat(user_id)
            self.message_sender.send_text_message(user_id, "New chat started", append=False)
        # {"action": "prompt"} body.action.option is the selected prompt
        if "option" in body["action"]:
            app_logger.info("set prompt")
            clean_chat(user_id)
            prompt = body["action"]["option"]
            if prompt == "default":
                user_prompt.delete_prompt(user_id)
            else:
                user_prompt.write_prompt(user_id, prompt)
            self.message_sender.send_text_message(user_id, "New prompt selected", append=False)


    def handle_message(self, event):
        image_configuration = ImageConfiguration()
        json_content = json.loads(event.event.message.content)
        if "text" in json_content and json_content["text"].startswith("/"):
            command = json_content["text"]
            if command == "/new":
                app_logger.info("new chat")
                clean_chat(event.event.sender.sender_id.user_id)
                self.message_sender.send_text_message(event.event.sender.sender_id.user_id,"New chat started", append=False)
            elif command.startswith("/prompt "):
                # /prompt <prompt>
                prompt = command[8:]            
                if prompt == "default":
                    user_prompt.delete_prompt(event.event.sender.sender_id.user_id)
                else:
                    user_prompt.write_prompt(event.event.sender.sender_id.user_id, prompt)
                clean_chat(event.event.sender.sender_id.user_id)
                self.message_sender.send_text_message(event.event.sender.sender_id.user_id,"Prompt is set", append=False)
            elif command.startswith("/img "):
                prompt = command[5:]
                self.message_sender.send_text_message(event.event.sender.sender_id.user_id,f"Prompt is \"{prompt}\"", append=False)
                app_logger.info(f"img command: {prompt}")
            elif command.startswith("/help"):
                prompt = command[5:]
                self.message_sender.send_card(event.event.sender.sender_id.user_id, image_configuration.help())
                app_logger.info(f"request /help")
            elif command.startswith("/list_models"):
                prompt = command[5:]
                models_endpoint = "/sdapi/v1/sd-models"
                models = send_api_request(models_endpoint)
                model_names = [data.get('model_name') for data in models]
                self.message_sender.send_card(event.event.sender.sender_id.user_id, image_configuration.list_models(model_names))
                app_logger.info(f"/sdapi/v1/sd-models")
            elif command.startswith("/list_samplers"):
                prompt = command[5:]
                models_endpoint = "/sdapi/v1/samplers"
                samplers = send_api_request(models_endpoint)
                samplers_names = [data.get('samplers_name') for data in samplers]
                self.message_sender.send_card(event.event.sender.sender_id.user_id, image_configuration.list_sampler(samplers_names))
                app_logger.info(f"/sdapi/v1/samplers")
            elif command.startswith("/queue"):
                prompt = command[5:]
                models_endpoint = "/queue/status"
                queue = send_api_request(models_endpoint)
                self.message_sender.send_card(event.event.sender.sender_id.user_id, image_configuration.queue(queue))
                app_logger.info(f"/queue")
            else:
                app_logger.info("unknown command")
                # self.message_sender.send_text_message(event.event.sender.sender_id.user_id, "Unknown command", append=False)
                self.message_sender.send_command_card(event.event.sender.sender_id.user_id)
            return True
