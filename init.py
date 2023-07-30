import socket

# retorna o ip da maquina em que esta sendo executando o game
def get_local_ip():
    meu_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        meu_socket.connect(('192.255.255.255', 1))
        IP = meu_socket.getsockname()[0]
    except:
        IP = '127.0.0.1'
    return IP
 
# funcao que le o arquivo de configuracao, e retorna
# a lista de jogadores, o numero de jogadores, e a posicao inicial do bastao lido
def ler_cfg():
    lista_jogadores = []
    with open('cfg.txt') as cfg:
        jogadores_bastao = cfg.readline().strip().split(";")
        jogadores = int(jogadores_bastao[0])
        bastao_lido = int(jogadores_bastao[1])
        for linha in cfg:
            jogador_temp = linha.strip().split(";")
            jogador = int(jogador_temp[0])
            ip = jogador_temp[1]
            porta = int(jogador_temp[2])
            lista_jogadores.append((jogador, ip, porta))
            
    return (lista_jogadores, jogadores, bastao_lido)

# funcao que recebe o ip do jogador atual, a lista de jogadores, o bastao lido,
# e retorna a posicao do jogador na mesa, a porta do jogador, o ip e a porta que o jogador atual,
# mandara a mensagem, e um bool que que contem True caso o jogador atual comeca com o bastao
def get_ip_porta(meu_ip:int, lista_jogadores:list, jogadores:int, bastao_lido:int):
    n = 1
    bastao = False
    for jogador in lista_jogadores:
        if jogador[1] == meu_ip:
            minha_pos = jogador[0]
            if bastao_lido == jogador[0]:
                bastao = True
            minha_porta = jogador[2]
            if n == jogadores:
                porta_saida = lista_jogadores[0][2]
                ip_saida = lista_jogadores[0][1]
            else:
                porta_saida = lista_jogadores[n][2]
                ip_saida = lista_jogadores[n][1]
        n+=1
    return (minha_pos - 1, minha_porta, (ip_saida, porta_saida), bastao)