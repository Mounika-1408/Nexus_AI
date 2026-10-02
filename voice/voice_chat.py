from pathlib import Path

from speech_to_text import transcribe_audio
from text_to_speech import TextToSpeech

from langchain_ollama import ChatOllama


# --------------------------------------------------
# NexusAI Voice Assistant
# --------------------------------------------------

class VoiceAssistant:

    def __init__(self):

        self.llm = ChatOllama(
            model="llama3.2",
            temperature=0
        )

        self.tts = TextToSpeech()


    # --------------------------------------------------
    # Process User Question
    # --------------------------------------------------

    def process_question(self, question):
        """
        Send the transcribed question to Llama.
        """

        response = self.llm.invoke(
            question
        )

        return response.content


    # --------------------------------------------------
    # Process Audio
    # --------------------------------------------------

    def process_audio(self, audio_path):
        """
        Complete voice processing pipeline.
        """

        print("\nTranscribing audio...")

        question = transcribe_audio(
            audio_path
        )

        print(f"\nUser: {question}")

        print("\nProcessing with NexusAI...")

        answer = self.process_question(
            question
        )

        print(f"\nNexusAI: {answer}")

        print("\nGenerating voice response...")

        self.tts.speak(answer)


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():

    print(
        "\n========== NexusAI Voice Assistant ==========\n"
    )

    audio_path = input(
        "Enter audio file path: "
    )

    audio_path = Path(audio_path)

    if not audio_path.exists():

        print(
            f"Audio file not found: {audio_path}"
        )

        return

    assistant = VoiceAssistant()

    try:

        assistant.process_audio(
            audio_path
        )

    except Exception as error:

        print(
            f"\nError: {error}"
        )


if __name__ == "__main__":
    main()