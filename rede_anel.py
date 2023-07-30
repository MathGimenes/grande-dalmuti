import socket , os, random

from itertools import cycle
from time import sleep

# Marcadores de inicio e fim
inicio = bytes([int('11111111', 2)])
fim = bytes([int('10000001', 2)])

# Tipos
tipo_bastao = bytes([int('00000000', 2)])
tipo_ping = bytes([int('00000001', 2)])
tipo_carteado = bytes([int('00000010', 2)])
tipo_escolha = bytes([int('00000011', 2)])
tipo_jogar = bytes([int('00000100', 2)])
tipo_passar = bytes([int('00000101', 2)])
tipo_clear_descarte = bytes([int('00000110', 2)])
tipo_acabou_baralho = bytes([int('00000111', 2)])
tipo_fim_baralho = bytes([int('00001000', 2)])

byte_vazio = bytes([int('00000000', 2)])

# Recebe uma string lida do arquivo de configuracao que contem o ip,
# e retorna um bytearray que o contem
def codifica_ip(meu_ip: str) -> bytearray:
    campos = meu_ip.split(".")
    ip_codificado = bytearray()
    for campo in campos:
        ip_codificado.append(int(campo.encode(encoding="ascii")))
    
    return ip_codificado

# Recebe o ip,  a mensagem, e a posicao do jogador atual, escreve os bits de recebimento,
# e retorna um bool indicando se a mensagem foi enviada pelo jogador, o tipo de mensagem
# e a jogada
def decodifica_mensagem(meu_ip: bytearray, mensagem: bytearray, minha_pos: int):
    # verificando o marcador de inicio
    if mensagem[0] != inicio[0]:
        raise Exception("Inicio de mensagem possivelmente corrompido")
    
    # Verificando se a mensagem foi enviado pelo jogador que chamou a funcao
    eh_minha = False
    ip_origem = bytearray([mensagem[1], mensagem[2], mensagem[3], mensagem[4]])
    if ip_origem == meu_ip:
        eh_minha = True
    
    # Armazenando o tipo
    tipo = bytearray([mensagem[5]])
    
    #Armazenando a jogada
    jogada = bytearray([mensagem[6]])

    # marcando os bits de recebimento
    mensagem[7]|= 2 **( minha_pos)
    
    #verificando marcador de final
    if mensagem[8] != fim[0]:
        raise Exception("Fim de mensagem possivelmente corrompido")

    return eh_minha, tipo, jogada

# Gera um baralho de the great dalmuti embaralhado e o retorna em uma lista de inteiro
def gera_baralho() -> list[int]:
    baralho = list(range(1,13)) + list(range(2,13)) + list(range(3,13)) + list(range(4,13)) + list(range(5,13)) + list(range(6,13)) \
    + list(range(7,13)) + list(range(8,13)) + list(range(9,13)) + list(range(10,13)) + list(range(11,13)) + list(range(12,13)) 
    baralho += [13,13]
    random.shuffle(baralho)
    
    return baralho

# Recebe o baralho a ser impresso, uma string com o cabecalho que sera impresso antes,
# e o imprime na tela
def imprime_baralho(meu_baralho: list, cabecalho:str):
    print(cabecalho)
    baralho = ""
    for carta in meu_baralho:
        baralho += str(carta) + " "
    print(baralho + "\n")

# Recebe uma lista com a mao do jogador, uma lista com as cartas descartadas,
# e imprime a mensagem de espera na tela
def imprime_espere_sua_vez(meu_baralho:list[int], monte_descarte:list[int]):
    os.system('clear')
    print("Espere a sua vez:")
    imprime_baralho(monte_descarte, "Monte descarte:")
    imprime_baralho(meu_baralho, "Suas cartas")

# Recebe um bytearray que contem a jogada,
# e retorna o jogador. 
def pegar_jogador(jogada: bytearray):
    get_jogador = bytearray([int('00000011',2)])
    jogador = jogada[0] & get_jogador[0]
    return jogador

# Funcao que verifica se o baralho esta vazio,
# retorna um bool
def baralho_vazio(meu_baralho:list) -> bool:
    if len(meu_baralho) == 0:
        return True
    return False

