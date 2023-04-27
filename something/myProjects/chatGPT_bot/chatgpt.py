import openai
import subprocess
import os

openai.api_key = 'OPENAI_TOKEN'

def gpt_prompt(prompt):
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=prompt
    )

    return response


def gen_image(prompt):
    try:
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="1024x1024"
        )

        return response['data'][0]['url']
    except:
        return False


def audio_to_text(audio_name):
    if '.ogg' in audio_name:
        new_name = f'{audio_name.replace(".ogg", "")}.m4a'
        if not os.path.isfile(new_name):
            subprocess.call(['ffmpeg', '-i', f'{audio_name}', f'{new_name}'])
            os.remove(audio_name)
            audio = open(new_name, 'rb')
            transcript = openai.Audio.transcribe('whisper-1', audio)
            audio.close()
            os.remove(new_name)
        else:
            return 'Error'
    else:
        audio = open(audio_name, 'rb')
        transcript = openai.Audio.transcribe('whisper-1', audio)
        audio.close()
        os.remove(audio_name)

    return transcript['text']