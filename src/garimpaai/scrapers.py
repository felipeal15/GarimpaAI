import random
import time
import re

from bs4 import BeautifulSoup

from .browser import get_driver
from .text_utils import (
    calculate_similarity,
    clean_price,
    clean_title,
    validate_product_relevance,
)


def abre_amazon_para_busca(produto, page=1):
    """Abre a URL de busca da Amazon (Selenium) e retorna o HTML completo."""
    termo = produto.replace(" ", "+")
    url_busca = f"https://www.amazon.com.br/s?k={termo}&page={page}"
    print("URL de busca:", url_busca)

    driver = get_driver()
    driver.get(url_busca)
    time.sleep(random.uniform(4, 10))
    return driver.page_source


def abre_americanas_para_busca(produto, page=0):
    """Abre a URL de busca da Americanas (Selenium) e retorna o HTML completo."""
    termo = produto.replace(" ", "+")
    url_busca = f"https://www.americanas.com.br/s?q={termo}&sort=score_desc&page={page}"
    print("URL de busca:", url_busca)

    driver = get_driver()
    driver.get(url_busca)
    time.sleep(random.uniform(6, 8))
    return driver.page_source


def scrape_amazon_selenium(produto, max_pages=3, min_similarity=0.3, extra_blacklist=None):
    resultados = []

    print(
        f"🔍 Buscando (Selenium) por: '{produto}'  |  Páginas: {max_pages}  |  Sim. mínima: {min_similarity:.1%}"
    )
    print("-" * 60)

    combined_blacklist = extra_blacklist or []

    for page in range(1, max_pages + 1):
        html = abre_amazon_para_busca(produto, page)
        soup = BeautifulSoup(html, "html.parser")

        selectors = [
            'div[data-component-type="s-search-result"]',
            ".s-result-item",
            "[data-asin]",
        ]

        product_containers = []
        for sel in selectors:
            product_containers = soup.select(sel)
            if product_containers:
                break

        if not product_containers:
            print(f"· Página {page}: sem produtos.")
            time.sleep(random.uniform(2, 5))
            continue

        relevantes_pagina = 0
        for container in product_containers:
            try:
                title = None
                title_selectors = [
                    "h2 a span",
                    "h2 span",
                    ".a-size-base-plus",
                    ".a-size-medium",
                    ".s-size-mini",
                ]

                for sel in title_selectors:
                    elem = container.select_one(sel)
                    if elem and elem.get_text().strip():
                        title = clean_title(elem.get_text())
                        break

                if not title or len(title) < 5:
                    continue

                if not validate_product_relevance(
                    produto, title, min_similarity, combined_blacklist
                ):
                    continue

                price = None
                price_selectors = [
                    ".a-price-whole",
                    ".a-price .a-offscreen",
                    ".a-price-range .a-offscreen",
                    'span[data-a-color="price"]',
                    ".a-price-symbol + .a-price-whole",
                ]

                for sel in price_selectors:
                    pelem = container.select_one(sel)
                    if pelem:
                        price = clean_price(pelem.get_text())
                        if price and price > 0:
                            break

                link = None
                link_elem = container.select_one("h2 a")
                if link_elem:
                    href = link_elem.get("href", "")
                    if href.startswith("/"):
                        link = "https://www.amazon.com.br" + href

                if not link:
                    asin = container.get("data-asin", "").strip()
                    if asin:
                        link = f"https://www.amazon.com.br/dp/{asin}"

                rating = None
                rating_elem = container.select_one(".a-icon-alt")
                if rating_elem:
                    m = re.search(r"(\d+[.,]?\d*)", rating_elem.get_text())
                    if m:
                        try:
                            rating = float(m.group(1).replace(",", "."))
                        except Exception:
                            rating = None

                num_reviews = None
                review_selectors = [
                    'a[href*="#customerReviews"] span',
                    ".a-size-base",
                    'span[aria-label*="estrelas"]',
                ]

                for sel in review_selectors:
                    rev = container.select_one(sel)
                    if rev:
                        m2 = re.search(
                            r"(\d+)",
                            rev.get_text()
                            .replace(".", "")
                            .replace(",", ""),
                        )
                        if m2:
                            try:
                                num_reviews = int(m2.group(1))
                                break
                            except Exception:
                                pass

                if title and price and price > 0:
                    resultados.append(
                        {
                            "titulo": title[:100] + ("..." if len(title) > 100 else ""),
                            "preco": price,
                            "avaliacao": rating,
                            "num_avaliacoes": num_reviews,
                            "link": link,
                            "similaridade": calculate_similarity(produto, title),
                            "pagina": page,
                        }
                    )
                    relevantes_pagina += 1

            except Exception:
                continue

        print(f"· Página {page}: {len(product_containers)} brutos → {relevantes_pagina} relevantes.")
        time.sleep(random.uniform(2, 5))

    return resultados


def scrape_americanas_selenium(produto, max_pages=3, min_similarity=0.3, extra_blacklist=None):
    resultados = []

    print(
        f"🔍 Buscando (Selenium) por: '{produto}'  |  Páginas: {max_pages}  |  Sim. mínima: {min_similarity:.1%}"
    )
    print("-" * 60)

    combined_blacklist = extra_blacklist or []

    for page in range(max_pages):
        html = abre_americanas_para_busca(produto, page)
        soup = BeautifulSoup(html, "html.parser")

        product_containers = soup.find_all(
            "div", class_=lambda c: c and "ProductCard_productInfo" in c
        )

        if not product_containers:
            print(f"· Página {page}: sem produtos.")
            time.sleep(random.uniform(2, 5))
            continue

        relevantes_pagina = 0
        for container in product_containers:
            try:
                titulo_elem = container.select_one("h3")
                if not titulo_elem:
                    continue

                title = clean_title(titulo_elem.get_text())
                if not title or len(title) < 5:
                    continue

                if not validate_product_relevance(
                    produto, title, min_similarity, combined_blacklist
                ):
                    continue

                price = None
                price_elem = container.select_one('span[class*="ProductCard_discountPrice"]')
                if price_elem:
                    price = clean_price(price_elem.get_text())
                if not price or price <= 0:
                    continue

                link = None
                link_elem = container.find_parent("a", href=True)
                if link_elem:
                    href = link_elem.get("href", "")
                    if href.startswith("/"):
                        link = "https://www.americanas.com.br" + href
                    else:
                        link = href

                resultados.append(
                    {
                        "titulo": title[:100] + ("..." if len(title) > 100 else ""),
                        "preco": price,
                        "avaliacao": None,
                        "num_avaliacoes": None,
                        "link": link,
                        "similaridade": calculate_similarity(produto, title),
                        "pagina": page,
                    }
                )
                relevantes_pagina += 1

            except Exception:
                continue

        print(f"· Página {page}: {len(product_containers)} brutos → {relevantes_pagina} relevantes.")
        time.sleep(random.uniform(2, 5))

    return resultados
