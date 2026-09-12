import speech_recognition as sr

recognizer = sr.Recognizer()

print("=" * 60)
print("NEXIS MICROPHONE TEST")
print("=" * 60)

devices = sr.Microphone.list_microphone_names()

for i, name in enumerate(devices):
    print(f"{i}: {name}")

print()

index = int(input("Enter microphone number to test: "))

microphone = sr.Microphone(device_index=index)

print()
print("Calibrating...")

with microphone as source:

    recognizer.adjust_for_ambient_noise(
        source,
        duration=0.5
    )

    print("Say: hello NEXIS")

    audio = recognizer.listen(
        source,
        timeout=8,
        phrase_time_limit=8
    )

print()
print("Recognising...")

try:

    result = recognizer.recognize_google(
        audio,
        language="en-US"
    )

    print()
    print("RESULT:", repr(result))

except sr.UnknownValueError:

    print("RESULT: Speech not understood.")

except sr.RequestError as error:

    print("Speech service error:", error)