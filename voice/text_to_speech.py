import pyttsx3


class TextToSpeech:
    """
    Converts NexusAI text responses into speech.
    """

    def __init__(self):
        self.engine = pyttsx3.init()

        # Speech speed
        self.engine.setProperty(
            "rate",
            170
        )

        # Volume
        self.engine.setProperty(
            "volume",
            1.0
        )

    def speak(self, text):
        """
        Convert text into speech.
        """

        if not text:
            return

        self.engine.say(text)

        self.engine.runAndWait()


def main():

    print(
        "\n========== NexusAI Text-to-Speech ==========\n"
    )

    text = input(
        "Enter text: "
    )

    tts = TextToSpeech()

    tts.speak(text)


if __name__ == "__main__":
    main()