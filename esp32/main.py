import network
import time
import ujson
import machine
import dht
from umqtt.simple import MQTTClient  # Library untuk MQTT
import urequests

# Konfigurasi Ubidots
UBIDOTS_TOKEN = "BBUS-OGujRN8Cb1YJna6KwOVmdfwSHP6iQd"
DEVICE_LABEL = "aeromind"  # Pastikan ini sesuai dengan label perangkat Anda di Ubidots
MQTT_BROKER = "industrial.api.ubidots.com"
MQTT_PORT = 1883

# Inisialisasi sensor dan pin
dht_sensor = dht.DHT11(machine.Pin(4))
power = machine.Pin(13, machine.Pin.OUT)  # LED yang dihubungkan ke pin 13

# Status LED
led_state = False

# Koneksi MQTT
client = None  # Definisikan client sebagai global

# Fungsi untuk mengontrol LED
def control_led(state):
    """Mengontrol status LED hijau"""
    global led_state
    if state:
        power.value(1)
        led_state = True
        print("LED hijau dinyalakan")
    else:
        power.value(0)
        led_state = False
        print("LED hijau dimatikan")

# Membaca sensor DHT11
def read_dht11_sensor():
    """Membaca data dari sensor DHT11"""
    try:
        dht_sensor.measure()
        temperature = dht_sensor.temperature()
        humidity = dht_sensor.humidity()
        
        print(f"Suhu: {temperature}°C, Kelembaban: {humidity}%")
        return temperature, humidity
    except Exception as e:
        print("Error membaca sensor DHT11:", e)
        return None, None

# Fungsi callback untuk menerima data power melalui MQTT
def mqtt_callback(topic, message):
    """Callback untuk menerima data power melalui MQTT"""
    try:
        print("Pesan diterima pada topik:", topic)
        print("Pesan:", message)
        
        # Mengkonversi pesan ke JSON
        msg = ujson.loads(message.decode('utf-8'))
        
        # Mengecek status power dalam pesan
        if 'value' in msg:
            power_value = int(msg['value'])
            print(f"Status power dari Ubidots: {power_value}")
            if power_value == 1:
                control_led(True)
            elif power_value == 0:
                control_led(False)
    except Exception as e:
        print("Error memproses pesan MQTT:", e)

# Menghubungkan ke broker MQTT dan subscribe ke topik
def connect_mqtt():
    """Membuat koneksi MQTT dan subscribe ke topik untuk mengambil data power"""
    global client  # Menggunakan client global
    try:
        client = MQTTClient("ubidots-client", MQTT_BROKER, user=UBIDOTS_TOKEN, password=UBIDOTS_TOKEN)
        client.set_callback(mqtt_callback)
        client.connect()
        print("Terhubung ke MQTT broker Ubidots")
        
        # Subscribe ke topik power
        client.subscribe(f"/v1.6/devices/{DEVICE_LABEL}/power")
        print(f'Subscribed ke: /v1.6/devices/{DEVICE_LABEL}/power')
        
        return client
    except Exception as e:
        print("Gagal terhubung ke MQTT:", e)
        return None

# Mengirim data ke Ubidots melalui MQTT
def send_data_mqtt(temperature, humidity):
    """Mengirim data suhu dan kelembaban ke Ubidots melalui MQTT"""
    global client  # Menggunakan client global
    try:
        # Buat payload untuk suhu dan kelembaban
        payload_temp = {"value": temperature}
        payload_hum = {"value": humidity}
        
        # Konversi payload ke JSON
        message_temp = ujson.dumps(payload_temp)
        message_hum = ujson.dumps(payload_hum)
        
        # Mengirim data ke topik suhu dan kelembaban
        client.publish(f"/v1.6/devices/{DEVICE_LABEL}/temperature", message_temp)
        client.publish(f"/v1.6/devices/{DEVICE_LABEL}/humidity", message_hum)
        print(f"Data suhu dan kelembaban berhasil dikirim: {message_temp}, {message_hum}")
        
        response = urequests.post("https://aeromindsic6-production.up.railway.app", json={"temperature": temperature, "humidity": humidity})
        response.close()
        
    except Exception as e:
        print("Gagal mengirim data:", e)

# Fungsi utama untuk menjalankan perangkat
def main():
    """Fungsi utama untuk menjalankan perangkat"""
    
    # Matikan LED awal
    control_led(False)
    
    try:
        # Koneksi MQTT untuk menerima data power
        client = connect_mqtt()
        if client:
            # Proses data power melalui callback MQTT secara real-time
            client.check_msg()  # Mengecek pesan baru yang masuk dari MQTT

            # Baca sensor dan kirim data setelah menerima data power
            temperature, humidity = read_dht11_sensor()
            
            # Kirim data suhu dan kelembaban jika berhasil membaca sensor
            if temperature is not None and humidity is not None:
                send_data_mqtt(temperature, humidity)
        
        # Tunggu beberapa detik sebelum mengulangi proses
        time.sleep(10)
        
    except Exception as e:
        print("Terjadi kesalahan:", e)
    finally:
        # Setelah mengirim data, disconnect dari broker MQTT
        if client:
            client.disconnect()
            print("Disconnected dari MQTT broker")
        print("Memulai ulang dalam 1 menit...")
        time.sleep(60)

# Jalankan program utama
if __name__ == "__main__":
    main()

