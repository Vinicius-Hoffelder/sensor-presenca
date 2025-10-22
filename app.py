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
    
def buzzer_beep(duration=2, beep_time=0.1, pause_time=0.1):
    """Faz o buzzer emitir beeps durante 'duration' segundos"""
    end_time = time.time() + duration
    while time.time() < end_time:
        GPIO.output(BUZZER, True)
        time.sleep(beep_time)
        GPIO.output(BUZZER, False)
        time.sleep(pause_time)

try:
    while True:
        tempo_agora = time.time()
        
        if (tempo_agora - ultima_leitura) < TEMPO_ENTRE_LEITURAS:
            time.sleep(0.01)
            continue
            
        movimento_atual = GPIO.input(PIR_PIN)
        ultima_leitura = tempo_agora

 
        print(f"PIR: {movimento_atual}, Buzzer: {buzzer_ligado}, Detecções: {deteccoes_consecutivas}")


        if movimento_atual:
            if tempo_high_inicio is None:
                tempo_high_inicio = tempo_agora
            elif (tempo_agora - tempo_high_inicio) > TEMPO_MAXIMO_HIGH:
                print("AVISO: Sensor PIR em HIGH contínuo! Resetando estado para evitar falso positivo.")
                deteccoes_consecutivas = 0
                tempo_high_inicio = tempo_agora
                if buzzer_ligado:
                    GPIO.output(LED_VERMELHO, False)
                    GPIO.output(BUZZER, False)
                    GPIO.output(LED_VERDE, True)
                    buzzer_ligado = False
                time.sleep(1)
                continue
        else:
            tempo_high_inicio = None


        if movimento_atual:
            deteccoes_consecutivas += 1
        else:
            deteccoes_consecutivas = 0


        movimento_real = (deteccoes_consecutivas >= MIN_DETECCOES)

        if not movimento_atual:
            if tempo_low_inicio is None:
                tempo_low_inicio = tempo_agora
            elif (tempo_agora - tempo_low_inicio) > DESABILITADO_TIMEOUT:
                if not sensor_desabilitado:
                    print("Sensor PIR parece estar desabilitado (conectado ao GND). Sistema em espera...")
                    sensor_desabilitado = True
      
                GPIO.output(LED_VERMELHO, False)
                GPIO.output(BUZZER, False)
                GPIO.output(LED_VERDE, False)
                buzzer_ligado = False
            else:

                GPIO.output(LED_VERMELHO, False)
                GPIO.output(BUZZER, False)
                GPIO.output(LED_VERDE, True)
                buzzer_ligado = False
        else:
            tempo_low_inicio = None
            if sensor_desabilitado:
                print("Sensor PIR reabilitado. Sistema retomado!")
                sensor_desabilitado = False

  
        if not sensor_desabilitado:

            if (tempo_agora - ultimo_fim_movimento) < TEMPO_REARME:
                if buzzer_ligado:
                    GPIO.output(LED_VERMELHO, False)
                    GPIO.output(BUZZER, False)
                    GPIO.output(LED_VERDE, True)
                    buzzer_ligado = False
                    print("Tempo de rearme - alarme desligado")
                movimento_anterior = False
                continue


            if movimento_real:
                if not movimento_anterior:
                    detecao_inicio = tempo_agora
                    distancia_cm = medir_distancia_cm()
                    print(f"Movimento REAL detectado a {distancia_cm} cm!")
                    registrar_em_arquivo() 

                if not buzzer_ligado:
                    GPIO.output(LED_VERMELHO, True)
                    GPIO.output(BUZZER, True)
                    GPIO.output(LED_VERDE, False)
                    buzzer_ligado = True
                    print("ALARME LIGADO")
            else:
                if movimento_anterior:
                    duracao = tempo_agora - detecao_inicio
                    print(f"Movimento finalizado! Duração: {duracao:.2f}s")
                    ultimo_fim_movimento = tempo_agora
                    registrar_em_arquivo(duracao) 
                if buzzer_ligado:
                    GPIO.output(LED_VERMELHO, False)
                    GPIO.output(BUZZER, False)
                    GPIO.output(LED_VERDE, True)
                    buzzer_ligado = False
                    print("ALARME DESLIGADO")

            movimento_anterior = movimento_real


        if movimento_real and not alarme_ligado:
            print("Movimento REAL detectado!")
            registrar_em_arquivo() 
            GPIO.output(LED_VERDE, False)
            GPIO.output(LED_VERMELHO, True)

            buzzer_beep(duration=2, beep_time=0.1, pause_time=0.1)
            GPIO.output(LED_VERMELHO, False)
            GPIO.output(LED_VERDE, True)
            alarme_ligado = True
            tempo_alarme_inicio = tempo_agora

        if alarme_ligado and (tempo_agora - tempo_alarme_inicio) > TEMPO_MAXIMO_ALARME:
            print("PROTEÇÃO: Alarme desligado automaticamente (tempo máximo excedido)")
            GPIO.output(LED_VERMELHO, False)
            GPIO.output(BUZZER, False)
            GPIO.output(LED_VERDE, True)
            alarme_ligado = False
            
            if verificar_sensor_continuo():
                print("AVISO: Sensor PIR pode estar travado em HIGH!")
                time.sleep(5) 
                continue

        if movimento_atual:
            if not alarme_ligado and (tempo_agora - ultima_deteccao) > TEMPO_ENTRE_LEITURAS:
                print("Movimento detectado...")
                GPIO.output(LED_VERMELHO, True)
                GPIO.output(BUZZER, True)
                GPIO.output(LED_VERDE, False)
                alarme_ligado = True
                tempo_alarme_inicio = tempo_agora
                ultima_deteccao = tempo_agora
                registrar_em_arquivo()
        else:
            if alarme_ligado:
                print("Movimento cessou. Desativando alarme...")
                GPIO.output(LED_VERMELHO, False)
                GPIO.output(BUZZER, False)
                GPIO.output(LED_VERDE, True)
                alarme_ligado = False

        time.sleep(0.1)

except KeyboardInterrupt:
    print("Encerrando o sistema...")

finally:
    GPIO.output(LED_VERDE, False)
    GPIO.output(LED_VERMELHO, False)
    GPIO.output(BUZZER, False)
    GPIO.cleanup()
    print("Sistema encerrado com sucesso.")
