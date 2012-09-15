# -*- coding: utf-8 -*-
'''
Extração de dados CV-Lattes - ver 1.0
*************************************

Nova estrutura da página, no ar desde 23 de julho 2012
© Mauro Zackiewicz - maurozac@probabit.com.br

Por favor comunique o autor se usar estas funções em seu código
Fora isso, valem as regras e a ética do Open Source
    
'''
cv = '4727357182510680'
#cv = '2136191211439968'
#cv = '9437784541909444'
#cv = '1388529283382853'

ANO_ATUAL = 2012

# dependencias externas (instalar antes de usar)
from BeautifulSoup import UnicodeDammit
from lxml import html
from lxml.html.clean import Cleaner


def bot_lattes(cv): 
    import urllib2
    import time

    pre10 = 'http://buscatextual.cnpq.br/buscatextual/visualizacv.do?metodo=apresentar&id='
    pre16 = 'http://lattes.cnpq.br/'
    if len(cv) == 10:
        url = pre10 + str(cv)
    if len(cv) == 16:
        url = pre16 + str(cv)

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
        print '... OK: ', cv
        #print pagina
    except IOError, e:
        erros=['erro','erro']
        if hasattr(e, 'reason'):
            erros[0]=e.reason
        elif hasattr(e, 'code'):
            erros[1]=e.code
        e = str(erros[0])+ ' ' + str(erros[1])
        print e
    print '... ... ... bot OK'
    time.sleep(0.4) # para não sobrecarregar o servidor do CNPq
    return pagina 


