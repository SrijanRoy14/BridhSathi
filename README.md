**BridhSathi** is a compassionate initiative designed to assist elderly individuals in quickly seeking help without relying on complicated smartphone apps. Instead, it uses simple hand gestures to trigger messages to their loved ones, based on actions detected by an edge-based FOMO AI model with minimal latency.

Originally intended to leverage the ESP32-EYE MCU for real-time gesture recognition, I adapted the project to work with a standard ESP32 for testing purposes. The goal was to capture image buffers from my laptop, transmit them to the ESP32 in real-time with low latency, and perform predictions on the image buffer.

### Key Features:
- A Django-based web app connects to a JavaScript WebSocket frontend for live streaming the user’s webcam feed.
- Image buffers are processed and sent to the ESP32 as grayscale buffers with reduced dimensions, transmitted at 15-second intervals to prevent overloading the connection.
- Advanced image manipulation techniques were used to convert the single-channel grayscale buffer to an RGB888 3-channel buffer, as required by the FOMO Edge Impulse model.
- The FOMO model, trained on five action classes—**fine, danger, stolen, call**, and **others**—achieved an F1 score of 85% and successfully predicted actions from the received buffers.
- Predictions were transmitted back to the server via WebSocket, ensuring a non-blocking and asynchronous workflow on both the frontend and edge device.
- Upon receiving action classes, user data is stored along with their location (latitude and longitude) using an IP-based geolocation service.
- For "danger" and "stolen" classes, the app automatically captures and stores an image.
- Emergency messages, including the user’s Google Maps location, are sent via WhatsApp to saved contacts using the Twilio WhatsApp API.
- Additional features include user authentication and the ability to capture multiple images for Edge Impulse model training.

This setup creates a seamless, user-friendly solution to help elderly people connect with their loved ones in critical moments.
