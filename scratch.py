import time
import network
import machine
import json
from simple import MQTTClient


#uart setup
voc = machine.UART(2, baudrate=9600)
pm = machine.UART(1, baudrate=9600,tx=23,rx=22)

#instruction setup
read_instruct=[0xff,0x01,0x87,0x00,0x00,0x00,0x00,0x00,0x78]
light_on=[0xff,0x01,0x89,0x00,0x00,0x00,0x00,0x00,0x76]
light_off=[0xff,0x01,0x88,0x00,0x00,0x00,0x00,0x00,0x77]
sleep=[0xaf,0x53,0x6c,0x65,0x65,0x70]
wakeup=[0xae,0x45,0x78,0x69,0x74]
read_instruct_voc=bytearray(read_instruct)
light_on_voc=bytearray(light_on)
light_off_voc=bytearray(light_off)
sleep_voc=bytearray(sleep)
wakeup_voc=bytearray(wakeup)

sleep_pm=[0x42,0x4d,0xe4,0x00,0x00,0x01,0x73]
wakeup_pm=[0x42,0x4d,0xe4,0x00,0x01,0x01,0x74]

sleep_pm=bytearray(sleep_pm)
wakeup_pm=bytearray(wakeup_pm)


#ali iot connection setup
client_ID='c1h2m3e4g5o6o7'
product_key='a17CX8cfYJa'
device_secret='07ce56598863bb132b19a361ab3c1dce'
device_name='PJvn7dwBGFsNEYXdvfJy'
region_ID='cn-shanghai'

content='clientId'+client_ID+'deviceName'+device_name+'productKey'+product_key

mqttClientId=client_ID+"|securemode=3,signmethod=hmacsha1|"
mqttUsername=device_name+"&"+product_key
mqttPassword='0670031da68e292b6bf8a692b6944d8a7fa14a9e'

server=product_key+'.iot-as-mqtt.'+region_ID+'.aliyuncs.com'
port=1883

topic_p='/sys/{}/{}/thing/event/property/post'.format(product_key,device_name)
topic_s='/sys/{}/{}/thing/event/property/post_reply'.format(product_key,device_name)

#wlan setup
def net_connecting(ssid,passwd):
    sta=network.WLAN(network.STA_IF)
    ap=network.WLAN(network.AP_IF)

    sta.active(True)
    ap.active(False)

    if not sta.isconnected():
        sta.connect(ssid,passwd)

    if not sta.isconnected():
        for i in range(5):
            time.sleep(6)
            sta.connect(ssid, passwd)

    if not sta.isconnected():
        machine.reset()

#read tvoc data
def instruction_voc(instruct):
    voc.write(instruct)
    data=bytearray(13)
    time.sleep(1)
    voc.readinto(data)
    return data

#read pm2.5 data
def instruction_pm(instruct):
    pm.write(instruct)
    data=bytearray(32)
    time.sleep(1)
    pm.readinto(data)
    return data

#mqtt.subscribe的callback设置
def callback(topic,msg):

    if topic.decode('utf-8')==topic_s:
         msg = json.loads(msg.decode('utf-8'))

         if msg['message'] == 'success':
            instruction_voc(light_off_voc)
            instruction_voc(sleep_voc)
            instruction_pm(sleep_pm)
            machine.deepsleep(180000)

#read tvoc data and send to ali iot
def read_send():

    data_pm=bytearray(32)
    pm.readinto(data_pm)

    instruction_voc(light_on_voc)
    data_voc = instruction_voc(read_instruct_voc)
    if data_voc[0] == 255 and data_voc[1] == 135 and data_pm[0]==66 and data_pm[1]==77:
        data_g = (data_voc[2] * 256 + data_voc[3]) / 1000
        data_t = (data_voc[8] << 8 | data_voc[9]) / 100
        data_h = (data_voc[10] << 8 | data_voc[11]) / 100
        data_pm2_5 = data_pm[6]<<8 | data_pm[7]
        data_pm10 = data_pm[8] << 8 | data_pm[9]
        dataframe = {"params": {"concentration": data_g, "temperature": data_t, "humidity": data_h,
                                "pm2_5":data_pm2_5,"pm10":data_pm10}}

        tvoc_mqtt = MQTTClient(client_id=mqttClientId, server=server, port=port, user=mqttUsername, password=mqttPassword,keepalive=60)
        tvoc_mqtt.set_callback(callback)
        tvoc_mqtt.connect()
        time.sleep(1)
        tvoc_mqtt.publish(topic_p,json.dumps(dataframe))
        time.sleep(1)
        tvoc_mqtt.subscribe(topic_s)
        time.sleep(1)

def main():
    while(True):
        net_connecting('TP-LINK_5BF0', 'biubiu2017')
        instruction_pm(wakeup_pm)
        instruction_voc(wakeup_voc)
        read_send()