# Funcao que usa uma lista circular para determinar o proximo jogador    
def get_prox_jogador(minha_pos:int, jogadores:int, nova_ordem=[], reverso=False) -> int:
    temp = list(range(jogadores))
    if reverso:
        temp.reverse()
    for i in nova_ordem:
        temp.remove(i)
    players = cycle(temp)
    for player in players:
        if player == minha_pos:
            break

    return next(players)

# Recebe a lista de jogadores que contem a ordem da mao atual, os ips e portas dos jogadores,
# uma lista com a ordem da nova mao, e gera uma lista com a nova ordem, os ips e portas dos jogadores,
# e a retorna
def gerar_cfg(lista_jogadores:list, nova_ordem:list[int], jogadores:int) -> list:
    # Determinando e adicionando o ultimo jogador
    for i in range(jogadores):
        if nova_ordem.count(i) == 0:
            nova_ordem.append(i)
    
    nova_lista = list()
    #nova ordem com uma lista com a nova ordem, que nada mais e que os indices dass listas de jogadores
    for i in range(jogadores):
        # em lista_jogadores os membros sao tuplas, transformando-os em lista
        # para que possam ser alterados
        nova_lista.append(list(lista_jogadores[nova_ordem[i]]))
        nova_lista[i][0] = i

    return nova_lista

# Recebe uma lista que contem a nova ordem dos jogadores, o numero de jogadores,
# e grava no diretorio do script a configuracao da proxima mao
def gravar_cfg(nova_lista:list, jogadores:int):
    with open('cfg.txt', 'w') as f:
        #cabecalho
        f.write("%d;1\n" % jogadores)
        #formatando a saida para que fique no padrao do arquivo de configuracao
        for i in range(jogadores):
            f.write("%d;%s;%d\n" % (nova_lista[i][0] + 1, nova_lista[i][1], nova_lista[i][2]))

# funcao que identifica qual o tipo de mensagem recebida, e a encaminha para a funcao que a ira tratar
def mensagem_handler(meu_socket: socket.socket, mensagem: bytearray, tipo:bytearray, jogada:bytearray, lista_jogadores:list, monte_descarte:list , meu_baralho:list[int],
                    nova_ordem:list[int], ip_porta_saida:tuple,minha_pos:int, bastao:list, jogadores:int):
    # verificando se o jogador esta ou nao na lista de players que ja terminaram
    tem_cartas = nova_ordem.count(minha_pos) == 0
    if tipo[0] == tipo_ping[0]:
        print("Ping recebido, passando adiante...")
        meu_socket.sendto(mensagem, ip_porta_saida)
        return 0
    elif tipo[0] == tipo_carteado[0]:
        carteado_recebendo(meu_socket, mensagem, jogada, meu_baralho, ip_porta_saida, minha_pos, jogadores)
        return 0
    elif tipo[0] == tipo_bastao[0]:
        tipo_prox = bastao_recebendo(meu_socket, mensagem, jogada, meu_baralho, ip_porta_saida, minha_pos, bastao)
        return tipo_prox
    elif tipo[0] == tipo_jogar[0]:
        jogar_recebendo(meu_socket, mensagem, jogada, meu_baralho, monte_descarte, ip_porta_saida, tem_cartas)
    elif tipo[0] == tipo_escolha[0]:
        escolha_recebendo(meu_socket, mensagem, ip_porta_saida)
    elif tipo[0] == tipo_passar[0]:
        passar_recebendo(meu_socket, mensagem, jogada, meu_baralho, monte_descarte, ip_porta_saida, minha_pos, tem_cartas)
    elif tipo[0] == tipo_clear_descarte[0]:
        clear_descarte_recebendo(meu_socket, mensagem, monte_descarte, ip_porta_saida)
    elif tipo[0] == tipo_acabou_baralho[0]:
        acabou_baralho_recebendo(meu_socket, mensagem, jogada, nova_ordem, ip_porta_saida)
    elif tipo[0] == tipo_fim_baralho[0]:
        fim_baralho_recebendo(meu_socket, mensagem, lista_jogadores, nova_ordem, ip_porta_saida, jogadores)


