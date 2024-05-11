from shortGPT.audio.voice_module import VoiceModule
from shortGPT.gpt import facts_gpt
from shortGPT.config.languages import Language
from shortGPT.engine.content_short_engine import ContentShortEngine


class SATEngine(ContentShortEngine):

    def __init__(self, voiceModule: VoiceModule, background_video_name: str, background_music_name: str,short_id="", script=None,
                 num_images=None, watermark=None, language:Language = Language.ENGLISH):
        super().__init__(script=script, short_id=short_id,  short_type="sat", background_video_name=background_video_name, background_music_name=background_music_name,
                 num_images=num_images, watermark=watermark, language=language, voiceModule=voiceModule)
        
    def _generateScript(self):
        """
        Implements Abstract parent method to generate the script for an SAT question.
        """
        self._db_script = sat_gpt.generateSATquestion()


