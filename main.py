import pdfquery
import json
import glob
import os
import PyPDF2
from utils import format_date, \
                    date_obj_json, \
                    format_float, \
                    formata_historico, \
                    formata_produto, \
                    formata_leitura, \
                    remover_chaves_vazias, \
                    format_outros, \
                    format_fatura

UNIDADE_CONSUMIDORA = "unidade_consumidora"
FATURA = "fatura"
LEITURAS = "leituras"
PRODUTOS = "produtos"
BANDEIRAS = "bandeiras"
SALDOS_GERACAO = "saldos_geracao"
HISTORICO = "historico"
OUTROS = "outros"


def extrair_dados_unidade_consumidora(pdf, get, format, parent):
    obj = pdf.extract([
            parent,
            format,

            ('nome', f'{get}("76.55, 756.112, 175.614, 764.112")'),
            ('cpf/cnpj', f'{get}("303.3, 590.94, 370.477, 596.44")', lambda match: match.text()[6:]),
            ('logradouro', f'{get}("51.0, 584.94, 134.446, 590.44")'),
            ('bairro', f'{get}("51.0, 578.94, 92.283, 584.44")'),
            ('cidade', f'{get}("51.0, 572.94, 133.489, 578.44")', lambda match: match.text()[10:-5]),
            ('estado', f'{get}("51.0, 572.94, 133.489, 578.44")', lambda match: match.text()[-2:]),
            ('cep', f'{get}("51.0, 572.94, 133.489, 578.44")', lambda match: match.text()[:9]),
            ('classificação', f'{get}("303.3, 578.94, 537.154, 584.44")', lambda match: match.text()[15:]),
        ])
    return obj


def extrair_dados_fatura(pdf, get, format, parent, pdf_pages):
    for page in range(len(pdf_pages.pages)):
        fatura = pdf.extract([
            ('with_parent', f'LTPage[pageid="{page + 1}"]'),
            format,
            ('mês_de_referência', f'{get}("302.95, 540.101, 343.477, 549.101")'),
            ('valor_total', f'{get}("467.191, 540.101, 526.753, 549.101")', format_float),
            ('vencimento', f'{get}("380.017, 540.101, 424.981, 549.101")', format_date)
        ])

    fatura['nota_fiscal'] = pdf.extract([
        parent,
        format,

        ('descricao', f'{get}("133.7, 121.084, 201.884, 127.084")'),
        ('numero', f'{get}("133.7, 112.084, 193.622, 118.084")', lambda match: int(match.text()[3:12])),
        ('serie', f'{get}("133.7, 112.084, 193.622, 118.084")', lambda match: match.text()[-1]),
        ('data_emissao', f'{get}("379.85, 743.329, 465.221, 749.829")', lambda match: match.text()[17:]),
        ('data_apresentacao', f'{get}("379.85, 736.023, 492.564, 743.023")', lambda match: match.text()[22:]),
        ('conta_contrato', f'{get}("379.85, 721.729, 477.877, 728.229")', lambda match: int(match.text()[18:])),
        ('data_leitura_proximo_mes', f'{get}("379.85, 714.423, 487.804, 721.423")', lambda match: match.text()[21:]),
    ])

    fatura['nota_fiscal'] = format_fatura(data=fatura['nota_fiscal'])
    return fatura


def extrair_dados_leituras(pdf, get, parent, format):
    list_leituras = list()
    y0_leitura, y1_leitura = 338.645, 343.645
    altura_leitura = y1_leitura - y0_leitura
    ajuste = 2
    while True:
        obj = pdf.extract([
            parent,
            format,
            ('numero', f'{get}("303.4, {y0_leitura}, 325.575, {y1_leitura}")'),
            ('energia', f'{get}("344.445, {y0_leitura}, 355.55, {y1_leitura}")'),
            ('leitura 1', f'{get}("364.385, {y0_leitura}, 378.25, {y1_leitura}")'),
            ('leitura 2', f'{get}("392.73, {y0_leitura}, 406.595, {y1_leitura}")'),
            ('fator multipl.', f'{get}("422.5, {y0_leitura}, 434.96, {y1_leitura}")'),
            ('consumo_taxa [kWh]', f'{get}("446.635, {y0_leitura}, 463.255, {y1_leitura}")'),
            ('leitura_prox_mes', f'{get}("514.6, {y0_leitura}, 539.535, {y1_leitura}")'),
        ])

        linha_vazia = not any([val != "" for val in obj.values()])
        if linha_vazia:
            break
        y0_leitura = y0_leitura - altura_leitura - ajuste
        y1_leitura = y1_leitura - altura_leitura - ajuste
        list_leituras.append(obj)
    return formata_leitura(list_leituras)


