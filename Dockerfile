FROM python:3.12-slim

WORKDIR /app

# Dipendenze
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Codice
COPY . .

# I protocolli vivono qui: montati come volume per la persistenza
RUN mkdir -p /app/protocols

EXPOSE 8501

# Avvio Streamlit in modalita' headless dietro reverse proxy
CMD ["streamlit", "run", "app/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
