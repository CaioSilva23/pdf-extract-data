from datetime import datetime
import re


def format_float(valor, fora_extract=False):
    if not fora_extract:
        valor = valor.text()
    try:
        return float(valor.replace('.', '').replace(',', '.'))
    except ValueError:
        return valor


def formata_produto(lista_produtos):
    lista_produtos_filtrados = filtro(lista_produtos)

    def formatar_quant_faturada(valor):
        if len(valor.split()) == 2:
            return valor.split()[1]
        elif remove_mes_ano_in_qtd_faturada(valor):
            return ''
        return valor

    nova_lista = [
        {
            chave: format_float(valor, fora_extract=True) if chave not in ['codigo', 'produto', 'mes_ref', 'unid_med']
            else valor
            for chave, valor in produto.items()
        }
        for produto in lista_produtos_filtrados
    ]

    for produto in nova_lista:
        produto['quant_faturada'] = formatar_quant_faturada(produto['quant_faturada'])
        remover_chaves_vazias(produto)
    return nova_lista


def remove_mes_ano_in_qtd_faturada(texto):
    padrao = r"\b[A-Z][A-Za-z]{2}/\d{2}\b"
    resultado = re.sub(padrao, '', texto)
    if resultado == '':
        return True
    return False


def format_date(date, fora_do_extract=False):
    if not fora_do_extract:
        date = date.text()
    try:
        return datetime.strptime(date, "%d/%m/%Y")
    except ValueError:
        return date


# serializa a data
def date_obj_json(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()


def remover_chaves_vazias(dicionario):
    chaves_vazias = [chave for chave, valor in dicionario.items() if not valor]
    for chave in chaves_vazias:
        dicionario.pop(chave)


def filtro(lista):
    def tem_codigo_indesejado(dicionario):
        codigo = dicionario.get("codigo")
        return codigo in ["Tota", "DÉBI", "CRÉD"]

    lista_filtrada = [d for d in lista if not tem_codigo_indesejado(d)]
    return lista_filtrada


def formata_historico(data):
    for historico in data:
        for chave, valor in historico.items():
            try:
                historico[chave] = int(valor)
            except ValueError:
                pass

            if chave in ['dias', 'kWh']:
                partes = valor.split()
                if len(partes) == 2:
                    historico[chave] = partes[0]

            if chave == 'mes':
                historico['mes'] = valor.replace('l', '')
    return data


def formata_leitura(data):
    lista_nova = []
    for leitura in data:
        for chave, valor in leitura.items():
            if chave == 'leitura_prox_mes':
                try:
                    leitura[chave] = format_date(valor, fora_do_extract=True)
                except ValueError:
                    leitura[chave] = valor

        leitura = {chave: valor for chave, valor in leitura.items() if valor}
        lista_nova.append(leitura)
    return lista_nova


def format_outros(data):
    debitos_antigos = data['debitos_antigos']
    remover_chaves_vazias(debitos_antigos)

    if debitos_antigos:
        try:
            vencimento = debitos_antigos.get('vencimento')
            valor = debitos_antigos.get('valor')

            debitos_antigos['vencimento'] = format_date(vencimento, fora_do_extract=True)
            debitos_antigos['valor'] = format_float(valor=valor, fora_extract=True)
        except KeyError:
            pass
    else:
        debitos_antigos = False
    data['debitos_antigos'] = debitos_antigos

    # Formatar outros campos
    try:
        total_pagar = data.get('total_pagar')
        data_vencimento = data.get('data_vencimento')

        data['total_pagar'] = format_float(valor=total_pagar, fora_extract=True)
        data['data_vencimento'] = format_date(data_vencimento, fora_do_extract=True)
    except KeyError:
        pass
    return data


def format_fatura(data):
    for chave, valor in data.items():
        str = chave[0:4]
        if str == 'data':
            data[chave] = format_date(date=valor, fora_do_extract=True)
    return data