def extrair_dados_produtos(pdf, get, parent, format, pdf_pages):
    dict_prod = dict()
    dict_prod['gerais'] = pdf.extract([
        parent,
        format,
        ('operacao', f'{get}("101.6, 502.895, 141.95, 507.895")', lambda match: int(match.text()[2:])),
        ('cod.', f'{get}("48.95, 502.895, 57.29, 507.895")'),
        ('pis', f'{get}("461.55, 502.895, 475.705, 507.895")'),
        ('cofins', f'{get}("487.35, 502.895, 501.505, 507.895")'),
        ])

    list_produtos = list()
    for page in range(len(pdf_pages.pages)):
        y0_prod, y1_prod = 488.7, 493.2
        altura_prod = y1_prod - y0_prod
        ajuste = 3
        while True:
            obj = pdf.extract([
                ('with_parent', f'LTPage[pageid="{page + 1}"]'),
                format,
                ('codigo', f'{get}("48.15, {y0_prod}, 134.073, {y1_prod}")', lambda texto: texto.text()[:4]),
                ('produto', f'{get}("48.15, {y0_prod}, 134.073, {y1_prod}")', lambda texto: texto.text()[5:]),
                ('mes_ref', f'{get}("184.7, {y0_prod}, 234.084, {y1_prod}")', lambda texto: texto.text()[:6]),
                ('quant_faturada', f'{get}("184.7, {y0_prod}, 234.084, {y1_prod}")'),
                ('unid_med', f'{get}("239.05, {y0_prod}, 248.046, {y1_prod}")'),
                ('tarifa_com_tributos', f'{get}("265.047, {y0_prod}, 289.968, {y1_prod}")'),
                ('valor_total_operacao', f'{get}("303.882, {y0_prod}, 322.566, {y1_prod}")'),
                ('base_calculo_icms', f'{get}("345.0, {y0_prod}, 363.684, {y1_prod}")'),
                ('aliq_icms', f'{get}("377.985, {y0_prod}, 389.208, {y1_prod}")'),
                ('icms R$ R$', f'{get}("399.729, {y0_prod}, 414.687, {y1_prod}")'),
                ('base_calculo_pis/confins', f'{get}("345.0, {y0_prod}, 363.684, {y1_prod}")'),
                ('pis_valor', f'{get}("467.435, {y0_prod}, 479.891, {y1_prod}")'),
                ('cofins_valor', f'{get}("496.325, {y0_prod}, 508.781, {y1_prod}")'),
            ])

            linha_vazia = not any([val != "" for val in obj.values()])
            if linha_vazia:
                break
            y0_prod = y0_prod - altura_prod - ajuste
            y1_prod = y1_prod - altura_prod - ajuste
            list_produtos.append(obj)
    dict_prod['lista'] = formata_produto(list_produtos)
    return dict_prod


def extrair_dados_bandeiras(pdf, get, parent, format):
    dict_obj = dict()
    dict_obj['1'] = pdf.extract([
        parent,
        format,
        ('bandeira', f'{get}("522.4, 487.901, 539.131, 492.401")'),
        ('dias', f'{get}("523.15, 481.25, 538.383, 485.75")', lambda match: match.text()[:-4]),
    ])

    dict_obj['2'] = pdf.extract([
        parent,
        format,
        ('bandeira', f'{get}("517.8, 474.6, 543.747, 479.1")'),
        ('dias', f'{get}("523.15, 467.95, 538.383, 472.45")', lambda match: match.text()[:-4]),
    ])

    dict_obj['3'] = pdf.extract([
        parent,
        format,
        ('bandeira', f'{get}("524.8, 461.3, 536.784, 465.8")'),
        ('dias', f'{get}("523.15, 454.65, 538.383, 459.15")', lambda match: match.text()[:-4]),
    ])
    remover_chaves_vazias(dict_obj['3'])
    len_dict = len(dict_obj['3'])
    if not len_dict:
        dict_obj.pop('3')
    return dict_obj