#Funcao que envia a mensagem no anel e aguarda seu retorno
def espera_mensagem(meu_socket: socket.socket, meu_ip:bytearray, mensagem:bytearray, tipo_atual: bytearray, ip_porta_saida:tuple, 
                    jogadores:int, minha_pos:int, timeout=3.0):
    #timeout para esperar a mensagem viajar no anel
    meu_socket.settimeout(timeout)
    mensagem_original = mensagem
    while True:

        meu_socket.sendto(mensagem_original, ip_porta_saida)
        try:
            data = meu_socket.recv(9) 
            mensagem = bytearray(data)
            eh_minha, tipo, jogada = decodifica_mensagem(meu_ip, mensagem,  minha_pos)

            if  not (mensagem[7] ^ (2 ** jogadores - 1) == 0 and eh_minha and tipo[0] == tipo_atual[0]):
                raise Exception()
            return jogada
        except KeyboardInterrupt:
            print("Saindo")
            os._exit(os.EX_OK)
        except:
            print(".", end="", flush=True)

# funcao que verifica se todos os computadores estao conectados, uma mensagem simples é enviada,
# se o computador de origem a recebe novamente todos estao conectados
# campo jogada:    
#   *-----------------*
#   | 0 0 0 0 0 0 0 0 |
#   *-----------------*
# O campo jogada tem um byte vazio
def ping(meu_socket: socket.socket, meu_ip:bytearray, ip_porta_saida:tuple, minha_pos:int, jogadores:int):
    recebimento = byte_vazio
    mensagem = inicio + meu_ip + tipo_ping + byte_vazio + recebimento + fim
    print("Iniciando conexao...")
    espera_mensagem(meu_socket, meu_ip, mensagem, tipo_ping, ip_porta_saida, jogadores, minha_pos)
    print("Sucesso, rede conectada")

# funcao que recebe uma carta, e envia uma mensagem que contem qual carta e para qual player e
# campo jogada:    
#   *-----------------*
#   | 0 0|0 0 0 0|0 0 |
#   *-----------------*
#   zeros| carta | posicao do player que recebera a carta
def carteado(meu_socket: socket.socket, meu_ip: bytearray, meu_baralho: list[int], ip_porta_saida:tuple, 
             carta:int, pos_player:int, minha_pos:int, jogadores:int):
    jogada = bytearray(byte_vazio)
    
    #colocando a carta na jogada
    jogada[0] |= carta
    
    #colocando a carta na posicao correta
    jogada[0] <<= 2

    #colocando a posicao do player
    jogada[0] |= pos_player

    #criando a mensagem
    mensagem = inicio + meu_ip + tipo_carteado + jogada + byte_vazio + fim
    
    espera_mensagem(meu_socket, meu_ip, mensagem, tipo_carteado, ip_porta_saida, jogadores, minha_pos)
    
    #Verificando se a carta é para o jogador que chamou a funcao
    jogador = pegar_jogador(jogada)
    if jogador == minha_pos:
        meu_baralho.append(jogada[0] >> 2)
    
# funcao que passa o bastao para o proximo jogador
# campo jogada:    
#   *------------------------------------------------------------------*
#   | 0        0        0   |    0        0        0    |   0        0 |
#   *------------------------------------------------------------------*
#          zeros            |   proximo tipo de jogada  | posicao do player que recebera o bastao
def passa_bastao(meu_socket: socket.socket, meu_ip:bytearray, prox_tipo:bytearray, ip_porta_saida:tuple, prox_player:int, 
                 jogadores:int, minha_pos:int, bastao:list):

    jogada = bytearray(byte_vazio)
    # Retirando bastao do jogador atual
    bastao[0] = False
    # colocando proximo tipo no campo jogada
    jogada[0] |= prox_tipo[0]
    jogada[0] <<= 2

    # colocando proximo jogador
    jogada[0] |= prox_player

    mensagem = inicio + meu_ip + tipo_bastao + jogada + byte_vazio + fim
    espera_mensagem(meu_socket, meu_ip, mensagem, tipo_bastao, ip_porta_saida, jogadores, minha_pos)
    
