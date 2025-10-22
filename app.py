import RPi.GPIO as GPIO
import time
from datetime import datetime
import os


PIR_PIN = 17
LED_VERMELHO = 27
LED_VERDE = 23
BUZZER = 22

TRIG = 5
ECHO = 6


ARQUIVO_REGISTRO = os.path.join(os.getcwd(), "registro.txt")

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(LED_VERMELHO, GPIO.OUT)
GPIO.setup(LED_VERDE, GPIO.OUT)
GPIO.setup(BUZZER, GPIO.OUT)


GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.output(TRIG, False)


GPIO.output(LED_VERDE, True)
GPIO.output(LED_VERMELHO, False)
GPIO.output(BUZZER, False)

print("Sistema de monitoramento iniciado...")
print("Aguardando estabilização do sensor PIR (10 segundos)...")
time.sleep(10)
print("Sistema pronto!")

TEMPO_MAXIMO_ALARME = 30  
TEMPO_MAXIMO_HIGH = 10  
tempo_high_inicio = None

def registrar_em_arquivo(duracao=None):
    """Registra data, hora e duração da detecção no arquivo de texto"""
    agora = datetime.now()
    data_str = agora.strftime("%Y-%m-%d")
    hora_str = agora.strftime("%H:%M:%S")
    if duracao is not None:
        linha = f"{data_str} {hora_str} Duração: {duracao:.2f}s\n"
    else:
        linha = f"{data_str} {hora_str}\n"
    try:
        with open(ARQUIVO_REGISTRO, "a") as arquivo:
            arquivo.write(linha)
        print(f"[OK] Detecção registrada: {linha.strip()}")
    except Exception as e:
        print(f"[ERRO] Falha ao registrar no arquivo: {e}")


TEMPO_REARME = 2
DESABILITADO_TIMEOUT = 5
MIN_DETECCOES = 6
TEMPO_ENTRE_LEITURAS = 0.1

movimento_anterior = False
detecao_inicio = 0
ultimo_fim_movimento = 0
tempo_low_inicio = None
sensor_desabilitado = False
deteccoes_consecutivas = 0
ultima_leitura = 0
buzzer_ligado = False
ultima_deteccao = 0
alarme_ligado = False
tempo_alarme_inicio = 0

def verificar_sensor_continuo():
    """Verifica se o sensor está travado em HIGH"""
    leituras = []
    for _ in range(10):
        leituras.append(GPIO.input(PIR_PIN))
        time.sleep(0.1)
    return all(leituras)

def medir_distancia_cm():
    """Mede a distância usando o sensor ultrassônico HC-SR04"""

    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)


    timeout = time.time() + 0.04 
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        if pulse_start > timeout:
            return -1  


    timeout = time.time() + 0.04
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        if pulse_end > timeout:
            return -1  

    pulse_duration = pulse_end - pulse_start
    distancia = pulse_duration * 17150  
    distancia = round(distancia, 2)
    return distancia if 2 < distancia < 400 else -1  