def extrair_dados_saldos_geracao(pdf, get, parent, format):
    obj = pdf.extract([
        parent,
        format,
        ('saldo_energia_instalacao', f'{get}("51.0, 245.239, 224.393, 250.739")', lambda match: match.text()[45:]),
        ('saldo_expirar_prox_mes', f'{get}("51.0, 237.939, 171.296, 243.439")',lambda match: match.text()[29:]),
        ('participacao_geracao', f'{get}("51.0, 230.639, 127.202, 236.139")', lambda match: match.text()[24:]),
    ])

    # saldo geracao, vazios e dados incorretos.
    data = obj.get('saldo_energia_instalacao')[-3:]
    if data != 'kWh':
        return False
    return obj


def extrair_dados_historico(pdf, get, parent , format):
    list_historico = list()
    y0_historico, y1_historico = 351.995, 356.995
    altura_historico = y1_historico - y0_historico
    ajuste = 2

    while True:
        obj = pdf.extract([
            parent,
            format,
            ('mes', f'{get}("50.25, {y0_historico}, 130.96, {y1_historico}")', lambda texto: texto.text()[:9]),
            ('kWh', f'{get}("156.05, {y0_historico}, 167.15, {y1_historico}")'),
            ('dias', f'{get}("178.645, {y0_historico}, 184.205, {y1_historico}")'),
        ])
        linha_vazia = not any([val != "" for val in obj.values()])
        if linha_vazia:
            break
        y0_historico = y0_historico - altura_historico - ajuste  # 482,2
        y1_historico = y1_historico - altura_historico - ajuste
        list_historico.append(obj)
    return formata_historico(list_historico)


def extrair_outros_dados(pdf, get, parent, format, pdf_pages):
    for page in range(len(pdf_pages.pages)):
        obj = pdf.extract([
                ('with_parent', f'LTPage[pageid="{page + 1}"]'),
                format,
                ('cod_debito_auto', f'{get}("321.45, 117.812, 374.826, 125.812")'),
                ('total_pagar', f'{get}("404.6, 117.812, 459.8, 125.812")'),
                ('data_vencimento', f'{get}("504.9, 117.812, 544.868, 125.812")'),
                ('codigo_barras', f'{get}("99.2, 58.057, 333.205, 66.557")'),
        ])
    obj['debitos_antigos'] = pdf.extract([
            parent,
            format,
            ('vencimento', f'{get}("51.0, 160.539, 118.942, 166.039")', lambda texto: texto.text()[:10]),
            ('valor', f'{get}("51.0, 160.539, 118.942, 166.039")', lambda texto: texto.text()[14:]),
    ])
    return format_outros(obj)


def processar_pdf(fatura):
    pdf = pdfquery.PDFQuery(fatura)
    pdf_name = os.path.basename(fatura)[0:-4]
    pdf_pages = PyPDF2.PdfReader(fatura)

    get = 'LTTextLineHorizontal:overlaps_bbox'
    parent = ('with_parent', 'LTPage[pageid="1"]')
    format = ('with_formatter', 'text')
    schema = {
        UNIDADE_CONSUMIDORA: {},
        FATURA: {},
        LEITURAS: {},
        PRODUTOS: {},
        BANDEIRAS: {},
        SALDOS_GERACAO: {},
        HISTORICO: {},
        OUTROS: {}
    }

    # Extrair os dados
    schema[UNIDADE_CONSUMIDORA] = extrair_dados_unidade_consumidora(pdf, get, format, parent)
    schema[FATURA] = extrair_dados_fatura(pdf, get, format, parent, pdf_pages)
    schema[LEITURAS] = extrair_dados_leituras(pdf, get, parent, format)
    schema[PRODUTOS] = extrair_dados_produtos(pdf, get, parent, format, pdf_pages)
    schema[BANDEIRAS] = extrair_dados_bandeiras(pdf, get, parent, format)
    schema[SALDOS_GERACAO] = extrair_dados_saldos_geracao(pdf, get, format, parent)
    schema[HISTORICO] = extrair_dados_historico(pdf, get, parent, format)
    schema[OUTROS] = extrair_outros_dados(pdf, get, parent, format, pdf_pages)

    json_data = json.dumps(schema, indent=4, ensure_ascii=False, default=date_obj_json)
    with open(f"./json/{pdf_name}.json", "w", encoding='utf-8') as arquivo:
        arquivo.write(json_data)


def main():
    faturas = glob.glob('./faturas/' + "*.pdf")
    for i, fatura in enumerate(faturas):
        print(f'Processando: {i+1}', end='\r')
        processar_pdf(fatura)

    print('')
    print(f'{len(faturas)} faturas processadas.')


if __name__ == "__main__":
    main()
