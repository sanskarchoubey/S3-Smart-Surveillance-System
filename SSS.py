import tkinter as tk
from PIL import Image, ImageTk
from ultralytics import YOLO
import cv2
import pyaudio
import wave
import threading
from ultralytics.utils.plotting import Annotator
from email.message import EmailMessage
import ssl
import smtplib
from datetime import datetime, timedelta
import io


class ObjectDetectionApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)
        self.window.configure(bg="#f0f0f0")

        self.audio_playing = False

        # Initialize PyAudio
        self.p = pyaudio.PyAudio()

        # Initialize the YOLO model
        self.model = YOLO('yolov8l.pt')

        # Open the camera
        self.cap = cv2.VideoCapture(0)

        # Initialize counts
        self.knife_count = 0
        self.scissors_count = 0

        # Cooldown period for sending email (in seconds)
        self.email_cooldown = 60  # Set to 1 minute

        # Timestamp of the last email sent
        self.last_email_time = None

        # Create GUI elements
        self.canvas = tk.Canvas(window, bg="#f0f0f0", highlightthickness=0)
        self.canvas.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        self.btn_quit = tk.Button(window, text="Quit", command=self.close_app, bg="#ff4d4d", fg="white",
                                  font=("Helvetica", 14, "bold"), padx=20, pady=10, bd=0)
        self.btn_quit.pack(side=tk.BOTTOM, padx=(0, 10), pady=10)

        # Fullscreen toggle
        self.window.bind("f", self.toggle_fullscreen)
        self.window.attributes("-fullscreen", False)
        self.fullscreen = False

        # Start object detection loop
        self.detect_objects()

    def detect_objects(self):
        _, img = self.cap.read()

        # Detect objects using YOLO
        results = self.model.predict(img)

        annotator = Annotator(img)

        for r in results:
            boxes = r.boxes
            for box in boxes:
                b = box.xyxy[0]
                c = box.cls
                detected_object = self.model.names[int(c)]

                if detected_object == 'knife':
                    self.knife_count += 1
                    self.play_audio()
                    self.send_email(detected_object, img)

                elif detected_object == 'scissors':
                    self.scissors_count += 1
                    self.play_audio()
                    self.send_email(detected_object, img)

                annotator.box_label(b, detected_object)

        img = annotator.result()

        # Resize the image to fit the canvas
        img = cv2.resize(img, (self.canvas.winfo_width(), self.canvas.winfo_height()))

        # Convert image for displaying in Tkinter
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        img = ImageTk.PhotoImage(img)

        # Update canvas with the new image
        self.canvas.img = img  # Keep a reference to prevent garbage collection
        self.canvas.create_image(0, 0, anchor=tk.NW, image=img)

        # Schedule the next detection iteration
        self.window.after(10, self.detect_objects)

    def play_audio(self):
        if not self.audio_playing:
            threading.Thread(target=self._play_audio).start()

    def _play_audio(self):
        chunk = 1024
        self.audio_playing = True  # Set audio_playing to True when audio starts playing
        f = wave.open("repeating-alarm-tone-metal-detector.wav", "rb")
        f.rewind()
        data = f.readframes(chunk)
        stream = self.p.open(format=self.p.get_format_from_width(f.getsampwidth()),
                             channels=f.getnchannels(),
                             rate=f.getframerate(),
                             output=True)
        while data:
            stream.write(data)
            data = f.readframes(chunk)
        stream.stop_stream()
        stream.close()
        self.audio_playing = False  # Set audio_playing to False when audio finishes playing

    def send_email(self, detected_object, img):
        # Check if cooldown period has passed since the last email
        if self.last_email_time is None or (datetime.now() - self.last_email_time) >= timedelta(
                seconds=self.email_cooldown):
            threading.Thread(target=self._send_email, args=(detected_object, img)).start()
            self.last_email_time = datetime.now()

    @staticmethod
    def _send_email(detected_object, img):
        current_datetime = datetime.now()
        email_sender = '11anantjain@gmail.com'
        email_pass = 'jrqh hpmr gcff tycj'
        email_receiver = 'jainanant892@gmail.com'

        subject = f"Security Alert - {detected_object.capitalize()} Detected"

        body = f"""Dear User,
        We have detected a {detected_object} in your premises at {current_datetime.strftime("%Y-%m-%d %H:%M:%S")}. 
        For your safety, please take necessary actions.

        Best regards,
        S3 - Smart Security System

        Note: This is an automated alert from your home security system.
        """

        em = EmailMessage()
        em["From"] = email_sender
        em["To"] = email_receiver
        em["Subject"] = subject
        em.set_content(body)

        # Convert OpenCV image to PIL Image
        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

        # Save PIL Image to a BytesIO object
        img_io = io.BytesIO()
        pil_img.save(img_io, 'JPEG')
        img_io.seek(0)

        # Attach the screenshot to the email
        em.add_attachment(img_io.getvalue(), maintype='image', subtype='jpeg', filename='screenshot.jpg')

        context = ssl.create_default_context()

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
            smtp.login(email_sender, email_pass)
            smtp.sendmail(email_sender, email_receiver, em.as_string())

    def close_app(self):
        # Release resources
        self.cap.release()
        cv2.destroyAllWindows()
        self.p.terminate()  # Terminate PyAudio
        self.window.destroy()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.window.attributes("-fullscreen", self.fullscreen)


if __name__ == "__main__":
    # Create a Tkinter window
    root = tk.Tk()
    app = ObjectDetectionApp(root, "S3 - Security System")
    root.mainloop()