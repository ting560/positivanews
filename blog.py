import sys
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# ===========================
# Configuração UTF-8
# ===========================
sys.stdout.reconfigure(encoding='utf-8')

# ===========================
# Configuração Hugging Face (mantido, mas a reescrita é simplificada para robustez)
# ===========================
# Nota: A API do Hugging Face para reescrita complexa pode ser instável ou exigir modelos específicos
# para ter um bom desempenho em reescritas sem "hallucinar".
# A implementação atual usa um fallback simples de substituição de palavras.
HF_API_KEY = "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" # Use sua própria chave API real se for usar um modelo complexo
# Modelo especializado em português (exemplo, pode não ser o ideal para reescrita)
API_URL = "https://api-inference.huggingface.co/models/pysentimiento/robertuito-base-uncased"
headers = {"Authorization": f"Bearer {HF_API_KEY}"}

def reescrever_com_ia(texto):
    """
    Função que tenta reescrever um texto usando a API do Hugging Face.
    Devido à complexidade e possíveis falhas da API para reescrita de estilo,
    um fallback de substituição simples é prioritário.
    """
    try:
        # Nota: O modelo 'deepset/roberta-base-squad2' é para Question Answering, não para reescrita.
        # Para reescrita, você precisaria de um modelo Text Generation (e.g., GPT-2, T5, BART ou similares finetunados).
        # A lógica atual de prompt com esse modelo não gerará uma reescrita, mas sim uma "resposta" ao prompt.
        # Por isso, o fallback simples é mais robusto para a proposta de "reescrita" atual do script.

        # Se você realmente quiser usar um modelo de geração de texto, o endpoint e o payload seriam diferentes:
        # response = requests.post(
        #     "https://api-inference.huggingface.co/models/google/flan-t5-base", # Exemplo de modelo de geração
        #     headers=headers,
        #     json={"inputs": prompt, "parameters": {"max_new_tokens": 200}},
        #     timeout=30
        # )

        # Por enquanto, mantemos a substituição simples, que é o que o seu script efetivamente faz
        # e é mais garantida para o objetivo de evitar erros de escrita.
        print(f"⚠️ Hugging Face API para reescrita complexa não configurada/testada para este fim. Usando reescrita simples.")
        return texto.replace("segundo", "conforme").replace("disse", "afirmou").replace("não irá", "não deve")

    except Exception as e:
        print(f"⚠️ Falha na IA. Usando texto original: {e}")
        return texto

