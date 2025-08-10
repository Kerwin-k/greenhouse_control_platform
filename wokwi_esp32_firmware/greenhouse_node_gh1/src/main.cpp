#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>

// --- 1. 配置区域 ---
#define PUBLISH_INTERVAL_MS 2000
#define WIFI_SSID "Wokwi-GUEST"
#define WIFI_PASSWORD ""
#define MQTT_BROKER "broker-cn.emqx.io"
#define MQTT_PORT 1883

// ！！注意，此处为每个开发板的唯一ID，新建开发板请将数字++
#define GREENHOUSE_ID "gh1"

// --- 2. 引脚定义 ---
#define DHT_PIN 15
#define SERVO_PIN 12
#define LED_PIN 13
#define DOOR_SWITCH_PIN 14
#define SPRINKLER_PIN 23

// --- 3. 初始化硬件和客户端 ---
DHT dht(DHT_PIN, DHT22);
Servo fanServo;
WiFiClient espClient;
PubSubClient client(espClient);

// --- 4. 全局状态变量 ---
long lastMsg = 0;
String lightState = "OFF";
String fanState = "OFF";
String sprinklerState = "OFF";

int servoPos = 0;
int servoDir = 1;
long lastServoMove = 0;
const int servoSpeed = 25;

// --- 5. 函数声明 ---
void callback(char* topic, byte* payload, unsigned int length);
void setup_wifi();
void reconnect();

// --- 6. 函数完整定义 ---

void setup_wifi() {
  Serial.print("Connecting to ");
  Serial.println(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");

    // --- 核心修正 1：创建唯一的客户端ID ---
    // 在ID后附加一个随机数，防止与服务器上残留的旧连接冲突
    String clientId = "gh-client-" + String(GREENHOUSE_ID) + "-" + String(random(0, 1000));

    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
      char controlTopic[128];
      snprintf(controlTopic, sizeof(controlTopic), "ucsi/mdt1001/greenhouse/%s/control/#", GREENHOUSE_ID);
      client.subscribe(controlTopic);
      Serial.print("Subscribed to: ");
      Serial.println(controlTopic);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  randomSeed(micros()); // 初始化随机数种子
  pinMode(LED_PIN, OUTPUT);
  pinMode(DOOR_SWITCH_PIN, INPUT_PULLUP);
  pinMode(SPRINKLER_PIN, OUTPUT);
  fanServo.attach(SERVO_PIN);
  dht.begin();

  setup_wifi();
  client.setServer(MQTT_BROKER, MQTT_PORT);
  client.setCallback(callback);

  client.setBufferSize(512);
}

void callback(char* topic, byte* payload, unsigned int length) {
  String payloadStr;
  payloadStr.reserve(length);
  for (int i = 0; i < length; i++) {
    payloadStr += (char)payload[i];
  }

  StaticJsonDocument<128> doc;
  deserializeJson(doc, payloadStr);
  const char* command = doc["command"];

  if (strstr(topic, "/control/light")) {
    lightState = strcmp(command, "ON") == 0 ? "ON" : "OFF";
    digitalWrite(LED_PIN, lightState == "ON" ? HIGH : LOW);
  }

  if (strstr(topic, "/control/fan")) {
    fanState = strcmp(command, "ON") == 0 ? "ON" : "OFF";
  }

  if (strstr(topic, "/control/sprinkler")) {
    sprinklerState = strcmp(command, "ON") == 0 ? "ON" : "OFF";
    digitalWrite(SPRINKLER_PIN, sprinklerState == "ON" ? HIGH : LOW);
  }
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  long now = millis();

  if (fanState == "ON") {
    if (now - lastServoMove > servoSpeed) {
      lastServoMove = now;
      servoPos += servoDir;
      fanServo.write(servoPos);
      if (servoPos >= 180 || servoPos <= 0) {
        servoDir *= -1;
      }
    }
  } else {
    if (servoPos != 0) {
      servoPos = 0;
      fanServo.write(servoPos);
    }
  }

  if (now - lastMsg > PUBLISH_INTERVAL_MS) {
    lastMsg = now;

    float h = dht.readHumidity();
    float t = dht.readTemperature();
    String doorStatus = digitalRead(DOOR_SWITCH_PIN) == HIGH ? "OPEN" : "CLOSED";

    if (isnan(h) || isnan(t)) {
      Serial.println("Failed to read from DHT sensor!");
      return;
    }

    StaticJsonDocument<512> telemetry_doc;
    telemetry_doc["temperature"] = t;
    telemetry_doc["humidity"] = h;
    String telemetry_output;
    serializeJson(telemetry_doc, telemetry_output);

    StaticJsonDocument<512> status_doc;
    status_doc["door"] = doorStatus;
    status_doc["light_state"] = lightState;
    status_doc["fan_state"] = fanState;
    status_doc["sprinkler_state"] = sprinklerState;
    status_doc["interval"] = PUBLISH_INTERVAL_MS;
    String status_output;
    serializeJson(status_doc, status_output);

    // --- 核心修正 2：使用更安全的方式构建Topic字符串 ---
    char topic_buffer[128];

    snprintf(topic_buffer, sizeof(topic_buffer), "ucsi/mdt1001/greenhouse/%s/telemetry/environment", GREENHOUSE_ID);
    client.publish(topic_buffer, telemetry_output.c_str());

    snprintf(topic_buffer, sizeof(topic_buffer), "ucsi/mdt1001/greenhouse/%s/telemetry/status", GREENHOUSE_ID);
    client.publish(topic_buffer, status_output.c_str());

    Serial.println("Published data to MQTT Broker.");
  }
}