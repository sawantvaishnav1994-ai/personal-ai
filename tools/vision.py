from vision.screen_understanding import ScreenUnderstanding
from tools.registry import Tool, Risk

def register(reg,models,settings):
    vision=ScreenUnderstanding(models=models,data_dir=settings.data_dir)
    reg.register(Tool("screen_understand","Capture current screen and prepare multimodal payload; params: question",
                      lambda p:vision.prepare_payload(str(p.get("question","Describe the visible screen."))),Risk.READ_ONLY))
