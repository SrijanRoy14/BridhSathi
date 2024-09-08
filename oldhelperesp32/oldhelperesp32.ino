
#include <Arduino.h>

#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>

#include <WebSocketsClient.h>

#include <Hash.h>

#include <OldHelper_SignDetection_inferencing.h>
#include "edge-impulse-sdk/dsp/image/image.hpp"

ESP8266WiFiMulti WiFiMulti;
WebSocketsClient webSocket;

#define USE_SERIAL Serial
#define EI_CAMERA_RAW_FRAME_BUFFER_COLS 320
#define EI_CAMERA_RAW_FRAME_BUFFER_ROWS 240
#define EI_CAMERA_FRAME_BYTE_SIZE 3

const int img_width = 96;
const int img_height = 96;
int predicted_class = -1;

void webSocketEvent(WStype_t type, uint8_t *payload, size_t length)
{

  switch (type)
  {
  case WStype_DISCONNECTED:
    USE_SERIAL.printf("[WSc] Disconnected!\n");
    break;
  case WStype_CONNECTED:
  {
    USE_SERIAL.printf("[WSc] Connected to url: %s\n", payload);

    // send message to server when Connected
    webSocket.sendTXT("Connected");
  }
  break;
  case WStype_TEXT:
    USE_SERIAL.printf("[WSc] get text: %s\n", payload);

    // send message to server
    webSocket.sendTXT(payload);
    break;
  case WStype_BIN:
    uint8_t *image_buffer;
    USE_SERIAL.printf("[WSc] get binary length: %u\n", length);
    // hexdump(payload, length);
    image_buffer = (uint8_t *)malloc(96 * 96);
    if (length == 96 * 96)
    {

      memcpy(image_buffer, payload, length);
      USE_SERIAL.println("Image received");

      predicted_class = run_inference(image_buffer, length);

      if (predicted_class > 1)
        webSocket.sendTXT(predicted_class);

      // webSocket.sendBIN(num, image_buffer, length);
    }
    else
    {
      USE_SERIAL.println("Received data size mismatch");
    }
    free(image_buffer);
    break;
  case WStype_PING:
    // pong will be send automatically
    USE_SERIAL.printf("[WSc] get ping\n");
    break;
  case WStype_PONG:
    // answer to a ping we send
    USE_SERIAL.printf("[WSc] get pong\n");
    break;
  }
}

void setup()
{
  // USE_SERIAL.begin(921600);
  USE_SERIAL.begin(115200);

  // Serial.setDebugOutput(true);
  USE_SERIAL.setDebugOutput(true);

  USE_SERIAL.println();
  USE_SERIAL.println();
  USE_SERIAL.println();

  for (uint8_t t = 4; t > 0; t--)
  {
    USE_SERIAL.printf("[SETUP] BOOT WAIT %d...\n", t);
    USE_SERIAL.flush();
    delay(1000);
  }

  WiFiMulti.addAP("dlink-108C", "87654321");

  // WiFi.disconnect();
  while (WiFiMulti.run() != WL_CONNECTED)
  {
    delay(100);
  }

  // server address, port and URL
  webSocket.begin("192.168.0.100", 8000, "/ws/testing/");

  // event handler
  webSocket.onEvent(webSocketEvent);

  webSocket.setReconnectInterval(5000);
}

