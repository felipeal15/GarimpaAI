import re


# Palavras "vazias" do português, ignoradas ao construir padrões dinâmicos
# e ao calcular overlap entre busca e blacklist.
STOP_WORDS = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas",
    "de", "do", "da", "dos", "das",
    "em", "no", "na", "nos", "nas",
    "para", "por", "pela", "pelo",
    "com", "sem", "e", "ou",
}


# Acessórios agrupados por categoria. Cada item pode ser palavra ou frase curta.
# Quando o termo buscado tem alguma palavra significativa que aparece em uma
# categoria, o grupo INTEIRO é desligado do filtro automático (afinal o
# usuário está procurando exatamente aquela categoria).
ACCESSORY_GROUPS = {
    "capa": [
        "capa", "capinha", "case", "cover", "bumper", "skin",
    ],
    "pelicula": [
        "pelicula", "protetor de tela",
        "vidro temperado", "pelicula de privacidade",
    ],
    "cabo": [
        "cabo usb", "cabo lightning", "cabo tipo c", "cabo tipo-c",
    ],
    "carregador": [
        "carregador", "adaptador", "fonte usb", "dock",
        "base carregadora", "powerbank", "power bank",
    ],
    "fone": [
        "fone de ouvido", "fones de ouvido", "headset",
        "earphone", "earbud", "headphone",
    ],
    "suporte": [
        "suporte", "holder", "tripe",
        "selfie stick", "pau de selfie",
    ],
    "estojo": [
        "estojo", "bolsa case", "sleeve",
    ],
    "reposicao": [
        "tampa traseira", "back cover",
        "tela de reposicao", "tela substituicao",
        "lente da camera", "lente camera",
    ],
    "outros": [
        "adesivo", "skin para",
        "kit reparo", "kit de reparo", "ferramenta",
    ],
}

# Lista plana para uso direto (e iteração simples).
ACCESSORY_KEYWORDS = [kw for grupo in ACCESSORY_GROUPS.values() for kw in grupo]


# Padrões regex dinâmicos que indicam acessório PARA outro produto.
# A palavra {word} é substituída por cada palavra significativa do termo buscado.
ACCESSORY_PHRASE_PATTERNS = [
    r"\bpara\s+(?:o\s+|a\s+|os\s+|as\s+|seu\s+|sua\s+|meu\s+|minha\s+)?{word}\b",
    r"\bcompativel\s+(?:com|para)\s+(?:o\s+|a\s+)?{word}\b",
    r"\bp/\s*{word}\b",
]


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


def _significant_words(text):
    """Retorna o conjunto de palavras "significativas" (sem stop words, len>=3)."""
    if not text:
        return set()
    return {
        w for w in remove_acentos_regex(text).lower().split()
        if len(w) >= 3 and w not in STOP_WORDS
    }


def _group_significant_words(group_keywords):
    """Conjunto das palavras significativas de um grupo de acessórios."""
    words = set()
    for kw in group_keywords:
        for w in remove_acentos_regex(kw).lower().split():
            if len(w) >= 3 and w not in STOP_WORDS:
                words.add(w)
    return words


def contains_blacklisted_keyword(titulo, blacklist):
    """Retorna True se 'titulo' contiver qualquer palavra/frase de 'blacklist'.

    - Frases (com espaço) usam contains direto.
    - Palavras únicas usam fronteira de palavra (\\b...\\b) para evitar
      falsos positivos do tipo "case" casando em "telecase".
    """
    if not titulo or not blacklist:
        return False

    tl = remove_acentos_regex(titulo).lower()
    for kw in blacklist:
        kw_norm = remove_acentos_regex(kw).lower().strip()
        if not kw_norm:
            continue
        if " " in kw_norm:
            if kw_norm in tl:
                return True
        else:
            if re.search(rf"\b{re.escape(kw_norm)}\b", tl):
                return True

    return False


def search_targets_accessory(search_term):
    """Retorna True se a busca já é direcionada a alguma categoria de acessório.

    Ex.: 'capa iphone', 'carregador apple', 'fone bluetooth' devolvem True,
    enquanto 'iphone 13', 'samsung galaxy s23' devolvem False.
    """
    search_words = _significant_words(search_term)
    if not search_words:
        return False
    for group_keywords in ACCESSORY_GROUPS.values():
        if search_words & _group_significant_words(group_keywords):
            return True
    return False


def build_search_aware_blacklist(search_term):
    """Retorna a blacklist de acessórios, removendo grupos relacionados à busca.

    Cada grupo (capa, película, cabo, carregador, fone, suporte, etc.) é
    incluído ou descartado por inteiro. Assim, buscar 'capa iphone' desativa
    capa, capinha, case, cover, bumper e skin — mas continua filtrando
    película, cabo, carregador etc.
    """
    if not search_term:
        return list(ACCESSORY_KEYWORDS)

    search_words = _significant_words(search_term)
    result = []
    for group_keywords in ACCESSORY_GROUPS.values():
        if search_words & _group_significant_words(group_keywords):
            continue  # busca pede esta categoria — desliga o grupo inteiro
        result.extend(group_keywords)
    return result


def is_accessory_for_search(titulo, search_term):
    """Detecta padrões 'para X', 'compatível com X' ou 'p/ X' no título.

    Padrão que já apareça no próprio termo buscado é ignorado (caso
    'tinta para parede' não filtre o próprio produto buscado).
    """
    if not titulo or not search_term:
        return False

    titulo_norm = remove_acentos_regex(titulo).lower()
    search_norm = remove_acentos_regex(search_term).lower()

    search_words = [
        w for w in search_norm.split()
        if len(w) >= 3 and w not in STOP_WORDS
    ]
    if not search_words:
        return False

    for word in search_words:
        for tpl in ACCESSORY_PHRASE_PATTERNS:
            pat = tpl.format(word=re.escape(word))
            # Padrão presente na própria busca não conta como acessório.
            if re.search(pat, search_norm):
                continue
            if re.search(pat, titulo_norm):
                return True
    return False


def validate_product_relevance(produto_buscado, titulo_produto, min_similarity, blacklist=None):
    """Decide se o produto é relevante para o termo buscado.

    Aplica, nessa ordem:
      1. Blacklist automática de acessórios (consciente do termo buscado).
      2. Detecção de padrões 'para X' / 'compatível com X' / 'p/ X'
         (desligada se a própria busca já é por uma categoria de acessório).
      3. Blacklist extra opcional fornecida pelo usuário.
      4. Similaridade mínima.
    """
    if not titulo_produto:
        return False

    auto_blacklist = build_search_aware_blacklist(produto_buscado)
    if contains_blacklisted_keyword(titulo_produto, auto_blacklist):
        return False

    if not search_targets_accessory(produto_buscado):
        if is_accessory_for_search(titulo_produto, produto_buscado):
            return False

    if blacklist and contains_blacklisted_keyword(titulo_produto, blacklist):
        return False

    sim = calculate_similarity(produto_buscado, titulo_produto)
    return sim >= min_similarity
