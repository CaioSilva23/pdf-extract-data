from datetime import datetime
import re


def format_float(str_value):
    try:
        novo_valor = float(str_value.text().replace('.', '').replace(',', '.'))
    except Exception:
        novo_valor = str_value.text()
    return novo_valor


def format_date(date, fora_do_extract=False):
    if not fora_do_extract:
        try:
            new_date = datetime.strptime(date.text(), "%d/%m/%Y")
        except Exception:
            new_date = date
        return new_date

    new_date = datetime.strptime(date, "%d/%m/%Y")
    return new_date


# serializa a data
def date_obj_json(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()


def remover_chaves_vazias(dicionario):
    chaves_vazias = [chave for chave, valor in dicionario.items() if not valor]
    for chave in chaves_vazias:
        dicionario.pop(chave)


def tem_codigo_indesejado(dicionario):
    codigo = dicionario.get("codigo")
    return codigo in ["Tota", "DÉBI"]


def filtro(lista):
    lista_filtrada = [d for d in lista if not tem_codigo_indesejado(d)]
    return lista_filtrada


def formata_historico(data):
    lista_nova = list()
    for historico in data:
        for chave, valor in historico.items():
            try:
                historico[chave] = int(valor)
            except Exception:
                pass
            if chave in ['dias', 'kWh']:
                if len(valor.split()) == 2:
                    historico[chave] = valor.split()[0]
            if chave == 'mes':
                if 'l' in valor:
                    historico['mes'] = historico['mes'].replace('l', '')
        lista_nova.append(historico)
    return lista_nova


def formata_leitura(data):
    lista_nova = list()
    for leitura in data:
        for chave, valor in leitura.items():
            if chave in ['leitura_prox_mes']:
                try:
                    leitura[chave] = format_date(valor, fora_do_extract=True)
                except Exception:
                    pass
        remover_chaves_vazias(leitura)
        lista_nova.append(leitura)
    return lista_nova


def formata_produto(lista_produtos):
    lista_produtos = filtro(lista_produtos)
    nova_lista = list()
    for produto in lista_produtos:
        for chave, valor in produto.items():
            if chave == 'quant_faturada':
                if len(valor.split()) == 2:
                    produto[chave] = valor.split()[1]
                if remove_mes_ano_in_qtd_faturada(valor):
                    produto[chave] = ''
            try:
                if chave in ['codigo', 'produto', 'mes_ref', 'unid_med']:
                    continue
                produto[chave] = float(valor.replace('.', '').replace(',', '.'))
            except Exception:
                pass
        remover_chaves_vazias(dicionario=produto)
        nova_lista.append(produto)
    return nova_lista


def remove_mes_ano_in_qtd_faturada(texto):
    padrao = r"\b[A-Z][A-Za-z]{2}/\d{2}\b"
    resultado = re.sub(padrao, '', texto)
    if resultado == '':
        return True
    return False


def format_outros(data):
    # format debitos antigos
    debitos = data['debitos_antigos']

    remover_chaves_vazias(debitos)
    if len(debitos) == 0:
        debitos = False
    else:
        try:
            vencimento = debitos['vencimento']
            valor = debitos['valor']

            debitos['vencimento'] = format_date(vencimento, fora_do_extract=True)
            debitos['valor'] = float(valor.replace('.', '').replace(',', '.'))
        except Exception:
            pass
    data['debitos_antigos'] = debitos

    # format outros
    for chave, valor in data.items():
        if chave == 'total_pagar':
            try:
                data[chave] = float(valor.replace('.', '').replace(',', '.'))
            except Exception:
                pass
        elif chave == 'data_vencimento':
            try:
                data[chave] = format_date(valor, fora_do_extract=True)
            except Exception:
                pass
    return data