# Funcao que cria e envia uma mensagem no anel que representa a jogada do jogador atual
# campo jogada:    
#   *-------------------------------*
#   | 0   0   0   0 | 0   0   0   0 |
#   *-------------------------------*
#  carta descartada | Quantidade de carta descartada
def jogar(meu_socket:socket.socket, meu_ip:bytearray, meu_baralho: list, monte_descarte:list,  ip_porta_saida:tuple, minha_pos:int, jogadores:int) -> bytearray:
    # imprimindo situacao atual
    os.system('clear')
    imprime_baralho(monte_descarte, "Monte descarte:")
    imprime_baralho(meu_baralho, "Suas cartas:")

    
    

    so_coringa = True
    monte_descarte_tam = len(monte_descarte)
    if monte_descarte_tam > 0:
        ultima_carta = monte_descarte[monte_descarte_tam - 1]
        quantidade_ultima_carta = monte_descarte.count(ultima_carta)
        for i in range(ultima_carta - 1):
            if meu_baralho.count(i + 1)  >= quantidade_ultima_carta:
                so_coringa = False
    else:
        so_coringa = False
    if so_coringa:
        print("O seu coringa sera jogado nessa jogada")

    coringas = meu_baralho.count(13)
    quantos_coringas_jogados = 0
    if coringas > 0 and not so_coringa:
        escolher_jogar = True
        while escolher_jogar:
            try:
                res = input("Voce deseja jogar seus coringas?(s/n)\n").strip()
                if res == "s":
                    jogar_coringas = True
                    escolher_jogar2 = True
                    quantos_coringas_jogados = 1
                    if coringas > 1:
                        while escolher_jogar2:
                            try:
                                res2 = input("Quantos?(1/2)\n").strip()
                                if res2 == "1":
                                    quantos_coringas_jogados = 1
                                elif res2 == "2":
                                    quantos_coringas_jogados = 2,
                                else:
                                    raise Exception()
                            except KeyboardInterrupt:
                                print("Saindo")
                                os._exit(os.EX_OK)
                            except:
                                print("Entrada invalida, insira novamente")
                            else:
                                escolher_jogar2 = False
                elif res == "n":
                    jogar_coringas = False
                else: 
                    raise Exception()
            except:
                print("Entrada invalida, insira novamente")
            else:
                escolher_jogar = False

            
    # coletando jogada do jogador
    flag = True
    while flag:
        try:
            carta, quantidade = input("Escolha as cartas para descartar no formato: <carta> <quantidade>\n").split()
        except KeyboardInterrupt:
            print("Saindo")
            os._exit(os.EX_OK)
        except:
            print("Entrada invalida tente novamente.")
        else:
            flag = False

    # verificando se a carta informada existe na minha mao
    tem_quantos = meu_baralho.count(int(carta))

    # coletando a ultima jogada
    monte_descarte_tam = len(monte_descarte)
    if monte_descarte_tam > 0:
        ultima_carta = monte_descarte[monte_descarte_tam - 1]
        n = monte_descarte.count(ultima_carta)
        if monte_descarte_tam - n - 1 >= 0 and monte_descarte[monte_descarte_tam - n - 1] == 13:
            n+=1
        if monte_descarte_tam - n - 2 >= 0 and monte_descarte[monte_descarte_tam - n - 1] == 13 and monte_descarte[monte_descarte_tam - n - 2] == 13:
            n+=1


    if so_coringa:
        if coringas == 1:
            quantos_coringas_jogados = 1
        elif coringas == 2:
            if tem_quantos + 2 == n:
                quantos_coringas_jogados = 2

    flag = True
    while flag:      
        if tem_quantos == 0:
            carta, quantidade = input("Seu baralho nao possui esta carta, insira os valores novamente\n").split()
        elif monte_descarte_tam > 0 and int(carta) >= ultima_carta:
            carta, quantidade = input("Voce so pode jogar cartas com rank superior as anteriores (%d), insira uma carta valida\n" % ultima_carta).split()
        elif monte_descarte_tam > 0 and (int(quantidade) + quantos_coringas_jogados) != n:
            carta, quantidade = input("Voce so pode jogar a mesma quantidade de cartas(%d) que a jogada anterior, insira uma quantidade valida\n" % n).split()
        elif tem_quantos + quantos_coringas_jogados < int(quantidade):
            carta, quantidade = input("Voce possui apenas %d da carta %s, insira uma quantia valida\n" % (tem_quantos, carta) ).split()

        # e uma jogada valida
        else:
            flag = False
            # removendo a quantidade da carta informado da mao do jogador
            for i in range(quantos_coringas_jogados):
                meu_baralho.remove(13)
                monte_descarte.append(13)
            for i in range(int(quantidade)):
                meu_baralho.remove(int(carta))
                monte_descarte.append(int(carta))
        tem_quantos = meu_baralho.count(int(carta))
    #imprimindo a mao do jogador apos a remocao
    imprime_baralho(meu_baralho, "Suas cartas:")
    

    if quantos_coringas_jogados > 0:
        jogada = bytearray(byte_vazio)
        jogada[0] |= 13
        jogada[0] <<= 4
        jogada[0] |= quantos_coringas_jogados
        mensagem = inicio + meu_ip + tipo_jogar + jogada + byte_vazio + fim
        espera_mensagem(meu_socket, meu_ip, mensagem, tipo_jogar, ip_porta_saida, jogadores, minha_pos)


    #colocando a carta no campo jogada
    jogada = bytearray(byte_vazio)
    jogada[0] |= int(carta)
    jogada[0] <<= 4
    
    #colocando a quantidade no campo jogada
    jogada[0] |= int(quantidade)
    
    mensagem = inicio + meu_ip + tipo_jogar + jogada + byte_vazio + fim
    espera_mensagem(meu_socket, meu_ip, mensagem, tipo_jogar, ip_porta_saida, jogadores, minha_pos)
    
    # verificando fim do jogo
    if len(monte_descarte) == 80:
        tipo_prox = tipo_fim_baralho
    else:
        tipo_prox = tipo_escolha

    imprime_espere_sua_vez(meu_baralho, monte_descarte)
    
    return tipo_prox

