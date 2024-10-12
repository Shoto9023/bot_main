from interactions.api.voice.audio import AudioVolume
from interactions import (
    ActiveVoiceState,
)
from google.cloud import texttospeech
from functions import log
import os, random, datetime, string, re

service_account = "./tts-mesugaki-865604b60d28.json"
tts_client = texttospeech.TextToSpeechClient.from_service_account_json(service_account)
queue = []

tts_dict : dict = {}

def initialize_tts_dict():
    global tts_dict
    log("initializing dictionary...")
    with open("./tts/tts_dict.csv", newline='', encoding="utf-8") as f:
        items = []
        with open("./tts/tts_dict.csv", newline='') as f:
            items = f.readlines()
        for item in items:
            tts_dict[item.split()[0]] = item.split()[1]
    return tts_dict

async def tts_play(text:str, voice_state:ActiveVoiceState):
    global queue
    log("tts_play")
    text = re.sub(r"[\w\-._]+@[\w\-._]+\.[A-Za-z]+", " メールアドレス ", text)
    if re.match(r"src='https?://[\w!\?/\+\-_~=;\.,\*&@#\$%\(\)'\[\]]+'",text):
        pass
    elif re.match(r"https?://[\w!\?/\+\-_~=;\.,\*&@#\$%\(\)'\[\]]+",text):
        text = re.sub(r"https?://[\w!\?/\+\-_~=;\.,\*&@#\$%\(\)'\[\]]+", " URL ", text)
    if re.match(r"<:(.+):[0-9]+>", text):
        s = re.match(r"<:(.+):[0-9]+>", text)
        replacer = s.group(1).replace("_"," ")
        text = text.replace(s.group(), replacer)
    if re.match(r"<a:(.+):[0-9]+>", text):
        s = re.match(r"<a:(.+):[0-9]+>", text)
        replacer = s.group(1).replace("_"," ")
        text = text.replace(s.group(), replacer)
    for k, v in tts_dict.items():
        text = text.replace(k, v)
    file = text_to_audio_file(text)
    queue.append(file)

    if not voice_state.playing:
        log("not current audio! play!")
        await play_audio(voice_state)
        log("queue done!")
        await voice_state.stop()
    else:
        log("current audio! queuing!")

def text_to_audio_file(text:str) -> str:
    log("text_to_audio_file")
    with open("./tts/tts_settings", "r") as f:
        settings = f.readlines()
    voice_name = ""
    gender = ""
    for item in settings:
        s = item.split(":")
        if s[0] == "name": voice_name = s[1].rstrip('\r\n')
        if s[0] == "gender": gender = s[1].rstrip('\r\n')

    if gender == "男性": gender_num = 1
    if gender == "女性": gender_num = 2
    if gender == "中世": gender_num = 3

    ssml = "<speak>{}</speak>".format(
        text.replace("\n", '\n<break time="1s"/>')
    )

    text = texttospeech.SynthesisInput(ssml=ssml)
    voice = texttospeech.VoiceSelectionParams(
        language_code="ja-JP",
        name=voice_name,
        ssml_gender=gender_num,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    log(f"synthesizing content: {ssml}")
    response = tts_client.synthesize_speech(
        input=text, voice=voice, audio_config=audio_config
    )

    now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    salt = ''.join(random.choices(string.ascii_letters+string.digits, k=8))
    with open(f"./tts/tts_{now}_{salt}.mp3", "wb") as out:
        out.write(response.audio_content)
        log(f"saved tts file: ./tts/tts_{now}_{salt}.mp3 : {voice_name}, {gender}")

    return f"./tts/tts_{now}_{salt}.mp3"

async def play_audio(voice_state:ActiveVoiceState):
    log("play_audio")
    if not queue: return
    file = queue.pop(0)
    audio = AudioVolume(file)
    await voice_state.play(audio)
    os.remove(file)
    log(f"audio play finished: {file}")
    await play_audio(voice_state)