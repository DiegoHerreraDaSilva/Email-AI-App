import os
import re
from flask import Flask, render_template, request
import PyPDF2

# tenta importar openai se estiver instalado e chave disponível
try:
    import openai
    OPENAI_KEY = os.getenv("OPENAI_API_KEY")
    if OPENAI_KEY:
        openai.api_key = OPENAI_KEY
        OPENAI_AVAILABLE = True
    else:
        OPENAI_AVAILABLE = False
except Exception:
    openai = None
    OPENAI_AVAILABLE = False

app = Flask(__name__)

def extract_text_from_pdf(file_stream):
    try:
        reader = PyPDF2.PdfReader(file_stream)
        texto = ""
        for page in reader.pages:
            page_text = page.extract_text() or ""
            texto += page_text + "\n"
        return texto
    except Exception:
        return ""

def preprocess(text):
    if not text:
        return ""
    text = text.strip()
    # remove múltiplos espaços/quebras
    text = re.sub(r'\s+', ' ', text)
    return text

def rule_based_classify(text):
    keywords = [
  "suporte", "erro", "problema", "ajuda", "reclama", "falha",
  "solicitar", "solicitação", "dúvida", "duvida", "urgente",
  "pagamento", "fatura", "corrigir", "alteração", "configuração",
  "instalação", "reparo", "conserto", "não consigo", "nao consigo",
  "sistema", "software", "tela", "ruim", "internet",
  "atendimento", "assistance", "bug", "travamento", "pendente",
  "suporte técnico", "erro crítico", "problema urgente", "solicitar ajuda",
  "falha no sistema", "dificuldade", "incidente", "manutenção",
  "atualização", "limite", "recibo", "pagamento pendente", "instável",
  "configurar", "instalar", "ajustar", "corrigido", "falhou",
  "conexão", "offline", "lentidão", "mensagem", "alerta", "notificação",
  "senha", "login", "acesso", "desconectado", "interrompido",
  "erro de pagamento", "fatura atrasada", "documento", "protocolo",
  "atraso", "falha técnica", "problema no aplicativo", "aplicativo travado",
  "suporte online", "helpdesk", "ticket", "reclamação", "solicitação urgente",
  "correção", "atualizar", "configurações", "instalação falhou", "erro desconhecido",
  "bug crítico", "problema recorrente", "falha temporária", "ajuda imediata",
  "erro de sistema", "problema na tela", "internet lenta", "sistema instável",
  "reparo necessário", "conserto urgente", "ajuda técnica", "problema técnico",
  "dúvida sobre pagamento", "fatura incorreta", "configuração errada", "ajuste necessário",
  "falha de conexão", "login não funciona", "acesso negado", "erro de login",
  "senha incorreta", "falha de atualização", "problema de sincronização",
  "mensagem de erro", "alerta crítico", "notificação falha", "problema de rede",
  "intermitente", "reclamação registrada", "suporte imediato", "ticket aberto",
  "incidente reportado", "atendimento pendente", "ajuda online", "problema resolvido"
    ]
    t = text.lower()
    for k in keywords:
        if k in t:
            return "Produtivo"
    # se for curto e for agradecimento -> improdutivo
    if len(t.split()) < 8 and any(x in t for x in [
  "obrigado", "obrigada", "parabéns", "parabens", "feliz", "felicidades", "thanks", "grato",
  "agradecido", "agradecida", "ótimo", "otimo", "excelente", "perfeito", "sucesso", "aproveite",
  "bom trabalho", "ótima iniciativa", "otima iniciativa", "felicidade", "congratulações", "congrats",
  "muito obrigado", "muito obrigada", "valeu", "legal", "fantástico", "fantastica", "ótima", "otima",
  "maravilhoso", "maravilhosa", "ótima notícia", "otima noticia", "alegria", "boas energias",
  "sucesso sempre", "abraço", "abraços", "feliz dia", "feliz aniversário", "parabéns pelo sucesso",
  "muito grato", "muito grata", "aprecio", "apreciado", "agradecemos", "felicitações", "feliz jornada",
  "boas festas", "alegria sempre", "ótimo resultado", "otimo resultado", "gratidão", "thanks a lot",
  "congratulations", "cheers", "bem feito", "bem feita", "boa sorte", "ótima sorte", "otima sorte",
  "felicidade eterna", "ótimo dia", "otimo dia", "viva", "sucesso garantido", "excelente trabalho",
  "parabéns pelo esforço", "bom dia", "boa tarde", "boa noite", "aplausos", "felicidades sempre",
  "tudo de bom", "ótimas notícias", "otimas noticias", "viva você", "muito sucesso", "ótimo trabalho",
  "otimo trabalho", "ótima oportunidade", "otima oportunidade", "parabéns equipe", "grata", "grato muito"
]
):
        return "Improdutivo"
    return "Improdutivo"