def parserLattes(pagina):
    cleaner = Cleaner(safe_attrs_only = False)
    pagina = cleaner.clean_html(pagina)
    tree = html.fromstring(pagina)

    # 1. arrumações necessárias
    # ****************************************

    arruma = tree
    for x in arruma.iter():
        try:
            if x.tag == 'br' and x.attrib['class'] == 'clear':
                x.text = ';; '
        except: pass
        try:
            if x.tag == 'span' and x.attrib['class'] == 'informacao-artigo':
                t = x.text
                x.text = t + ' ; '
        except: pass     
        try:
            if x.tag == 'div' and x.text == u'Currículo não encontrado':
                return None
        except: pass
        

    # 2. extrai do corpo os trechos
    # *****************************
    
    foto = u''
    nome = u''
    cnpq = u''
    falecido = u''
    infoautor = []
    resumo = u''
    identifica = []
    endereco = u''
    formacao = []
    profissional = []
    projetos = []
    anoAnt = ';;'
    areas = []
    artigos = []
    coautores = []
    producao = []
    orientados = []

    for x in tree.iter():
        # dados gerais
        try:
            if x.tag == 'img' and x.attrib['class'] == 'foto':
                foto = x.attrib['src']
        except: pass
        try:
            if x.tag == 'h2' and x.attrib['class'] == 'nome':
                nome = x.text.strip()
                for y1 in x.iter():
                    try:
                        if y1.tag == 'img' and y1.attrib['src'] == "/buscatextual/images/falecido-32x32.gif":
                            falecido = y1.getnext().text.strip()
                    except: pass
                    try:
                        if y1.tag == 'span' and falecido == u'':
                            cnpq = y1.text.strip()
                    except: pass
        except: pass
        try:
            if x.tag == 'ul' and x.attrib['class'] == 'informacoes-autor':
                for y1 in x.iter():
                    try:
                        if y1.tag == 'li':                           
                            infoautor.append(y1.text_content().strip())
                    except: pass
        except: pass
        try:
            if x.tag == 'p' and x.attrib['class'] == 'resumo':
                resumo = x.text_content().strip()
        except: pass
        try:
            if x.tag == 'a' and x.attrib['name'] == 'Identificacao':
                y = x.getnext().getnext()
                for y1 in y.iter():
                    try:
                        if y1.tag == 'div' and y1.attrib['class'] == 'layout-cell-pad-5 text-align-right':
                            campo = y1.text_content().strip()
                    except: pass
                    try:
                        if y1.tag == 'div' and y1.attrib['class'] == 'layout-cell layout-cell-9':
                            identificacao = y1.text_content().strip()
                            identifica.append((campo, identificacao))
                    except: pass
        except: pass
        try:
            if x.tag == 'a' and x.attrib['name'] == 'Endereco':
                y = x.getnext().getnext()
                for y1 in y.iter():
                    try:
                        if y1.tag == 'div' and y1.attrib['class'] == 'layout-cell-pad-5':
                            endereco = y1.text_content().strip()
                    except: pass
        except: pass
        try:
            if x.tag == 'a' and x.attrib['name'] == 'FormacaoAcademicaTitulacao':
                y = x.getparent()
                for y1 in y.iter():
                    capes = u''
                    orientador = u''
                    try:
                        if y1.tag == 'div' and y1.attrib['class'] == 'layout-cell layout-cell-3 text-align-right':
                            ano = y1.text_content().strip()
                            z = y1.getnext()
                            curso = z.text_content().strip()
                            for z1 in z.iter():
                                try:
                                    if z1.tag == 'span' and z1.attrib['class'] == 'ajaxCAPES':
                                        capes = z1.attrib['data-param']
                                except: pass
                                try:
                                    if z1.tag == 'a' and z1.attrib['class'] == 'icone-lattes':
                                        orientador = z1.attrib['href']
                                except: pass
                            formacao.append((ano, curso, capes, orientador))
                    except: pass
        except: pass
        # PULEI: formacao complementar
        # Atuacao Profissional
        try:
            if x.tag == 'a' and x.attrib['name'] == 'AtuacaoProfissional':
                y = x.getnext().getnext()
                '''
                inst: nome da instituição
                k1: subtitulo
                k2: anos
                desc: descrição

                cada = [(inst,conteudo)]
                conteudo = [(k1, itens)]   
                itens = [(k2, desc)]
                
                portanto:
                    profissional = [(inst,[(k1,[(k2, desc),]),]),]
                '''
                for y1 in y.iter():
                    try:
                        if y1.tag == 'div' and y1.attrib['class'] == 'inst_back':
                            inst = y1.text_content().strip()
                            profissional.append((inst,[]))
                    except: pass
                    try:
                        if y1.tag == 'div' and y1.attrib['class'] == 'layout-cell layout-cell-3 text-align-right subtit-1':
                            k1 = y1.text_content().strip()
                            a = profissional.pop()
                            a[1].append((k1,[]))
                            profissional.append(a)
                    except: pass       
                    try:
                        if y1.tag == 'div' and y1.attrib['class'] == 'layout-cell layout-cell-3 text-align-right':
                            k2 = y1.text_content().strip()
                            if k2 == ';;':
                                k2 = k2Ant
                            else: k2Ant = k2
                    except: pass
                    try:
                        if y1.tag == 'div' and y1.attrib['class'] == 'layout-cell layout-cell-9':
                            if y1.getprevious().attrib['class'] == 'layout-cell layout-cell-3 text-align-right':
                                desc = y1.text_content().strip()
                                a = profissional.pop()
                                b = a[1].pop()
                                b[1].append((k2, desc))
                                a[1].append(b)
                                profissional.append(a)
                            else: pass                     
                    except: pass
        except: pass
        # PULEI: linhas de pesquisa
        # Projetos de pesquisa
        try:
            if x.tag == 'a' and x.attrib['name'] == 'ProjetosPesquisa':
                y = x.getnext().getnext()
                for y1 in y.iter():
                    try:
                        if y1.tag == 'div' and y1.attrib['class'] == 'layout-cell layout-cell-3 text-align-right':
                            ano = y1.text_content().strip()
                            if ano == ';;': ano = anoAnt
                            else: anoAnt = ano
                    except: pass
                    try:
                        if y1.tag == 'div' and y1.attrib['class'] == 'layout-cell layout-cell-9':
                            w = y1.getprevious().getprevious()
                            if w.tag == 'a':
                                titulo = y1.text_content().strip()
                            elif w.tag == 'div':
                                abstract = y1.text_content().strip()
                                projetos.append((ano, titulo, abstract))
                    except: pass            
        except: pass
        # PULEI: membro de corpo editorial
        # PULEI: revisor de periódico
        # Areas de atuacao
        try:
            if x.tag == 'a' and x.attrib['name'] == 'AreasAtuacao':
                y = x.getnext().getnext()
                for y1 in y.iter():
                    try:
                        if y1.tag == 'div' and y1.attrib['class'] == 'layout-cell layout-cell-3 text-align-right':
                            n = y1.text_content().strip()
                    except: pass
                    try:
                        if y1.tag == 'div' and y1.attrib['class'] == 'layout-cell layout-cell-9':
                            area = y1.text_content().strip()
                            areas.append((n, area))
                    except: pass
        except: pass
        # PULEI: idioma
        # PULEI: prêmios
        # Producao Cientifica
        try:
            if x.tag == 'a' and x.attrib['name'] == 'ProducoesCientificas':
                y = x.getnext().getnext()
                for y1 in y.iter():
                    try:
                        if y1.tag == 'a' and y1.attrib['class'] == 'tooltip':
                            parceiro = y1.text.strip()
                            id16 = y1.attrib['href']
                            coautores.append((parceiro, id16))
                    except: pass
                    # artigos completos:
                    try:
                        if y1.tag == 'div' and y1.attrib['class'] == 'artigo-completo':
                            for z1 in y1.iter():
                                try:
                                    if z1.tag == 'div' and z1.attrib['class'] == 'layout-cell-pad-5':
                                        artigo = z1.text_content().strip()
                                        ano = u''
                                        doi = u''
                                        issn = u''
                                        for z2 in z1.iter():
                                            try:
                                                if z2.tag == 'span' and z2.attrib['data-tipo-ordenacao'] == 'ano':
                                                    ano = z2.text.strip()
                                            except: pass
                                            try:
                                                if z2.tag == 'a' and z2.attrib['class'] == 'icone-producao icone-doi':
                                                    doi = z2.attrib['href']
                                            except: pass
                                            try:
                                                if z2.tag == 'img' and z2.attrib['class'] == 'ajaxJCR':
                                                    issn = z2.attrib['data-issn']
                                            except: pass
                                        artigos.append((artigo, ano, doi, issn))
                                except: pass
                    except: pass
                    # todos as demais bibliograficas
                    try:
                        if y1.tag == 'div' and y1.attrib['class'] == 'cita-artigos':
                            tipo = y1.text_content().strip()
                    except: pass
                    try:
                        if y1.tag == 'div' and y1.attrib['class'] == 'layout-cell layout-cell-11':
                            produto = y1.text_content().strip()
                            producao.append((tipo, produto))
                    except: pass 
                    # producao tecnica
                    try:
                        if y1.tag == 'a' and y1.attrib['name'] == 'ProducaoTecnica':
                            z = y1.getnext().getnext()
                            for z1 in z.iter():
                                try:
                                    if z1.tag == 'div' and z1.attrib['class'] == 'inst_back':
                                        tipo = z1.text_content().strip()                   
                                except: pass
                    except: pass
                    # artística
                    try:
                        if y1.tag == 'a' and y1.attrib['name'] == 'ProducaoArtisticaCultural':
                            z = y1.getnext().getnext()
                            for z1 in z.iter():
                                try:
                                    if z1.tag == 'div' and z1.attrib['class'] == 'inst_back':
                                        tipo = z1.text_content().strip()
                                except: pass
                    except: pass                       
        except: pass
        # PULEI bancas
        # PULEI eventos
        # Orientados
        try:
            if x.tag == 'a' and x.attrib['name'] == 'Orientacoes':
                y = x.getnext().getnext()
                for y1 in y.iter():
                    try:
                        if y1.tag == 'div' and y1.attrib['class'] == 'inst_back':
                            tipo1 = y1.text_content().strip()
                    except: pass
                    try:
                        if y1.tag == 'div' and y1.attrib['class'] == 'cita-artigos':
                            tipo2 = y1.text_content().strip()
                    except: pass
                    try:
                        if y1.tag == 'div' and y1.attrib['class'] == 'layout-cell layout-cell-11':
                            trabalho = y1.text_content().strip()
                            estudante = u''
                            for z1 in y1.iter():
                                try:
                                    if z1.tag == 'a' and z1.attrib['class'] == 'icone-lattes':
                                        estudante = z1.attrib['href']
                                except: pass     
                            orientados.append((tipo1, tipo2, trabalho, estudante))
                    except: pass
        except: pass


    #print '**********************************'
    #print nome, cnpq
    #print resumo
    #print foto
    #print infoautor
    #print identifica
    #print endereco
    #print areas
    #print formacao
    #print orientados
    #print profissional
    #print projetos
    #print artigos
    #print producao
    #print coautores


    # 3. extrai campos semi-estruturados e monta dict de saída
    # ********************************************************

    tamanho = len(pagina)
    
    id10 = foto[-10:]
    #print id10

    id16 = infoautor[0][-16:]
    #print id16

    try: ultima_atualizacao = infoautor[1][-10:]
    except:
        if falecido != u'': ultima_atualizacao = falecido[-10:]
        else: ultima_atualizacao = '00/00/0000'         
    #print ultima_atualizacao
        
    resumo = resumo.replace(u'(Texto informado pelo autor)', u'').strip()
    resumo = resumo.replace(u'(Texto gerado automaticamente pela aplicação CVLattes)', u'').strip()
    resumo = resumo.replace(u'(Texto gerado automaticamente pelo Sistema Lattes)', u'').strip()
    #print resumo
    
    var_nome = unicode(identifica[1][1]).split(';')
    #print var_nome

    if len(identifica) > 2: sexo = identifica[2][1]
    else: sexo = u''
    #print sexo
    
    endereco_campos = endereco.split(';; ')
    if len(endereco_campos) < 4: endereco_campos = [u'', u'', u'', u'']
    endereco_str = endereco.replace(';; ',' ')
    url_ende = endereco_str.find('URL da Homepage: ')
    endereco = endereco_str[:url_ende].strip()
    url_ende = endereco_str[url_ende + 17:].strip()

    dados_endereco = {'endereco':endereco,
                      'campos':endereco_campos,
                      'url':url_ende}
    #print dados_endereco
    
    dados_formacao = []
    for f in formacao:
        ano_i = 0
        ano_f = ANO_ATUAL
        if len(f[0].strip()) == 4: ano_i = f[0].strip()
        else:
            p0 = f[0].find('-')
            if p0 > -1:
                anos = f[0].split('-')
                if len(anos[0].strip()) and anos[0].strip().isdigit() == 4: ano_i = int(anos[0].strip())
                if len(anos[1].strip()) and anos[1].strip().isdigit() == 4: ano_f = int(anos[1].strip())
        detalhes = f[1].split(';; ')
        curso = detalhes[0][:detalhes[0].rfind('.')]
        if len(detalhes) > 1: local = detalhes[1][:detalhes[1].rfind('.')]
        else: local = u''
        areaf = []
        titulo = u''
        ano_ob = 0
        bolsa = u''
        tags = u''
        setor = u''
        orientador = u''
        for d in detalhes:
            p1 = d.find(u'Título: ')
            if p1 > -1:
                titulo = d[p1+8:]
                p11 = titulo.find(u'Ano de obtenção: ')
                if p11 > -1:
                    t = titulo.split(u'Ano de obtenção: ')
                    titulo = t[0]
                    ano_ob = t[1].replace('.','')
                p11b = titulo.find(u'Ano de Obtenção: ')
                if p11b > -1:
                    t = titulo.split(u'Ano de Obtenção: ')
                    titulo = t[0]
                    ano_ob = t[1].replace('.','')
                p12 = titulo.find(u'Orientador: ')
                if p12 > -1:
                    t = titulo.split(u'Orientador: ')
                    titulo = t[0]
                    orientador = t[1]
            p2 = d.find(u'Bolsista do(a): ')
            if p2 > -1: bolsa = d[p2+14:].replace('.','').strip()
            p3 = d.find(u'Palavras-chave: ')
            if p3 > -1: tags = d[p3+16:].strip()
            p4 = d.find(u'Grande Área: ')
            if p4 > -1: areaf.append(d[p4:].strip())
            p5 = d.find(u'Grande área: ')
            if p5 > -1: areaf.append(d[p5:].strip()) 
            p6 = d.find(u'Setores de atividade: ')
            if p6 > -1: setor = d[p6+22:]
            p7 = d.find(u'Orientador: ')
            if p7 > -1: orientador = d[p7+12:-1]
            p8 = d.find(u'Ano de finalização: ')
            if p8 > -1: ano_ob = d[p8+20:].replace('.','')
        id_curso = u''
        if f[2] != u'':
            id_curso = (f[2][f[2].find('=')+1:f[2].rfind('&')], f[2][f[2].rfind('=')+1:])
        id_orientador = u''
        if f[3] != u'':
            id_orientador = f[3][-16:]
                
        extrato = {'ano_inicio':ano_i,
                   'ano_final':ano_f,
                   'curso':curso,
                   'id_curso':id_curso,
                   'local':local,
                   'areaf':areaf,
                   'titulo':titulo,
                   'ano_ob':ano_ob,
                   'bolsa':bolsa,
                   'tags':tags,
                   'setor':setor,
                   'orientador':orientador,
                   'id_orientador':id_orientador}
        dados_formacao.append(extrato)
    #print dados_formacao

    vinculo_profissional = []
    vinculo_projetos = []
    for p in profissional:
        a1 = p[0].rfind(', ')
        instituicao = p[0][:a1]
        pais = p[0][a1+2:-1]
        for q in p[1]:
            if q[0] == u'Vínculo institucional':
                ano_i = 0
                ano_f = 0
                obs = u''
                for r in q[1]:
                    if r[0] == u'Outras informações':
                        obs = r[1]
                        continue
                    if r[0].find('-') > -1: 
                        anos = r[0].split('-')
                        if len(anos[0]) >= 4:
                            ano_i = anos[0].strip()
                            ano_i = int(ano_i[-4:])      
                        if len(anos[1]) >= 4:
                            ano_f = anos[1].strip()
                            ano_f = ano_f[-4:]
                            if ano_f == u'tual': ano_f = ANO_ATUAL
                extrato = {'instituicao':instituicao,
                           'pais':pais,
                           'ano_i':ano_i,
                           'ano_f':int(ano_f),
                           'obs':obs}
                vinculo_profissional.append(extrato)

            if q[0] == u'Atividades':
                ano_i = 0
                ano_f = 0
                local = u''
                proj = []
                for i in range(len(q[1])):
                    if q[1][i][1].find(u'Atividades de Participação em Projeto') > -1:
                        a2 = q[1][i][1].find(', ')
                        local = q[1][i][1][a2+2:-1]
                        try:
                            proj = q[1][i+1][1].split(';;')
                            tira = proj.pop(0)
                        except: pass
                        if len(proj) > 0:
                            for j in range(len(proj)):
                                proj[j] = proj[j].strip()
                                if len(proj[j]) == 0: tira = proj.pop(j)              
                        if q[1][i][0].find('-') > -1: 
                            anos = q[1][i][0].split('-')
                            if len(anos[0]) >= 4:
                                ano_i = anos[0].strip()
                                ano_i = int(ano_i[-4:])      
                            if len(anos[1]) >= 4:
                                ano_f = anos[1].strip()
                                ano_f = ano_f[-4:]
                                if ano_f == u'tual': ano_f = ANO_ATUAL
                                if str(ano_f).isdigit(): ano_f = int(ano_f)
                                else: ano_f = ano_i
                        extrato = {'instituicao':instituicao,
                                   'pais':pais,
                                   'ano_i':ano_i,
                                   'ano_f':ano_f,
                                   'local':local,
                                   'projetos':proj}
                        vinculo_projetos.append(extrato)              
    #print vinculo_profissional
    #print vinculo_projetos

    dados_projetos = []
    for p in projetos:
        ano_i = 0
        ano_f = 0
        if p[0].find('-') > -1:
            anos = p[0].split('-')
            if len(anos[0]) >= 4:
                ano_i = anos[0].strip()
                ano_i = int(ano_i[-4:])      
            if len(anos[1]) >= 4:
                ano_f = anos[1].strip()
                ano_f = ano_f[-4:]
                if ano_f == u'tual': ano_f = ANO_ATUAL
        titulo = p[1].replace(';;','').strip()
        detalhes = p[2].split(';;')
        descricao = u''
        situacao = u''
        natureza = u''
        integrantes = []
        coordenador = []
        financiador = []
        parceiro = []
        for d in detalhes:     
            p1 = d.find(u'Descrição: ')
            if p1 > -1: descricao = d[p1+11:]
            p2 = d.find(u'Situação: ')
            p3 = d.find(u'Natureza: ')
            if p2 > -1:
                situacao = d[p2+10:]
                if p3 > -1: situacao = d[p2+10:p3-2]
            if p3 > -1: natureza = d[p3+10:-2]  
            p4 = d.find(u'Integrantes: ')
            if p4 > -1:
                integra = d[p4+13:-1].split(' / ')
                for i in integra:
                    componente = i.split(' - ')
                    if len(componente) > 1:
                        if componente[1] == u'Integrante': integrantes.append(componente[0])
                        if componente[1] == u'Integrante.': integrantes.append(componente[0])
                        if componente[1] == u'Coordenador': coordenador.append(componente[0])
                        if componente[1] == u'Coordenador.': coordenador.append(componente[0])
            p5 = d.find(u'Financiador(es): ')
            if p5 > -1:
                financia = d[p5+17:-1].split(' / ')
                for f in financia:
                    fonte = f.split(' - ')
                    if len(fonte) > 1:
                        fonte[1] = fonte[1].replace(u'\t',u'')
                        fonte[1] = fonte[1].replace(u'\n',u' ')
                        if fonte[1] == u'Auxílio financeiro': financiador.append(fonte[0])
                        if fonte[1] == u'Auxílio financeiro.': financiador.append(fonte[0])
                        if fonte[1] == u'Cooperação': parceiro.append(fonte[0])
                        if fonte[1] == u'Cooperação.': parceiro.append(fonte[0])
                    # 'Bolsa'
                    # 'Remuneração'
                    # 'Outra'
        extrato = {'ano_i':ano_i,
                   'ano_f':int(ano_f),
                   'titulo':titulo,
                   'descricao':descricao,
                   'situacao':situacao,
                   'natureza':natureza,
                   'integrantes':integrantes,
                   'coordenador':coordenador,
                   'financiador':financiador,
                   'parceiro':parceiro}
        dados_projetos.append(extrato)
    #print dados_projetos
        
    dados_areas = []
    for a in areas:
        n = a[0][:-1]
        itens = a[1].split('/')
        grande_area = u''
        area = u''
        subarea = u''
        especialidade = u''
        for i in itens:
            p1 = i.find(u'Grande área: ')
            if p1 > -1: grande_area = i[p1+13:].replace('.','').replace(';;','').strip()
            p1v = i.find(u'Grande Área: ')
            if p1v > -1: grande_area = i[p1v+13:].replace('.','').replace(';;','').strip()
            p2 = i.find(u'Área: ')
            if p2 > -1: area = i[p2+6:].replace('.','').replace(';;','').strip()
            p3 = i.find(u'Subárea: ')
            if p3 > -1: subarea = i[p3+9:].replace('.','').replace(';;','').strip()
            p4 = i.find(u'Especialidade: ')
            if p4 > -1: especialidade = i[p4+15:].replace('.','').replace(';;','').strip()
        extrato = {'n':int(n),
                 'grande_area':grande_area,
                 'area':area,
                 'subarea':subarea,
                 'especialidade':especialidade}
        dados_areas.append(extrato)  
    #print dados_areas

    dados_artigos = []
    for a in artigos:
        ano = a[1].replace(';','').strip()
        doi = a[2]
        issn = a[3]
        p1 = a[0].find(a[1])
        p2 = a[0].rfind(ano)
        if ano.isdigit(): ano = int(ano)
        else: ano = 0
        detalhes = a[0][p1+6:p2-2].strip()
        p3 = detalhes.rfind(' p. ')
        p4 = detalhes.rfind(' v. ')
        p5 = detalhes.rfind(' n. ')
        corte = [len(detalhes)]
        if p3 > -1: corte.append(p3)
        if p4 > -1: corte.append(p4)
        if p5 > -1: corte.append(p5)
        corte.sort()
        detalhes = detalhes[:corte[0]]
        p6 = detalhes.rfind('. ')
        revista = detalhes[p6+1:].replace(',','').strip()
        detalhes = detalhes[:p6]
        autor_e_tit = detalhes
        extrato = {'autor_e_tit':autor_e_tit,
                   'ano':ano,
                   'doi':doi,
                   'issn':issn,
                   'revista':revista}
        dados_artigos.append(extrato)
    #print dados_artigos
        
    dados_producao = []
    # depois

    turma_orientados = []
    # poderia tentar extrair o ano, mas em geral deve ser da pagina do orientado
    for o in orientados:
        pupilo = o[2][:o[2].find('.')].strip()
        pid16 = o[3][-16:]
        grau = o[1]
        p1 = grau.find('mestrado')
        tipo = u''
        if p1 > -1: tipo = u'mestrado'
        p2 = grau.find('doutorado')
        if p2 > -1: tipo = u'doutorado'   
        if tipo != u'':
            extrato = {'orientador':nome,
                       'orientado':pupilo,
                       'id16':pid16,
                       'tipo':tipo}
            turma_orientados.append(extrato)
    #print turma_orientados
                   
    colaboradores = []
    for c in coautores:
        colaboradores.append(c[1][-16:])
    #print colaboradores

    cvdict = {'nome':nome,
              'sexo':sexo,
              'cnpq':cnpq,
              'id10':id10,
              'id16':id16,
              'ulti':ultima_atualizacao,
              'resu':resumo,
              'vnome':var_nome, 
              'ende':dados_endereco,
              'forma':dados_formacao,
              'vprof':vinculo_profissional,
              'vproj':vinculo_projetos,
              'proj':dados_projetos,
              'area':dados_areas,
              'artg':dados_artigos,
              'alunos':turma_orientados,
              'colabora':colaboradores,
              }
        
    return cvdict

#pagina = bot_lattes(cv)
#parserLattes(pagina)
