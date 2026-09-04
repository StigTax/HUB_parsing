import scrapy


class HubGallerySpider(scrapy.Spider):
    name = 'HUB_gallery'
    allowed_domains = ['hub.saint-gobain.ru']
    start_urls = ['https://hub.saint-gobain.ru/gallery']

    custom_settings = {
        'USER_AGENT': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/124.0.0.0 Safari/537.36'
        ),
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_page_goto_kwargs": {
                        "wait_until": "domcontentloaded"
                    },
                },
            )

    def parse(self, response):
        for a in response.css('a[href^="/gallery/"]'):
            href = a.attrib.get("href", "")
            if href in ("/gallery", "/gallery/map") or "page=" in href:
                continue
            title = a.css("::text").get()
            if title and title.strip():
                yield response.follow(
                    href,
                    callback=self.parse_object,
                    meta={
                        "playwright": True,
                        "playwright_page_goto_kwargs": {
                            "wait_until": "domcontentloaded"
                        },
                    }
                )

        next_page = response.css(
            'a[title="На следующую страницу"]::attr(href)'
        ).get()
        if next_page:
            yield response.follow(
                next_page,
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_page_goto_kwargs": {
                        "wait_until":
                        "domcontentloaded"
                    },
                }
            )

    def parse_object(self, response):
        object_url = response.url

        for set_item in response.css("div.project__set-item"):
            breadcrumb = set_item.css(
                "div.field--name-field-construction span.term--breadcrumb-style--item::text"
            ).getall()
            construction_type = " > ".join(
                t.strip() for t in breadcrumb if t.strip()
            )

            for material_item in set_item.css(
                "div.field--name-products-set > div.field__item"
            ):
                material_type = " ".join(
                    part.strip()
                    for part in material_item.css(
                        "div.field--name-label ::text"
                    ).getall()
                    if part.strip()
                )

                product_links = material_item.css(
                    "div.field--name-products div.field--name-product a::attr(href)"
                ).getall()

                if product_links:
                    for link in product_links:
                        material_url = response.urljoin(link)
                        yield scrapy.Request(
                            material_url,
                            callback=self.parse_material_status,
                            errback=self.material_status_failed,
                            dont_filter=True,
                            meta={
                                "handle_httpstatus_all": True,
                                "Ссылка на объект": object_url,
                                "Тип конструкции": construction_type,
                                "Тип материала": material_type,
                                "Ссылка на материал": material_url,
                            },
                        )
                else:
                    yield {
                        "Ссылка на объект": object_url,
                        "Тип конструкции": construction_type,
                        "Тип материала": material_type,
                        "Ссылка на материал": "",
                        "Статус ответа": "",
                    }

    def parse_material_status(self, response):
        yield {
            "Ссылка на объект": response.meta["Ссылка на объект"],
            "Тип конструкции": response.meta["Тип конструкции"],
            "Тип материала": response.meta["Тип материала"],
            "Ссылка на материал": response.meta["Ссылка на материал"],
            "Статус ответа": response.status,
        }

    def material_status_failed(self, failure):
        meta = failure.request.meta
        yield {
            "Ссылка на объект": meta["Ссылка на объект"],
            "Тип конструкции": meta["Тип конструкции"],
            "Тип материала": meta["Тип материала"],
            "Ссылка на материал": meta["Ссылка на материал"],
            "Статус ответа": "ERROR",
        }