# Funcao que le a escolha do jogador
def get_escolha(meu_baralho:list, monte_descarte:list) -> bytearray:
    #imprimindo estado atual do jogo
    os.system('clear')
    imprime_baralho(monte_descarte, "Monte descarte:")
    imprime_baralho(meu_baralho, "Suas cartas:")
    flag = False

    # verifica se existem jogadas possiveis, caso nao passa automaticamente a vez
    monte_descarte_tam = len(monte_descarte)
    if monte_descarte_tam > 0:
        coringas = meu_baralho.count(13)
        ultima_carta = monte_descarte[monte_descarte_tam - 1]
        quantidade_ultima_carta = monte_descarte.count(ultima_carta)
        if monte_descarte_tam - quantidade_ultima_carta - 1 >= 0 and monte_descarte[monte_descarte_tam - quantidade_ultima_carta - 1] == 13:
            quantidade_ultima_carta+=1
        if monte_descarte_tam - quantidade_ultima_carta - 2 >= 0 and monte_descarte[monte_descarte_tam - quantidade_ultima_carta - 1] == 13 and monte_descarte[monte_descarte_tam - quantidade_ultima_carta - 2] == 13:
            quantidade_ultima_carta+=1

        for i in range(ultima_carta - 1):
            if meu_baralho.count(i + 1) + coringas >= quantidade_ultima_carta:
                if (i + 1) == 13:
                    if meu_baralho.count(i + 1) >= quantidade_ultima_carta:
                        flag = True    
                else:
                    flag = True
        if not flag:
            os.system('clear')
            print("Nao ha jogadas possiveis passando a vez...\n")
            imprime_baralho(monte_descarte, "Monte descarte:")
            imprime_baralho(meu_baralho, "Suas cartas:")
            sleep(1.5)
            imprime_espere_sua_vez(meu_baralho, monte_descarte)
            tipo_prox = tipo_passar
    else:
        flag = True

    # coleta a opcao que o jogador escolher
    while flag:
        flag2 = True
        while flag2:
            try:
                escolha = int(input("Escolha o que deseja fazer:\n1.Jogar\n2.Passar\n"))
            except KeyboardInterrupt:
                print("Saindo")
                os._exit(os.EX_OK)
            except:
                print("Entrada invalida tente novamente")
            else:
                flag2 = False
            
        if escolha == 1:
            tipo_prox = tipo_jogar
            flag = False
        elif escolha == 2:
            tipo_prox = tipo_passar
            flag = False
        else:
            print("Escolha invalida: tente novamente")

    return tipo_prox


# funcao que cria uma mensagem do tipo escolha e a envia no anel, retorna o tipo escolhido pelo usuario.
# campo jogada:    
#   *-----------------*
#   | 0 0 0 0 0 0 0 0 |
#   *-----------------*
# O campo jogada tem um byte vazio
def escolha(meu_socket:socket.socket, meu_ip:bytearray, meu_baralho:list, monte_descarte:list,  ip_porta_saida:tuple, minha_pos:int, jogadores:int) -> bytearray:
    jogada = byte_vazio

    # coletando escolha do jogador
    tipo_prox = get_escolha(meu_baralho, monte_descarte)
    
    mensagem = inicio + meu_ip + tipo_escolha + jogada + byte_vazio + fim
    espera_mensagem(meu_socket, meu_ip, mensagem, tipo_escolha, ip_porta_saida, jogadores, minha_pos)
    
    return tipo_prox

