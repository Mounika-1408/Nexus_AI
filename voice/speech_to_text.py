from pathlib import Path

import whisper


# --------------------------------------------------
# Whisper Model
# --------------------------------------------------

MODEL_NAME = "base"


def load_whisper_model():
    """
    Load the Whisper speech-to-text model.
    """

    print("Loading Whisper model...")

    model = whisper.load_model(MODEL_NAME)

    print("Whisper model loaded.")

    return model


# --------------------------------------------------
# Speech to Text
# --------------------------------------------------

def transcribe_audio(audio_path):
    """
    Convert an audio file into text.
    """

    audio_path = Path(audio_path)

    if not audio_path.exists():
        raise FileNotFoundError(
            f"Audio file not found: {audio_path}"
        )

    model = load_whisper_model()

    result = model.transcribe(
        str(audio_path)
    )

    text = result["text"].strip()

    return text


# --------------------------------------------------
# Command Line Test
# --------------------------------------------------

def main():

    print("\n========== NexusAI Speech-to-Text ==========\n")

    audio_path = input(
        "Enter audio file path: "
    )

    try:

        text = transcribe_audio(
            audio_path
        )

        print("\nTranscribed Text:")
        print(text)

    except Exception as error:

        print(
            f"\nError: {error}"
        )


if __name__ == "__main__":
    main()