int run_inference(uint8_t *image_buffer, size_t length)
{
  ei_printf("\nInference settings:\n");
  ei_printf("\tImage resolution: %dx%d\n", EI_CLASSIFIER_INPUT_WIDTH, EI_CLASSIFIER_INPUT_HEIGHT);
  ei_printf("\tFrame size: %d\n", EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE);
  ei_printf("\tNo. of classes: %d\n", sizeof(ei_classifier_inferencing_categories) / sizeof(ei_classifier_inferencing_categories[0]));
  uint8_t *ei_camera_capture_out;
  if (image_buffer)
  {

    ei_camera_capture_out = (uint8_t *)malloc(img_height * img_width * EI_CAMERA_FRAME_BYTE_SIZE);
    if (!fmt2rgb888(image_buffer, length, ei_camera_capture_out))
    {
      Serial.println("Camera => Cannot convert the Grayscale buffer to RGB888!");
      return -1;
    }

    //  resize the converted RGB888 buffer by utilizing built-in Edge Impulse functions, since the captured image is 96x96
    ei::image::processing::crop_and_interpolate_rgb888(
        Sei_camera_capture_out, // Output image buffer, can be same as input buffer
        img_height,
        img_width,
        ei_camera_capture_out,
        EI_CLASSIFIER_INPUT_WIDTH,
        EI_CLASSIFIER_INPUT_HEIGHT);

    // Running inference:
    ei::signal_t signal;
    // Create a signal object from the converted and resized image buffer.
    signal.total_length = EI_CLASSIFIER_INPUT_WIDTH * EI_CLASSIFIER_INPUT_HEIGHT;
    signal.get_data = &ei_camera_cutout_get_data;
    // Running the classifier:
    ei_impulse_result_t result = {0};
    EI_IMPULSE_ERROR _err = run_classifier(&signal, &result, false);
    if (_err != EI_IMPULSE_OK)
    {
      ei_printf("ERR: Failed to run classifier (%d)\n", _err);
      return -1;
    }

    / Print the inference timings on the serial monitor.ei_printf("\nPredictions (DSP: %d ms., Classification: %d ms., Anomaly: %d ms.): \n",
                                                                  result.timing.dsp, result.timing.classification, result.timing.anomaly);

    // Obtain the object detection results and bounding boxes for the detected labels (classes).
    bool bb_found = result.bounding_boxes[0].value > 0;
    for (size_t ix = 0; ix < EI_CLASSIFIER_OBJECT_DETECTION_COUNT; ix++)
    {
      auto bb = result.bounding_boxes[ix];
      if (bb.value == 0)
        continue;
      // Print the calculated bounding box measurements on the serial monitor.
      ei_printf("    %s (", bb.label);
      ei_printf_float(bb.value);
      ei_printf(") [ x: %u, y: %u, width: %u, height: %u ]\n", bb.x, bb.y, bb.width, bb.height);
      // Get the predicted label (class).
      if (bb.label == "fine")
        return 0;
      if (bb.label == "danger")
        return 1;

      if (bb.label == "stolen")
        return 2;
      if (bb.label == "call")
        return 3;
      Serial.print("\nPredicted Class: ");
      Serial.println(bb.label);
    }
    if (!bb_found)
      ei_printf("    No objects found!\n");

// Detect anomalies, if any:
#if EI_CLASSIFIER_HAS_ANOMALY == 1
    ei_printf("Anomaly: ");
    ei_printf_float(result.anomaly);
    ei_printf("\n");
#endif
    free(ei_camera_capture_out);
    // Release the image buffers.
  }
  // USE_SERIAL.print(ei_camera_capture_out[27,640]);

  return -1;
}

static int ei_camera_cutout_get_data(size_t offset, size_t length, float *out_ptr)
{
  // Convert the given image data (buffer) to the out_ptr format required by the Edge Impulse FOMO model.
  size_t pixel_ix = offset * 3;
  size_t pixels_left = length;
  size_t out_ptr_ix = 0;
  // Since the image data is converted to an RGB888 buffer, directly recalculate offset into pixel index.
  while (pixels_left != 0)
  {
    out_ptr[out_ptr_ix] = (ei_camera_capture_out[pixel_ix] << 16) + (ei_camera_capture_out[pixel_ix + 1] << 8) + ei_camera_capture_out[pixel_ix + 2];
    // Move to the next pixel.
    out_ptr_ix++;
    pixel_ix += 3;
    pixels_left--;
  }
  return 0;
}

bool fmt2rgb888(const uint8_t *src_buf, size_t src_len, uint8_t *rgb_buf)
{
  int i;
  uint8_t b;
  size_t pix_count = src_len;
  for (i = 0; i < pix_count; i++)
  {
    b = *src_buf++;
    *rgb_buf++ = b;
    *rgb_buf++ = b;
    *rgb_buf++ = b;
  }
  return true;
}
void loop()
{
  webSocket.loop();
}