# funcao que cria uma mensagem do tipo passar e a envia no anel, retorna o proximo tipo
# campo jogada:    
#   *-----------------*
#   | 0 0 0 0 0 0|0 0 |
#   *-----------------*
#                | player que ira jogar (retorna vazio caso todo mundo passe)
def passar(meu_socket:socket.socket, meu_ip:bytearray, ip_porta_saida:tuple, minha_pos:int, jogadores:int, prox_player:list) -> bytearray:
    mensagem = inicio + meu_ip + tipo_passar + byte_vazio + byte_vazio + fim
    jogada = espera_mensagem(meu_socket, meu_ip, mensagem, tipo_passar, ip_porta_saida, jogadores, minha_pos, timeout=90)
    
    #caso alguem tenha escolhido jogar
    if jogada[0] != 0:
        jogada[0]&=int('00000011', 2)
        prox_player.append(jogada[0])
        tipo_prox = tipo_jogar
    # todos passaram
    else:
        tipo_prox = tipo_clear_descarte
        prox_player.append(minha_pos)

    return tipo_prox

# funcao que cria uma mensagem que indica que acabou a mao do jogador, e a envia no anel
# campo jogada:    
#   *-----------------*
#   | 0 0 0 0 0 0|0 0 |
#   *-----------------*
#                | posicao do player que acabou a mao
def acabou_baralho(meu_socket:socket.socket, meu_ip:bytearray, ip_porta_saida:tuple, jogadores:int, minha_pos:int):
    # colocando a posicao do player na jogada
    jogada = bytearray(byte_vazio)
    jogada[0]|= minha_pos
    
    mensagem = inicio + meu_ip + tipo_acabou_baralho + jogada + byte_vazio + fim
    espera_mensagem(meu_socket, meu_ip, mensagem, tipo_acabou_baralho, ip_porta_saida, jogadores, minha_pos)

# funcao que cria uma mensagem indicando que todos as maos acabaram, e a envia no anel
# campo jogada:    
#   *-----------------*
#   | 0 0 0 0 0 0 0 0 |
#   *-----------------*
# O campo jogada tem um byte vazio
def fim_baralho(meu_socket:socket.socket, meu_ip:bytearray, nova_lista:list, ip_porta_saida:tuple,  minha_pos:int, jogadores:int):
    mensagem = inicio + meu_ip + tipo_fim_baralho + byte_vazio + byte_vazio + fim
    
    #gravando no diretorio do script o novo arquivo de configuracao
    gravar_cfg(nova_lista, jogadores)

    espera_mensagem(meu_socket, meu_ip, mensagem, tipo_fim_baralho, ip_porta_saida, jogadores, minha_pos, timeout=10)

# funcao que cria uma mensagem que limpa o monte de descarte, e a envia no anel
# campo jogada:    
#   *-----------------*
#   | 0 0 0 0 0 0 0 0 |
#   *-----------------*
# O campo jogada tem um byte vazio
def clear_descarte(meu_socket:socket.socket, meu_ip:bytearray, monte_descarte:list, ip_porta_saida:tuple, minha_pos:int, jogadores:int):
    # Limpando o monte de descarte
    monte_descarte.clear()
    mensagem = inicio + meu_ip + tipo_clear_descarte + byte_vazio + byte_vazio + fim 
    espera_mensagem(meu_socket, meu_ip, mensagem, tipo_clear_descarte, ip_porta_saida, jogadores, minha_pos)

# funcao que trata de quando uma mensagem de carteado e recebida
def carteado_recebendo(meu_socket:socket.socket, mensagem: bytearray, jogada:bytearray, meu_baralho:list, ip_porta_saida:tuple, minha_pos:int, jogadores:int):
    # extraindo a carta do campo jogada
    carta = jogada[0] >> 2
    # extraindo o jogador do campo jogada
    jogador = pegar_jogador(jogada)
    
    # Caso a carta seja para o jogador o atual
    if jogador == minha_pos: 
        meu_baralho.append(carta)
        meu_baralho.sort()
    
    # caso a mao do jogador esteja completa, imprime ela
    if len(meu_baralho) == 80/jogadores:
        imprime_espere_sua_vez(meu_baralho, list())
    meu_socket.sendto(mensagem, ip_porta_saida)