def ai_classify(text):
    """
    Usa OpenAI se disponível; caso contrário, retorna classificação por regra.
    """
    if not OPENAI_AVAILABLE:
        return rule_based_classify(text)

    try:
        system = (
            "Você é um assistente que classifica emails em duas categorias: "
            "'Produtivo' (requer ação/resposta) e 'Improdutivo' (não requer ação). "
            "Responda apenas com a palavra 'Produtivo' ou 'Improdutivo'."
        )
        user_prompt = f"Classifique o email abaixo (responda só 'Produtivo' ou 'Improdutivo'):\n\n{text}"
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=6,
            temperature=0
        )
        ans = resp.choices[0].message['content'].strip()
        if "produt" in ans.lower():
            return "Produtivo"
        if "improdut" in ans.lower():
            return "Improdutivo"
        return rule_based_classify(text)
    except Exception:
        return rule_based_classify(text)

def ai_generate_reply(text, category):
    """
    Gera resposta com OpenAI (se disponível). Caso contrário, retorna template curto.
    """
    if OPENAI_AVAILABLE:
        try:
            system = "Você gera respostas profissionais, curtas e objetivas com base no email original."
            user_prompt = (
                f"O email abaixo foi classificado como '{category}'. "
                "Gere uma resposta especifica que ajude a pesssoa a resolver o problema, como se você fosse o dono da empresa e o mais inteligente presente no momento, pode ser grande.\n\n"
                f"Email:\n{text}"
            )
            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=200,
                temperature=0.2
            )
            return resp.choices[0].message['content'].strip()
        except Exception:
            pass

    # fallback sem OpenAI
    if category == "Produtivo":
        return (
            "Olá,\n\nRecebemos sua solicitação e já estamos verificando. "
            "Se possível, envie mais detalhes (print, passo a passo, ou número do pedido). "
            "Voltamos em breve com um retorno."
        )
    else:
        return (
            "Olá,\n\nAgradecemos sua mensagem! "
            "Caso precise de algo específico, nos informe e ajudaremos com prazer. "
            "Atenciosamente."
        )

@app.route("/", methods=["GET", "POST"])
def index():
    resultado = None
    resposta = None
    original_text = None

    if request.method == "POST":
        # texto direto
        email_text = request.form.get("email_text", "").strip()
        # arquivo enviado
        arquivo = request.files.get("arquivo")
        texto = ""

        if arquivo and arquivo.filename:
            fname = arquivo.filename.lower()
            if fname.endswith(".pdf"):
                # PyPDF2 aceita file-like; passamos stream
                texto = extract_text_from_pdf(arquivo.stream)
            elif fname.endswith(".txt"):
                try:
                    texto = arquivo.read().decode("utf-8")
                except Exception:
                    # fallback em outra codificação
                    texto = arquivo.read().decode("latin-1", errors="ignore")
            else:
                texto = ""
        else:
            texto = email_text

        texto = preprocess(texto)
        original_text = texto

        if not texto:
            resultado = "Improdutivo"
            resposta = "Não foi detectado texto no email/enviado. Verifique o arquivo ou cole o texto."
        else:
            # classificação e geração de resposta (usa OpenAI se disponível)
            resultado = ai_classify(texto)
            resposta = ai_generate_reply(texto, resultado)

    return render_template("index.html",
                           resultado=resultado,
                           resposta=resposta,
                           original=original_text)

if __name__ == "__main__":
    # debug True só em dev
    app.run(debug=True)
