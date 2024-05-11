from shortGPT.audio.voice_module import VoiceModule
from shortGPT.gpt import script_gpt
from shortGPT.config.languages import Language
from shortGPT.engine.content_short_engine import ContentShortEngine

class GeneratedScriptShortEngine(ContentShortEngine):

    def __init__(self, voiceModule: VoiceModule, script_description: str, background_video_name: str, background_music_name: str,short_id="",
                 num_images=None, watermark=None, language:Language = Language.ENGLISH):
        super().__init__(short_id=short_id, script_description="no script description",  short_type="custom_script", background_video_name=background_video_name, background_music_name=background_music_name,
                 num_images=num_images, watermark=watermark, language=language, voiceModule=voiceModule)
        
        self._db_custom_script = custom_script

    def _generateScript(self):
        """
        Implements Abstract parent method to generate the script for the Facts short.
        """
        self._db_script = script_gpt.generateScript(self._db_script_description)

