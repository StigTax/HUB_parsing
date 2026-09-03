from itemadapter import ItemAdapter
from openpyxl import Workbook


class HubScrapyPipeline:
    def process_item(self, item):
        return item


class NumberingPipeline:
    def open_spider(self, spider):
        self.counter = 0

    def process_item(self, item, spider):
        self.counter += 1
        return {"№": self.counter, **item}


class XlsxExportPipeline:
    def open_spider(self, spider):
        self.wb = Workbook()
        self.ws = self.wb.active
        self.header_written = False

    def process_item(self, item, spider):
        if not self.header_written:
            self.ws.append(list(item.keys()))
            self.header_written = True
        self.ws.append(list(item.values()))
        return item

    def close_spider(self, spider):
        self.wb.save("materials.xlsx")
