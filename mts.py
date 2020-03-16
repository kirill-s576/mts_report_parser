# -*- coding: utf-8 -*-

# pip install fitz

import fitz
import re
import os

def null_except(tuple:list, element:int):
    """ Отработка несуществующего элемента списка. Вспомогательная функция."""
    try:
        return tuple[element]
    except:
        return ""

class PdfDocument(object):
    """ Объект PDF документа. Работает с библиотекой fitz. Отдает данные из документа в строковом представлении."""
    def __init__(self, directory):
        self.pdf = fitz.Document(directory)

    def all_text(self):
        text = ""
        for number in range(1, self.pdf.pageCount):
            text += self.pdf.loadPage(number).getText()
        return text

    def pages(self):
        pages = []
        for number in range(1, self.pdf.pageCount):
            pages.append(self.pdf.loadPage(number).getText())
        return pages

    def page(self, number: int):
        return self.pdf.loadPage(number).getText()

    def numbers_list(self):
        numbers_list = re.findall(r'(375[\d]{9})\s+?Общество с ограниченной', self.all_text(), flags=re.DOTALL)
        return numbers_list


class Phone(object):
    """ Объект номера телефона из отчета"""
    def __init__(self, document: PdfDocument, number: str):
        self.document = document
        self.number = number
        self.short_info_text = self.short_info()
        self.long_info_text = self.long_info()

    def short_info(self):
        regular = r'Абонентский номер:\s+' + self.number + ',\s+Общ.*?Итого начислений по абонентскому номеру с учетом округлений\s+\d+,\d{2}'
        short = re.findall(regular, self.document.all_text(), flags=re.DOTALL)
        return null_except(short, 0)

    def long_info(self):
        text = self.document.all_text()
        text = re.sub(r'\n', " ", text)
        regular = r'Абонентский номер:  ' + self.number + ', Общество с ограниченной ответственностью "БелВэйп" Дата Время Номер Зона ПС Зона ВТК Услуга Длит. мин:сек Стоимость без налога, бел.руб. Стоимость c налогом, бел.руб.(.*?)Страница'
        array = re.findall(regular, text, flags=re.DOTALL)
        string = " ".join(array)
        return string

    def long_objects_array(self):
        string = self.long_info_text
        array = re.findall(r'(\d{2}\.\d{2}\.20\d\d.+?)[\s\n]+?\d\d', string)
        return array


class ShortInfo(Phone):
    """ Парсер короткой информации о номере телефона. НАследует целиком класс Phone """
    def tarif(self):
        tarif = re.findall(r'Тарифные планы:\s+(.*?)\s+?\d{2}.\d{2}.20\d\d', self.short_info_text)
        return tarif

    def period(self):
        period = re.findall(r'\d{2}.\d{2}.20\d\d - \d{2}.\d{2}.20\d\d', self.short_info_text)
        return period

    def sim_number(self):
        sim = re.findall(r'№ SIM-карты:\s\s(\d*)', self.short_info_text)
        return sim

    def sum_result(self):
        sum_result = re.findall(r'Итого начислений по абонентскому номеру с учетом округлений\s+(\d+,\d{2})', self.short_info_text)
        return sum_result

    def to_dict(self, tuple:list):
        dict = {}
        dict["time"] = null_except(null_except(tuple, 0), 0)
        dict["without_NDS"] = null_except(null_except(tuple, 0), 1)
        dict["with_NDS"] = null_except(null_except(tuple, 0), 2)
        return dict

    def parse_param(self, param:str):
        parse = re.findall(r'' + param + '.*?(\d{2}:\d{2}:\d{2}).*?(\d*,\d*).*?(\d*,\d*)',
                         self.short_info_text, flags=re.DOTALL)
        return parse

    def out_A1(self):
        out = self.parse_param("Исходящая связь: телефоны A1")
        return self.to_dict(out)

    def out_LIFE(self):
        out = self.parse_param("Исходящая связь: телефоны БЕСТ")
        return self.to_dict(out)

    def out_MTS(self):
        out = self.parse_param("Исходящая связь: мобильная на абонентов МТС")
        return self.to_dict(out)

    def json(self):
        return {
            "tarif": null_except(self.tarif(), 0),
            "period": null_except(self.period(), 0),
            "sum": null_except(self.sum_result(), 0),
            "detail": {
                "a1": self.out_A1(),
                "mts": self.out_MTS(),
                "life": self.out_LIFE()
            }
        }

class LongInfo(object):
    """ Детализация по номеру телефона. Для инициализации надо передать объект ShortInfo"""
    def __init__(self, short_phone_object):
        self.phone = short_phone_object
        self.info = self.phone.long_info()

    def sruct(self):
        result = re.findall(r'(\d{2}\.\d{2}\.\d{4})\s(\d{2}:\d{2}:\d{2})(.*?)(\d+?,[\d]{4}).*?\d{2}\.\d{2}\.', self.info, flags=re.DOTALL)
        return result

    def json(self):
        array = []
        parse = self.sruct()
        for obj in parse:
            new = {
                "date": obj[0],
                "time": obj[1],
                "sum": obj[3],
                "detail": obj[2],
            }
            if new["sum"] > "0,0000":
                array.append(new)
        return array

# doc = PdfDocument("files/MTS_207314557089_202002_8906694134.pdf")
# short = ShortInfo(doc, "375339048666")
# long = LongInfo(short)

abc = os.listdir(path="files")

class MTS_parsing_interface(object):
    pass