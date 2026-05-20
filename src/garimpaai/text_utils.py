import re


def remove_acentos_regex(texto):
    texto = re.sub(r"[áàâãä]", "a", texto, flags=re.IGNORECASE)
    texto = re.sub(r"[éèêë]", "e", texto, flags=re.IGNORECASE)
    texto = re.sub(r"[íìîï]", "i", texto, flags=re.IGNORECASE)
    texto = re.sub(r"[óòôõö]", "o", texto, flags=re.IGNORECASE)
    texto = re.sub(r"[úùûü]", "u", texto, flags=re.IGNORECASE)
    texto = re.sub(r"[ç]", "c", texto, flags=re.IGNORECASE)
    return texto


def clean_price(price_text):
    """Converte texto de preço (ex.: "R$ 2.999,00") em float (2999.0)."""
    if not price_text:
        return None

    text = re.sub(r"[^\d,\.]", "", price_text.replace("R$", "").strip())

    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")

    try:
        return float(text)
    except Exception:
        return None


def clean_title(title):
    """Remove quebras de linha e espaços duplicados do título."""
    return re.sub(r"\s+", " ", title.strip()) if title else ""


def calculate_similarity(produto_buscado, titulo_encontrado):
    """Calcula (|palavras em comum| / |palavras do termo buscado|)."""
    produto_words = set(remove_acentos_regex(produto_buscado).lower().split())
    titulo_words = set(remove_acentos_regex(titulo_encontrado).lower().split())

    if not produto_words:
        return 0

    intersec = produto_words.intersection(titulo_words)
    return len(intersec) / len(produto_words)


def contains_blacklisted_keyword(titulo, blacklist):
    """Retorna True se 'titulo' contiver qualquer palavra de 'blacklist'."""
    if not titulo:
        return False

    tl = remove_acentos_regex(titulo).lower()
    for kw in blacklist:
        if remove_acentos_regex(kw).lower() in tl:
            return True

    return False


def validate_product_relevance(produto_buscado, titulo_produto, min_similarity, blacklist):
    """Combina blacklist + similaridade mínima para validar relevância."""
    if contains_blacklisted_keyword(titulo_produto, blacklist):
        return False

    sim = calculate_similarity(produto_buscado, titulo_produto)
    return sim >= min_similarity
