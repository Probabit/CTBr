# -*- coding: utf-8 -*-
'''
Extração de dados FNDCT - ver 1.0
*************************************

do Site do MCTI - script 03 de agosto 2012
© Mauro Zackiewicz - maurozac@gmail.com

Por favor me comunique se usar estas funções em seu código
Fora isso, valem as regras e a ética do Open Source

'''


# dependencias externas (instalar antes de usar)
from BeautifulSoup import UnicodeDammit
from lxml import html
from lxml.html.clean import Cleaner


def bot_fndct(n): 
    import urllib2

    pre = 'http://sigcti.mct.gov.br/fundos/rel/ctl/ctl.php?act=projeto.visualizar&idp='
    url = pre + str(n)
    
    txdata = None
    txheaders = {}
    req = urllib2.Request(url, txdata, txheaders)
    try:
        resp = urllib2.urlopen(req)
        pagina = resp.read()
        converted = UnicodeDammit(pagina, isHTML=True)
        if not converted.unicode:
            raise UnicodeDecodeError('tentou: '.join(converted.triedEncodings))
        pagina = converted.unicode
        #print pagina
    except IOError, e:
        erros=['erro','erro']
        if hasattr(e, 'reason'):
            erros[0]=e.reason
        elif hasattr(e, 'code'):
            erros[1]=e.code
        e = str(erros[0])+ ' ' + str(erros[1])
        print e
    print n, '... ... ... bot OK'
    return pagina 


def parserFNDCT(pagina):
    cleaner = Cleaner(safe_attrs_only = False)
    pagina = cleaner.clean_html(pagina)
    tree = html.fromstring(pagina)

    for x in tree.iter():
        try:
            if x.tag == 'td' and x.attrib['id'] == 'conteudo':
                util = x.text_content()
        except: pass
            
    util = util.replace('\t','').split('\n')
    #for u in util: print u
    demanda = u''
    valorA, valorB, valorT = u'', u'', u''
    for i in range(len(util)):
        p1 = util[i].find(u'Projeto: ')
        if p1 > -1: projeto = util[i][p1+9:].strip()
        if util[i].strip() == u'Título': titulo = util[i+1]
        if util[i].strip() == u'Demanda': demanda = util[i+1]
        if util[i].strip() == u'Tipo de Demanda': tipo = util[i+1]
        if util[i].strip() == u'Agência': ag = util[i+1]
        if util[i].strip() == u'Fundo': fundo = util[i+1]
        if util[i].strip() == u'Período': periodo = util[i+1]
        if util[i].strip() == u'Coordenador': coord = util[i+1]
        if util[i].strip() == u'Categoria': cat = util[i+1]
        if util[i].strip() == u'Programa do PACTI': pacti = util[i+1]
        p2 = util[i].find(u'Objetivos/Resumo: ')
        if p2 > -1: resumo = util[i][p2+18:].strip()
        p3 = util[i].find(u'Palavras Chaves: ')
        if p3 > -1: tags = util[i][p3+17:].strip()
        if util[i].strip() == u'Membros': membros = util[i+1]
        if util[i].strip() == u'Instituições': orgs = util[i+1]
        if util[i].strip() == u'Valor Contratado:': valorT = util[i+1]
        if util[i].strip() == u'Valor das Bolsas:': valorB = util[i+1]
        if util[i].strip() == u'Valor do Auxílio:': valorA = util[i+1]
        p4 = util[i].find(u'Desembolso do ')
        if p4 > -1: desembolso = util[i+1]

    lmembros = []
    p1 = membros.find('(')
    while p1 > -1:
        mem = membros[:p1]
        p2 = membros.find(')')
        cargo = membros[p1+1:p2]
        membros = membros[p2+1:]
        lmembros.append([mem, cargo, u''])
        p1 = membros.find('(')

    tree2 = html.fromstring(pagina)
    for x in tree2.iter():
        try:
            if x.tag == 'td' and x.attrib['id'] == 'conteudo':
                lcoord = [coord, u'']
                for y1 in x.iter():
                    try:
                        if y1.tag == 'td' and y1.text == coord:
                            lattes = u''
                            for y2 in y1.iter():
                                try:
                                    if y2.tag == 'a':
                                        lattes = y2.attrib['href'][-16:]
                                except:pass
                            lcoord = [coord, lattes]
                    except: pass
                    for i in range(len(lmembros)):
                        try:
                            if y1.tag == 'li' and y1.text == lmembros[i][0]+'('+lmembros[i][1]+')':
                                lattes = u''
                                for y2 in y1.iter():
                                    try:
                                        if y2.tag == 'a':
                                            lattes = y2.attrib['href'][-16:]
                                    except: pass
                                lmembros[i][2] = lattes
                        except: pass
        except: pass
        
    lorgs = []
    p1 = orgs.find(u'(Instituição ')
    while p1 > -1:
        org = orgs[:p1]
        orgs = orgs[p1:]
        p2 = orgs.find(')')
        papel = orgs[1:p2]
        lorgs.append([org, papel])
        orgs = orgs[p2+1:]
        p1 = orgs.find(u'(Instituição ')
    
    from vyger import vtitulo
    fndct = {'projeto': projeto,
             'titulo': vtitulo(titulo),
             'demanda': demanda,
             'tipo': tipo,
             'ag': ag,
             'fundo': fundo,
             'periodo': periodo,
             'coord': lcoord,
             'cat': cat,
             'pacti': pacti,
             'resumo': resumo,
             'tags': tags.split(', '),
             'membros': lmembros,
             'orgs': lorgs,
             'valores': [valorA, valorB, valorT],
             'desembolso':desembolso,
             }
    return fndct