# funcao que trata quando uma mensagem de tipo bastao e recebida
def bastao_recebendo(meu_socket:socket.socket, mensagem:bytearray, jogada:bytearray, meu_baralho:list, ip_porta_saida:tuple, minha_pos:int, bastao:list) -> bytearray:
    # extraindo jogador da jogada
    jogador = pegar_jogador(jogada)
    #extraido o proximo tipo da jogada
    tipo_prox = bytearray([jogada[0] >> 2])

    # caso o bastao seja para o jogador do atual
    if jogador == minha_pos:
        bastao[0] = True
        imprime_baralho(meu_baralho, "Suas cartas:")
    
    meu_socket.sendto(mensagem, ip_porta_saida)
    
    return tipo_prox

# funcao que trata quando uma mensagem de tipo jogar e recebida
def jogar_recebendo(meu_socket:socket.socket, mensagem:bytearray, jogada:bytearray, meu_baralho:list, monte_descarte:list, ip_porta_saida:tuple, tem_cartas:bool):
    # extraindo carta da jogada
    carta = jogada[0] >> 4

    # extraindo quantidade de cartas
    pegar_quantidade = bytearray([int('00001111', 2)])
    quantidade = jogada[0] & pegar_quantidade[0]
    
    # colocando cartas descartadas no monte de descarte
    for i in range(int(quantidade)):
        monte_descarte.append(int(carta))

    meu_socket.sendto(mensagem, ip_porta_saida)
    
    # caso ainda tenha cartas imprime para o jogador
    if tem_cartas:
        imprime_espere_sua_vez(meu_baralho, monte_descarte)

# funcao que trata quando uma mensagem de tipo escolha e recebida
def escolha_recebendo(meu_socket:socket.socket, mensagem:bytearray, ip_porta_saida:tuple):
    meu_socket.sendto(mensagem, ip_porta_saida)

# funcao que trata quando uma mensagem de tipo passar e recebida
def passar_recebendo(meu_socket:socket.socket, mensagem:bytearray, jogada:bytearray, meu_baralho:list, 
                     monte_descarte:list, ip_porta_saida:tuple, minha_pos:int, tem_cartas:bool):
    # neste caso nehum jogador anterior escolheu jogar
    if jogada[0] == 0:
        if tem_cartas:
            # Pega escolha do jogador atual
            tipo_prox = get_escolha(meu_baralho, monte_descarte)
        else:
            tipo_prox = tipo_passar
        # gravando a posicao do jogador atual, caso tenha escolhido jogar
        if tipo_prox[0] == tipo_jogar[0]:
            mensagem[6]|=minha_pos
            mensagem[6]|=int('10000000', 2) 

    meu_socket.sendto(mensagem, ip_porta_saida)

# funcao que trata quando uma mensagem de tipo clear_descarte e recebida
def clear_descarte_recebendo(meu_socket:socket.socket, mensagem:bytearray, monte_descarte:list, ip_porta_saida:tuple):
    # limpando o monte de descarte
    monte_descarte.clear()
    meu_socket.sendto(mensagem, ip_porta_saida)

# funcao que trata quando uma mensagem de tipo acabou_baralho e recebida
def acabou_baralho_recebendo(meu_socket:socket.socket, mensagem:bytearray, jogada:bytearray, nova_ordem:list[int],  ip_porta_saida:tuple):
    # adicionando o jogador que acabou a mao na lista com a nova ordem
    nova_ordem.append(jogada[0])
    meu_socket.sendto(mensagem, ip_porta_saida)

# funcao que trata quando uma mensagem de tipo fim_baralho e recebida
def fim_baralho_recebendo(meu_socket:socket.socket, mensagem:bytearray, lista_jogadores:list, nova_ordem:list[int], ip_porta_saida:tuple, jogadores:int):
    # gerando e gravando a nova configuracao
    nova_lista = gerar_cfg(lista_jogadores, nova_ordem, jogadores)
    gravar_cfg(nova_lista, jogadores)
    
    meu_socket.sendto(mensagem, ip_porta_saida)
    
    print("Fim de jogo, novo setup salvo em cfg.txt\nTerminando execucao.")
    sleep(1.5)
    exit()