# ===========================
# Configuração do Selenium
# ===========================
options = Options()
# A opção --headless=new é a mais recente e recomendada.
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080") # Adicionar para headless funcionar melhor
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
options.add_argument("--log-level=3") # Suprimir logs desnecessários do Chrome

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    # Abrir página de notícias recentes
    print("Iniciando navegação para notícias recentes...")
    driver.get("https://br.bolavip.com/noticias-recentes")
    WebDriverWait(driver, 20).until( # Aumentar tempo de espera para páginas lentas
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.most-read-card__data a"))
    )
    print("Página de notícias recentes carregada.")

    # Pegar o link da primeira notícia
    soup_home = BeautifulSoup(driver.page_source, "html.parser")
    link_tag = soup_home.select_one("div.most-read-card__data a")

    if not link_tag or not link_tag.get("href"):
        print("❌ Não foi possível encontrar o link da notícia principal na página de notícias recentes.")
        exit()

    base_url = "https://br.bolavip.com"
    href = link_tag["href"]
    link_noticia = base_url + (href if href.startswith("/") else "/" + href)

    print(f"🔗 Acessando a notícia: {link_noticia}")
    driver.get(link_noticia)

    # Esperar carregamento completo da página da notícia
    WebDriverWait(driver, 20).until( # Aumentar tempo de espera
        EC.presence_of_element_located((By.TAG_NAME, "h1"))
    )
    # Dar um tempo extra para o JS carregar o conteúdo dinamicamente
    time.sleep(5)
    print("Página da notícia carregada.")

    # Extrair dados
    soup = BeautifulSoup(driver.page_source, "html.parser")

    titulo_tag = soup.find("h1")
    titulo = titulo_tag.get_text(strip=True) if titulo_tag else "Sem título"
    print(f"Título encontrado: {titulo}")

    # =============== IMAGEM PRINCIPAL (CORRIGIDA E MAIS ROBUSTA) ===============
    img_src = ""

    # Tenta encontrar a imagem principal dentro de <figure>
    img_tag = soup.select_one("figure img")
    if img_tag:
        img_src = img_tag.get("data-src") or img_tag.get("src", "")
        print(f"Imagem da figura encontrada: {img_src}")

    # Se ainda não tiver, busca por qualquer imagem que possa ser a principal
    if not img_src:
        for img in soup.find_all("img"):
            src = img.get("data-src") or img.get("src")
            # Heurística para tentar pegar uma imagem grande de conteúdo
            if src and ("webp" in src or "jpg" in src or "jpeg" in src or "png" in src) and ("full" in src or "content" in src or "article" in src) and ("thumbnail" not in src):
                img_src = src
                print(f"Imagem heurística encontrada: {img_src}")
                break
    
    # Se ainda não encontrar, pega a primeira imagem razoável que não seja muito pequena (ícones)
    if not img_src:
        for img in soup.find_all("img"):
            src = img.get("data-src") or img.get("src")
            if src and not src.startswith("data:") and img.get('width', '100') and int(img.get('width', '100')) > 100: # Evita ícones/miniaturas
                img_src = src
                print(f"Primeira imagem razoável encontrada: {img_src}")
                break

    # Garante URL completo
    if img_src and not img_src.startswith("http"):
        img_src = base_url + (img_src if img_src.startswith("/") else "/" + img_src)
        print(f"URL da imagem completa: {img_src}")
    elif not img_src:
        print("Nenhuma imagem principal encontrada.")

    # =============== CONTEÚDO (COM CORREÇÃO DE ESPAÇOS E ADIÇÃO DE ID/CLASSE) ===============
    paragrafos_texto = [] # Lista para armazenar o texto limpo dos parágrafos
    paragrafos_html = []  # Lista para armazenar o HTML dos parágrafos com ID/Classe

    # Prioriza parágrafos com atributo de conteúdo específico do site
    for p in soup.select('div[data-mrf-section-type="paragraph"]'):
        txt = p.get_text(separator=' ', strip=True)
        if len(txt) > 50:
            paragrafos_texto.append(txt)
    
    print(f"Parágrafos encontrados via 'data-mrf-section-type': {len(paragrafos_texto)}")

    # Se não encontrar conteúdo por essa heurística, tenta classes comuns de artigo
    if not paragrafos_texto:
        print("Tentando encontrar parágrafos via classes comuns (div.article-body p, article p)...")
        for p in soup.select("div.article-body p, article p"):
            txt = p.get_text(separator=' ', strip=True)
            if len(txt) > 50 and "function" not in txt.lower():
                paragrafos_texto.append(txt)
        print(f"Parágrafos encontrados via classes comuns: {len(paragrafos_texto)}")


    if not paragrafos_texto:
        print("❌ Nenhum parágrafo de conteúdo significativo encontrado. O layout do site pode ter mudado.")
        exit()

    # =============== REESCREVER COM IA (SIMPLES MAS FUNCIONAL) E PREPARAR HTML COM IDS ===============
    for i, paragrafo_original in enumerate(paragrafos_texto):
        texto_limpo = paragrafo_original
        for antigo, novo in {
            "segundo": "conforme",
            "disse": "afirmou",
            "revelou": "informou",
            "nesta terça-feira": "hoje",
            "não irá": "não deve",
            "vai ser": "será",
            "terá": "deve ter",
            "o jogador": "o atleta"
        }.items():
            texto_limpo = texto_limpo.replace(antigo, novo).replace(antigo.capitalize(), novo.capitalize())
        
        # Adiciona id e classe para cada parágrafo
        paragrafos_html.append(f'<p id="p-{i}" class="article-paragraph">{texto_limpo}</p>\n')
    
    conteudo_html = "".join(paragrafos_html)

    # =============== GERAR HTML ===============
    html_final = f'''<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{titulo}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
            background-color: #f8f9fa;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1a1a1a;
            text-align: center;
            font-size: 1.8em;
            margin-bottom: 20px;
            line-height: 1.3;
        }}
        img {{
            width: 100%; /* Garante que não ultrapasse o contêiner */
            max-width: 600px; /* Largura máxima da imagem */
            height: 350px; /* Altura fixa para todas as imagens */
            object-fit: contain; /* Ajusta a imagem dentro da caixa, mantendo a proporção */
            border-radius: 10px;
            margin: 25px auto; /* Centraliza a imagem horizontalmente */
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            display: block; /* Necessário para margin: auto funcionar */
        }}
        p {{
            font-size: 17px;
            margin-bottom: 18px;
            text-align: justify;
            color: #444;
            line-height: 1.7;
        }}
        /* Estilo para o parágrafo sendo lido */
        p.highlighted-paragraph {{
            background-color: #ffff99; /* Amarelo claro */
            padding: 5px;
            border-radius: 5px;
            transition: background-color 0.3s ease;
        }}
        .audio-button-container {{
            text-align: center;
            margin: 20px 0;
        }}
        #playPauseBtn {{
            background-color: #007acc;
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 8px;
            font-size: 1.1em;
            cursor: pointer;
            transition: background-color 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }}
        #playPauseBtn:hover {{
            background-color: #005f99;
        }}
        #playPauseBtn:active {{
            transform: translateY(1px);
        }}
        #playPauseBtn.playing {{
            background-color: #d9534f; /* Cor para indicar que está tocando/pausado */
        }}
        #playPauseBtn.playing:hover {{
            background-color: #c9302c;
        }}
        footer {{
            margin-top: 40px;
            font-size: 0.9em;
            color: #777;
            text-align: center;
            border-top: 1px solid #eee;
            padding-top: 20px;
        }}
        footer a {{
            color: #007acc;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{titulo}</h1>
        {f'<img src="{img_src}" alt="Imagem da notícia">' if img_src else ''}
        
        <div class="audio-button-container">
            <button id="playPauseBtn">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                    <path d="M8 5V19L19 12L8 5Z" class="play-icon"/>
                    <path d="M6 6H9V18H6V6ZM15 6H18V18H15V6Z" class="pause-icon" style="display:none;"/>
                </svg>
                Ouvir Matéria
            </button>
        </div>

        <div class="article-content-wrapper">
            {conteudo_html}
        </div>
        
        <footer>
        (Ganhe R$30: <a href="https://referme.to/marcosaureliop-71" target="_blank">clique aqui</a>)</p>
        </footer>
    </div>

    <script>
        let currentParagraphIndex = 0;
        let currentUtterance = null;
        let isSpeaking = false; // true if speech is active (playing or paused)

        // Function to update button icons (play/pause)
        function updateButtonIcons(isPlayingVisual) {{ // isPlayingVisual reflects if speech is actively playing
            const playIcon = document.querySelector('.play-icon');
            const pauseIcon = document.querySelector('.pause-icon');
            if (isPlayingVisual) {{
                playIcon.style.display = 'none';
                pauseIcon.style.display = 'block';
            }} else {{
                playIcon.style.display = 'block';
                pauseIcon.style.display = 'none';
            }}
        }}

        // Function to clear highlighting from all paragraphs
        function clearHighlighting() {{
            document.querySelectorAll('p.article-paragraph').forEach(p => {{
                p.classList.remove('highlighted-paragraph');
            }});
        }}

        // Function to speak the next paragraph in sequence
        function speakNextParagraph() {{
            clearHighlighting(); // Remove highlight from previous paragraph

            const paragraphs = document.querySelectorAll('.container p.article-paragraph'); 

            if (currentParagraphIndex < paragraphs.length) {{
                const paragraphToSpeak = paragraphs[currentParagraphIndex];
                paragraphToSpeak.classList.add('highlighted-paragraph'); // Add highlight to current paragraph

                // Optionally scroll to the highlighted paragraph
                paragraphToSpeak.scrollIntoView({{ behavior: 'smooth', block: 'center' }});

                currentUtterance = new SpeechSynthesisUtterance(paragraphToSpeak.innerText);
                currentUtterance.lang = 'pt-BR';
                currentUtterance.rate = 2;  // Velocidade definida
                currentUtterance.pitch = 1; // Tom definido

                currentUtterance.onend = () => {{
                    currentParagraphIndex++;
                    speakNextParagraph(); // Call itself to speak the next paragraph
                }};

                currentUtterance.onerror = (event) => {{
                    console.error('Erro na síntese de fala:', event.error);
                    isSpeaking = false;
                    playPauseBtn.textContent = 'Ouvir Matéria';
                    playPauseBtn.classList.remove('playing');
                    updateButtonIcons(false);
                    clearHighlighting();
                    alert('Ocorreu um erro ao tentar reproduzir o áudio. Tente novamente ou verifique as configurações do seu navegador.');
                    window.speechSynthesis.cancel(); // Ensure all is stopped on error
                }};

                window.speechSynthesis.cancel(); // Stop any previous speech before starting a new one
                window.speechSynthesis.speak(currentUtterance);
                isSpeaking = true; // Mark as speaking (or about to speak)
                playPauseBtn.textContent = 'Pausar Leitura';
                playPauseBtn.classList.add('playing');
                updateButtonIcons(true);

            }} else {{
                // All paragraphs have been spoken
                isSpeaking = false;
                playPauseBtn.textContent = 'Ouvir Matéria';
                playPauseBtn.classList.remove('playing');
                updateButtonIcons(false);
                clearHighlighting();
                currentParagraphIndex = 0; // Reset index for next full play
            }}
        }}

        playPauseBtn.addEventListener('click', () => {{
            if (!('speechSynthesis' in window)) {{
                alert('Seu navegador não suporta a síntese de fala.');
                return;
            }}

            if (isSpeaking && !window.speechSynthesis.paused) {{
                // If currently playing, pause it
                window.speechSynthesis.pause();
                isSpeaking = false; // No longer actively speaking, but paused
                playPauseBtn.textContent = 'Continuar Lendo';
                playPauseBtn.classList.remove('playing');
                updateButtonIcons(false);
            }} else if (window.speechSynthesis.paused) {{
                // If paused, resume
                window.speechSynthesis.resume();
                isSpeaking = true; // Back to actively speaking
                playPauseBtn.textContent = 'Pausar Leitura';
                playPauseBtn.classList.add('playing');
                updateButtonIcons(true);
            }} else {{
                // Not speaking and not paused (first play or finished last time), so start from beginning/current index
                currentParagraphIndex = 0; // Ensure start from first paragraph on new play
                speakNextParagraph();
            }}
        }});

        // Ensure speech is cancelled on page unload (browser tab/window close)
        window.addEventListener('beforeunload', () => {{
            if (window.speechSynthesis.speaking) {{
                window.speechSynthesis.cancel();
            }}
        }});

        // Optional: Reset button if speech is cancelled by another means (e.g., new tab/window, system speech service stops)
        window.speechSynthesis.onvoiceschanged = () => {{
            if (!window.speechSynthesis.speaking && (isSpeaking || window.speechSynthesis.paused)) {{
                isSpeaking = false;
                playPauseBtn.textContent = 'Ouvir Matéria';
                playPauseBtn.classList.remove('playing');
                updateButtonIcons(false);
                clearHighlighting();
                currentParagraphIndex = 0;
                window.speechSynthesis.cancel(); // Just to be sure
            }}
        }};
        
        // Also handle if speech ends for external reasons (e.g. system speech service stops unexpectedly)
        window.speechSynthesis.onend = () => {{
             if (!window.speechSynthesis.speaking && (isSpeaking || window.speechSynthesis.paused)) {{
                isSpeaking = false;
                playPauseBtn.textContent = 'Ouvir Matéria';
                playPauseBtn.classList.remove('playing');
                updateButtonIcons(false);
                clearHighlighting();
                currentParagraphIndex = 0;
            }}
        }};
    </script>
</body>
</html>'''

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_final)

    print("https://referme.to/marcosaureliop-71")

except Exception as e:
    print(f"❌ Erro inesperado: {e}")
    # Opcional: imprimir o source da página em caso de erro para debug
    # with open("error_page_source.html", "w", encoding="utf-8") as f:
    #     f.write(driver.page_source)
    # print("Conteúdo da página em erro salvo em error_page_source.html para depuração.")
finally:
    if driver:
        driver.quit()
