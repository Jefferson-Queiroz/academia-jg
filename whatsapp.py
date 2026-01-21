import requests
import urllib.parse

API_KEY = 'SUA_API_KEY_AQUI'

def enviar_whatsapp(telefone, mensagem):
    texto = urllib.parse.quote(mensagem)
    url = f"https://api.callmebot.com/whatsapp.php?phone={telefone}&text={texto}&apikey={API_KEY}"
    requests.get(url)
    
try:
    import requests
except ImportError:
    requests = None

def enviar_whatsapp(telefone, mensagem):
    if not requests:
        print("⚠️ requests não instalado")
        return False

    # sua lógica aqui
    return True

