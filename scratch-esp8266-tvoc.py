import time
import network
import machine
import uos
import json
from simple import MQTTClient


#uart0 setup
u0 = machine.UART(0, baudrate=9600)

#instruction setup
read_instruct=[0xff,0x01,0x87,0x00,0x00,0x00,0x00,0x00,0x78]
light_on=[0xff,0x01,0x89,0x00,0x00,0x00,0x00,0x00,0x76]
light_off=[0xff,0x01,0x88,0x00,0x00,0x00,0x00,0x00,0x77]
sleep=[0xaf,0x53,0x6c,0x65,0x65,0x70]
wakeup=[0xae,0x45,0x78,0x69,0x74]
read_instruct=bytearray(read_instruct)
light_on=bytearray(light_on)
light_off=bytearray(light_off)
sleep=bytearray(sleep)
wakeup=bytearray(wakeup)

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
            time.sleep(5)
            sta.connect(ssid, passwd)

#read tvoc data
def instruction(instruct):
    u0.write(instruct)
    data=bytearray(13)
    time.sleep(1)
    u0.readinto(data)
    return data

#mqtt.subscribe的callback设置
def callback(topic,msg):

    if topic.decode('utf-8')==topic_s:
         msg = json.loads(msg.decode('utf-8'))

         if msg['message'] == 'success':
            instruction(light_off)
            rtc = machine.RTC()
            rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
            rtc.alarm(rtc.ALARM0, 300000)
            machine.deepsleep()

#read tvoc data and send to ali iot
def read_send():
    instruction(light_on)
    data_frame = instruction(read_instruct)
    if data_frame[0] == 255 and data_frame[1] == 135:
        data_g = (data_frame[2] * 256 + data_frame[3]) / 1000
        data_t = (data_frame[8] << 8 | data_frame[9]) / 100
        data_h = (data_frame[10] << 8 | data_frame[11]) / 100
        dataframe = {"params": {"data_g": data_g, "data_t": data_t, "data_h": data_h}}

        tvoc_mqtt = MQTTClient(client_id=mqttClientId, server=server, port=port, user=mqttUsername, password=mqttPassword,keepalive=60)
        tvoc_mqtt.set_callback(callback)
        tvoc_mqtt.connect()
        time.sleep(1)
        tvoc_mqtt.publish(topic_p,json.dumps(dataframe))
        time.sleep(1)
        tvoc_mqtt.subscribe(topic_s)
        time.sleep(1)



def main():
    uos.dupterm(None, 1)

    net_connecting('TP-LINK_5BF0','biubiu2017')

    read_send()






