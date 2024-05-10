import os
import traceback

import gradio as gr

from gui.asset_components import AssetComponentsUtils
from gui.ui_abstract_component import AbstractComponentUI
from gui.ui_components_html import GradioComponentsHTML
from shortGPT.audio.edge_voice_module import EdgeTTSVoiceModule
from shortGPT.audio.eleven_voice_module import ElevenLabsVoiceModule
from shortGPT.audio.coqui_voice_module import CoquiVoiceModule
from shortGPT.config.api_db import ApiKeyManager
from shortGPT.config.languages import (EDGE_TTS_VOICENAME_MAPPING,
                                       ELEVEN_SUPPORTED_LANGUAGES,
                                       COQUI_SUPPORTED_LANGUAGES,
                                       LANGUAGE_ACRONYM_MAPPING,
                                       Language)
from shortGPT.engine.facts_short_engine import FactsShortEngine
from shortGPT.engine.reddit_short_engine import RedditShortEngine
from shortGPT.engine.custom_script_engine import CustomScriptShortEngine
from shortGPT.gpt import script_gpt

class ShortAutomationUI(AbstractComponentUI):
    def __init__(self, shortGptUI: gr.Blocks):
        self.shortGptUI = shortGptUI
        self.embedHTML = '<div style="display: flex; overflow-x: auto; gap: 20px;">'
        self.progress_counter = 0
        self.short_automation = None

    def generate_script_from_description(self, description):
        generated_script = script_gpt.generateScript(description)
        return generated_script

    def create_ui(self):
        with gr.Row(visible=False) as short_automation:
            with gr.Column():
                numShorts = gr.Number(label="Number of shorts", minimum=1, value=1)
                short_type = gr.Radio(["Reddit Story shorts", "Historical Facts shorts", "Scientific Facts shorts", "Custom Facts shorts", "Custom Script"], label="Type of shorts generated", value="Scientific Facts shorts", interactive=True)
                custom_script = gr.Textbox(label="Write out your own script", interactive=True, visible=False)
                facts_subject = gr.Textbox(label="Write a subject for your facts (example: Football facts)", interactive=True, visible=False)
                short_type.change(lambda x: gr.update(visible=x == "Custom Facts shorts"), [short_type], [facts_subject])
                short_type.change(lambda x: gr.update(visible=x == "Custom Script"), [short_type], [custom_script])

                with gr.Column(visible=True) as script_generator:
                    # Add a textbox for custom script description
                    script_description = gr.Textbox(label="Enter your custom script description", placeholder="Type here...", interactive=True)
                    
                    # Add a button to generate script
                    generate_script_button = gr.Button("Generate Script")
                    
                    # Output area for the generated script
                    generated_script_output = gr.Textbox(label="Generated Script", interactive=False, visible=True)
                    
                    # Button click event
                    generate_script_button.click(
                        self.generate_script_from_description,
                        inputs=[script_description],
                        outputs=[generated_script_output]
                    )

                tts_engine = gr.Radio([AssetComponentsUtils.ELEVEN_TTS, AssetComponentsUtils.EDGE_TTS, AssetComponentsUtils.COQUI_TTS], label="Text to speech engine", value=AssetComponentsUtils.ELEVEN_TTS, interactive=True)
                self.tts_engine = tts_engine.value
                with gr.Column(visible=True) as eleven_tts:
                    language_eleven = gr.Radio([lang.value for lang in ELEVEN_SUPPORTED_LANGUAGES], label="Language", value="English", interactive=True)
                    voice_eleven = AssetComponentsUtils.voiceChoice(provider=AssetComponentsUtils.ELEVEN_TTS)
                with gr.Column(visible=False) as edge_tts:
                    language_edge = gr.Dropdown([lang.value.upper() for lang in Language], label="Language", value="ENGLISH", interactive=True)
                with gr.Column(visible=False) as coqui_tts:
                    language_coqui = gr.Radio([lang.value for lang in COQUI_SUPPORTED_LANGUAGES], label="Language", value="English", interactive=True)
                    voice_coqui = AssetComponentsUtils.voiceChoice(provider=AssetComponentsUtils.COQUI_TTS)

                def tts_engine_change(x):
                    self.tts_engine = x
                    return gr.update(visible=x == AssetComponentsUtils.ELEVEN_TTS), gr.update(visible=x == AssetComponentsUtils.EDGE_TTS), gr.update(visible=x == AssetComponentsUtils.COQUI_TTS)
                tts_engine.change(tts_engine_change, tts_engine, [eleven_tts, edge_tts, coqui_tts])

                useImages = gr.Checkbox(label="Use images", value=True)
                numImages = gr.Radio([5, 10, 25], value=25, label="Number of images per short", visible=True, interactive=True)
                useImages.change(lambda x: gr.update(visible=x), useImages, numImages)

                addWatermark = gr.Checkbox(label="Add watermark")
                watermark = gr.Textbox(label="Watermark (your channel name)", visible=False)
                addWatermark.change(lambda x: gr.update(visible=x), [addWatermark], [watermark])

                AssetComponentsUtils.background_video_checkbox()
                AssetComponentsUtils.background_music_checkbox()

                createButton = gr.Button(label="Create Shorts")

                generation_error = gr.HTML(visible=True)
                video_folder = gr.Button("📁", visible=True)
                output = gr.HTML()

            video_folder.click(lambda _: AssetComponentsUtils.start_file(os.path.abspath("videos/")))

            createButton.click(self.inspect_create_inputs, inputs=[AssetComponentsUtils.background_video_checkbox(), AssetComponentsUtils.background_music_checkbox(), watermark, short_type, facts_subject, custom_script], outputs=[generation_error]).success(self.create_short, inputs=[
                numShorts,
                short_type,
                tts_engine,
                language_eleven,
                language_edge,
                language_coqui,
                numImages,
                watermark,
                AssetComponentsUtils.background_video_checkbox(),
                AssetComponentsUtils.background_music_checkbox(),
                facts_subject,
                custom_script,
                voice_eleven,
                voice_coqui
            ], outputs=[output, video_folder, generation_error])
        self.short_automation = short_automation
        return self.short_automation

    def create_short(self, numShorts, short_type, tts_engine, language_eleven, language_edge, language_coqui, numImages, watermark, background_video_list, background_music_list, facts_subject, custom_script, voice_eleven, voice_coqui, progress=gr.Progress()):
        '''Creates a short'''
        try:
            numShorts = int(numShorts)
            numImages = int(numImages) if numImages else None
            background_videos = (background_video_list * ((numShorts // len(background_video_list)) + 1))[:numShorts]
            background_musics = (background_music_list * ((numShorts // len(background_music_list)) + 1))[:numShorts]
            if tts_engine == AssetComponentsUtils.ELEVEN_TTS:
                language = Language(language_eleven.lower().capitalize())
                voice_module = ElevenLabsVoiceModule(ApiKeyManager.get_api_key('ELEVEN LABS'), voice_eleven, checkElevenCredits=True)
            elif tts_engine == AssetComponentsUtils.EDGE_TTS:
                language = Language(language_edge.lower().capitalize())
                voice_module = EdgeTTSVoiceModule(EDGE_TTS_VOICENAME_MAPPING[language]['male'])
            elif tts_engine == AssetComponentsUtils.COQUI_TTS:
                language = Language(language_coqui.lower().capitalize())
                voice_module = CoquiVoiceModule(voice_coqui, LANGUAGE_ACRONYM_MAPPING[language])
            for i in range(numShorts):
                shortEngine = self.create_short_engine(short_type=short_type, voice_module=voice_module, language=language, numImages=numImages, watermark=watermark,
                                                       background_video=background_videos[i], background_music=background_musics[i], facts_subject=facts_subject, custom_script=custom_script)
                num_steps = shortEngine.get_total_steps()

                def logger(prog_str):
                    progress(self.progress_counter / (num_steps * numShorts), f"Making short {i+1}/{numShorts} - {prog_str}")
                shortEngine.set_logger(logger)

                for step_num, step_info in shortEngine.makeContent():
                    progress(self.progress_counter / (num_steps * numShorts), f"Making short {i+1}/{numShorts} - {step_info}")
                    self.progress_counter += 1

                video_path = shortEngine.get_video_output_path()
                current_url = self.shortGptUI.share_url+"/" if self.shortGptUI.share else self.shortGptUI.local_url
                file_url_path = f"{current_url}file={video_path}"
                file_name = video_path.split("/")[-1].split("\\")[-1]
                self.embedHTML += f'''
                <div style="display: flex; flex-direction: column; align-items: center;">
                    <video width="{250}" height="{500}" style="max-height: 100%;" controls>
                        <source src="{file_url_path}" type="video/mp4">
                        Your browser does not support the video tag.
                    </video>
                    <a href="{file_url_path}" download="{file_name}" style="margin-top: 10px;">
                        <button style="font-size: 1em; padding: 10px; border: none; cursor: pointer; color: white; background: #007bff;">Download Video</button>
                    </a>
                </div>'''
                yield self.embedHTML + '</div>', gr.Button.update(visible=True), gr.update(visible=False)
        except Exception as e:
            traceback_str = ''.join(traceback.format_tb(e.__traceback__))
            error_name = type(e).__name__.capitalize() + " : " + f"{e.args[0]}"
            print("Error", traceback_str)
            error_html = GradioComponentsHTML.get_html_error_template().format(error_message=error_name, stack_trace=traceback_str)
            yield self.embedHTML + '</div>', gr.Button.update(visible=True), gr.HTML.update(value=error_html, visible=True)

    def inspect_create_inputs(self, background_video_list, background_music_list, watermark, short_type, facts_subject, custom_script):
        if short_type == "Custom Script":
            if not custom_script:
                raise gr.Error("Please write out your script.")
        if short_type == "Custom Facts shorts":
            if not facts_subject:
                raise gr.Error("Please write down your facts short's subject")
        if not background_video_list:
            raise gr.Error("Please select at least one background video.")

        if not background_music_list:
            raise gr.Error("Please select at least one background music.")

        if watermark != "":
            if not watermark.replace(" ", "").isalnum():
                raise gr.Error("Watermark should only contain letters and numbers.")
            if len(watermark) > 25:
                raise gr.Error("Watermark should not exceed 25 characters.")
            if len(watermark) < 3:
                raise gr.Error("Watermark should be at least 3 characters long.")

        openai_key = ApiKeyManager.get_api_key("OPENAI")
        if not openai_key:
            raise gr.Error("OPENAI API key is missing. Please go to the config tab and enter the API key.")
        eleven_labs_key = ApiKeyManager.get_api_key("ELEVEN LABS")
        if self.tts_engine == AssetComponentsUtils.ELEVEN_TTS and not eleven_labs_key:
            raise gr.Error("ELEVEN LABS API key is missing. Please go to the config tab and enter the API key.")
        return gr.update(visible=False)

    def create_short_engine(self, short_type, voice_module, language, numImages, watermark, background_video, background_music, facts_subject, custom_script):
        if short_type == "Reddit Story shorts":
            return RedditShortEngine(voice_module, background_video_name=background_video, background_music_name=background_music, num_images=numImages, watermark=watermark, language=language)
        if "fact" in short_type.lower():
            if "custom" in short_type.lower():
                facts_subject = facts_subject
            else:
                facts_subject = short_type
            return FactsShortEngine(voice_module, facts_type=facts_subject, background_video_name=background_video, background_music_name=background_music, num_images=50, watermark=watermark, language=language)
        if short_type == "Custom Script":
            print("Creating short with Custom Script")
            return CustomScriptShortEngine(voice_module, custom_script=custom_script, background_video_name=background_video, background_music_name=background_music, num_images=50, watermark=watermark, language=language)
        raise gr.Error(f"Short type does not have a valid short engine: {short_type}")
