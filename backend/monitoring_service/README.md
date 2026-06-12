### **Краткая инструкция по работе с системой мониторинга SigNoz** 

**Данная инструкция включает в себя основные блоки и ответы на вопросы по работе с мониторингом:**

1. Как установить систему мониторинга SigNoz?  
2. Как настроить логирование внутри сервиса и правильно отправить данные в систему мониторинга?  
3. Как настроить прием передаваемых данных в систему мониторинга?  
   

   **1\. Как установить и удалить SigNoz?**

---

1. Установка в папке проекта (project)
```text
bash  
git clone \-b main https://github.com/SigNoz/signoz.git && cd signoz/deploy/  
./install.sh  
```
установка просит почту\! Почту потом изменить будет нельзя \- только через удаление(см. ниже) и полную переустановку.

2. Регистрация в интерфейсе

Перейти в интерфейс и зарегистрироваться [http://localhost:8080](http://localhost:8080) 

3. Проверка сети

Убедитесь, что сеть signoz-net создана и работает
```text  
bash  
sudo docker network ls | grep signoz-net  
```
Если сети нет – создайте:  
```text
bash  
sudo docker network create signoz-net
```

4. Подключение сервисов через сборку образа в папке проекта **(**project)
```text
bash  
sudo docker compose up \--build \-d
```
настроенные ранее сервисы А,Б,С должны отображать графики

Дополнительно. Полная инструкция по удалению (для чистой переустановки) 
```text 
bash  
*\# 2.1 Перейти в рабочую папку (замените на свою, если отличается)*  
cd /home/user/project

*\# 2.2 Остановить и удалить контейнеры, созданные пользовательским docker-compose.yml*  
sudo docker compose down \-v 2\>/dev/null

*\# 2.3 Остановить и удалить контейнеры SigNoz (если запущены через install.sh или отдельно)*  
cd signoz/deploy 2\>/dev/null && sudo docker compose down \-v 2\>/dev/null ; cd ../..

*\# 2.4 Принудительно удалить все контейнеры, связанные с проектом (по именам)*  
sudo docker rm \-f $(sudo docker ps \-aq \--filter "name=signoz") 2\>/dev/null  
sudo docker rm \-f $(sudo docker ps \-aq \--filter "name=service\_") 2\>/dev/null  
sudo docker rm \-f $(sudo docker ps \-aq \--filter "name=clickhouse") 2\>/dev/null  
sudo docker rm \-f $(sudo docker ps \-aq \--filter "name=otel-collector") 2\>/dev/null  
sudo docker rm \-f $(sudo docker ps \-aq \--filter "name=query-service") 2\>/dev/null  
sudo docker rm \-f $(sudo docker ps \-aq \--filter "name=frontend") 2\>/dev/null

*\# 2.5 Удалить все тома, созданные проектом (по меткам или вручную)*  
sudo docker volume rm $(sudo docker volume ls \-q \--filter "name=clickhouse") 2\>/dev/null  
sudo docker volume rm $(sudo docker volume ls \-q \--filter "name=signoz") 2\>/dev/null  
*\# Также удалить том с данными ClickHouse, смонтированный из папки*  
sudo rm \-rf ./clickhouse-data

*\# 2.6 Удалить сети (если они остались)*  
sudo docker network rm signoz\_default 2\>/dev/null  
sudo docker network rm monitoring\_net 2\>/dev/null

*\# 2.7 Удалить образы, использованные проектом (освобождает место, опционально)*  
sudo docker rmi $(sudo docker images \-q \--filter "reference=signoz/\*") 2\>/dev/null  
sudo docker rmi $(sudo docker images \-q \--filter "reference=clickhouse/\*") 2\>/dev/null  
sudo docker rmi $(sudo docker images \-q \--filter "reference=service\_\*") 2\>/dev/null

*\# 2.8 Очистить систему Docker от неиспользуемых ресурсов (сети, кэш)*  
sudo docker system prune \-a \--volumes \-f

*\# 2.9 Удалить файлы конфигурации и исходный код SigNoz (если нужно заново клонировать)*  
sudo rm \-rf ./signoz  
sudo rm \-f ./otel-collector-config.yaml

*\# 2.10 (Опционально) Удалить файлы логов и временные данные, созданные сервисами*  
sudo rm \-rf ./logs 2\>/dev/null
```
Проверка полного удаления 
```text 
bash  
sudo docker ps \-a | grep \-E "signoz|service\_|clickhouse|otel-collector|query-service|frontend"  
sudo docker volume ls | grep \-E "clickhouse|signoz"  
sudo docker network ls | grep \-E "signoz|monitoring"  
sudo ls \-la /home/user/monitoring\_demo/  
```
*\# Должны отсутствовать папки signoz, clickhouse-data, файл otel-collector-config.yaml (если не нужны)*

**2\. Как настроить логирование внутри сервиса и правильно отправить данные в систему мониторинга?**

---

*Условие:* предполагается, что внутри сервиса логи уже собираются через стандартную библиотеку logging (log.info/debug/error и т.д.).

*Примеры правильной работы и оформления* логов, метрик и трейсов(в т.ч. ручных) смотрите в папке docs/памятка.md текущего проекта. Они вынесены в отдельный файл в т.ч. для упрощения текущей инструкции до работоспособного минимума.

*Готовые примеры по оформлению и настройке можно посмотреть в сервисах А,Б,С текущего проекта(services/…) или сервиса paser\_service*.

**Настройка и отправка данных(логи, метрики, трейсы) в систему мониторинга, шаги:**

1. Добавить в requirements.txt фиксированные версии библиотек для мониторинга:   
   
```text
   opentelemetry-api==1.27.0  
   opentelemetry-sdk==1.27.0  
   opentelemetry-distro==0.48b0  
   opentelemetry-exporter-otlp==1.27.0  
   opentelemetry-instrumentation-fastapi==0.48b0  
   opentelemetry-instrumentation-httpx==0.48b0  
   opentelemetry-propagator-b3==1.27.0  
   python-json-logger==2.0.4  
   setuptools\<70  
```
     
2. Скопировать общую библиотеку telemetry\_lib (из текущего проекта/services/) в ваш проект т.к. понадобятся импорты функций из нее.  
     
3. Для подключения ЛОГОВ (JSON \+ OTLP) необходимо проделать следующие шаги  
     
   в файле  main.py (полный пошаговый пример приведен ниже):  
   3.1 настроить импорт функций из telemetry\_lib   
   3.2 перед определением app вставить вызов setup\_observability    
   3.3.получить логгер через logging.getLogger(service\_name).После вызова setup\_observability.  
     
   в файле  всех остальных модулей где будет логирование:  
   добавить строки в начало каждого файла:   
   python  
   import logging  
   logger \= logging.getLogger(\_\_name\_\_)

   

     
     
4. Для подключения ТРЕЙСОВ (полный пошаговый пример приведен ниже):  
     
   4.1 после строк кода шага 3.2 добавить строку instrument\_fastapi(app, tracer\_provider), которая будет автоматически собирать все входящие HTTP-запросы и исходящие вызовы через httpx.  
   4.2  можно не выполнять: дополнительно если нужно (а нужно редко когда) можно настроить ручное добавление спанов \-  пример оформления смотрите в памятке.  
     
5. Для подключения МЕТРИК (если они НУЖНЫ, если нет, то шаг пропускаем) (полный пошаговый пример приведен ниже):  
   5.1 можно не выполнять: дополнительно если нужно  можно настроить сбор метрик \-  пример оформления смотрите в памятке.

   
```text
python  
ПРИМЕР (обратите внимание на последовательность шагов):   
\# \==================== ШАГ 3.1: импорты \====================  
import os  
import logging  
from fastapi import FastAPI, HTTPException  
from telemetry\_lib.telemetry import setup\_observability, instrument\_fastapi  
from opentelemetry import trace   \# для ручных спанов  
import uvicorn

\# \==================== ШАГ 3.2: настройка observability \====================  
app \= FastAPI()  
service\_name \= "payment-service"  
otlp\_endpoint \= os.getenv("OTEL\_EXPORTER\_OTLP\_ENDPOINT", "signoz-otel-collector:4317")

tracer\_provider, meter\_provider, \_ \= setup\_observability(service\_name, otlp\_endpoint)

\#\# \==================== ШАГ 4.1: инструментирование FastAPI для трейсов \====================  
instrument\_fastapi(app, tracer\_provider)

\# \==================== ШАГ 3.3: получение логгера \====================  
log \= logging.getLogger(service\_name)   \# используйте этот логгер везде

\# \==================== ШАГ 5.1: метрики (опционально и НЕ ОБЯЗАТЕЛЬНО т.е. можно удалить и не выполнять) \====================  
meter \= meter\_provider.get\_meter(service\_name)  
payment\_counter \= meter.create\_counter(  
    "payment\_requests\_total",  
    description="Total payment requests"  
)

\# \==================== ШАГ 4.2: ручной трейсер (опционально и НЕ ОБЯЗАТЕЛЬНО т.е. можно удалить и не выполнять) \====================  
tracer \= trace.get\_tracer(service\_name)

\# \==================== ЭНДПОИНТЫ \====================  
@app.get("/health")  
async def health():  
    log.debug("Health check")  
    return {"status": "ok"}

@app.post("/pay")  
async def pay(amount: float):  
    with tracer.start\_as\_current\_span("process\_payment") as span:  
        span.set\_attribute("payment.amount", amount)  
        log.info(f"Processing payment {amount}")  
        payment\_counter.add(1, {"currency": "USD"})  
        \# ... логика оплаты  
        return {"status": "paid"}

if \_\_name\_\_ \== "\_\_main\_\_":  
    uvicorn.run(app, host="0.0.0.0", port=8000)
```


Что при этом происходит автоматически?
* Логи выводятся в stdout в JSON-формате (поле severity вместо levelname).  
* Одновременно логи отправляются по OTLP в SigNoz.  
* К каждому логу автоматически добавляются trace\_id и span\_id активного спана.

  **3\. Как настроить прием передаваемых данных в систему мониторинга?**

---

Экспорт уже настроен внутри setup\_observability через OTLP gRPC экспортёры.

Далее нужно только передать правильные переменные окружения в контейнер и подключить:

1. в docker-compose.yml по шаблону из проекта (см. файл docker-compose.yml)  необходимо добавить сервис. Часть примера с обязательными полями для нового сервиса:

```text
yaml  
services:  
  my\_new\_service:  
    build: .  
    environment:  
      OTEL\_EXPORTER\_OTLP\_ENDPOINT: "signoz-otel-collector:4317"   *\# обязательно*  
      OTEL\_EXPORTER\_OTLP\_INSECURE: "true"                         *\# обязательно для http без TLS*  
    networks:  
      \- signoz\-net                                                *\# сеть должна существовать*
```
или для Dockerfile (если не используете docker-compose) добавить строки:  
```text
dockerfile  
ENV OTEL\_EXPORTER\_OTLP\_ENDPOINT=signoz-otel-collector:4317  
ENV OTEL\_EXPORTER\_OTLP\_INSECURE=true
```
2. Подключение сервисов через сборку образа в папке проекта **(**project)
```text
bash  
sudo docker compose up \--build \-d
```


Поздравляю\! Установка и настройки завершены\!