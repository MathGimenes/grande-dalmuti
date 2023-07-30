import socket, os
from itertools import cycle
from time import sleep

# meus modulos
import init
import rede_anel

def main():
    meu_ip = init.get_local_ip()
    lista_jogadores , jogadores, bastao_lido = init.ler_cfg()
    bastao =[False]
    minha_pos, minha_porta, ip_porta_saida, bastao[0]= init.get_ip_porta(meu_ip, lista_jogadores, jogadores, bastao_lido)
    # criando socket
    meu_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    meu_socket.bind((meu_ip, minha_porta))

    meu_ip = rede_anel.codifica_ip(meu_ip)

    primeira_jogada = [True]

    monte_descarte = []
    meu_baralho = []
    nova_ordem = []

    print("Iniciando jogo...")

    #jogador com o bastao fazendo o setup do jogo
    if bastao[0] and primeira_jogada:
        # verificaando se todos estao conectados
        rede_anel.ping(meu_socket, meu_ip, ip_porta_saida, minha_pos, jogadores)
        
        #gerando baralho
        baralho = rede_anel.gera_baralho()
        
        # lista circular representando os jogadores
        players = cycle(range(jogadores))
        for player in players:
            if player == minha_pos:
                break
        # distribuindo cartas
        for carta in baralho:
            rede_anel.carteado(meu_socket, meu_ip, meu_baralho, ip_porta_saida, carta, next(players), minha_pos, jogadores)
        
        # ordenando o baralho para uma melhor visualizacao
        meu_baralho.sort()
        
        
        rede_anel.imprime_espere_sua_vez(meu_baralho, list())

        rede_anel.passa_bastao(meu_socket, meu_ip, rede_anel.tipo_jogar, ip_porta_saida, rede_anel.get_prox_jogador(minha_pos, jogadores),  jogadores, minha_pos, bastao)
        
        # volta o comportamento padrao do socket
        meu_socket.setblocking(True)

    # laco principal do programa
    flag = True
    while flag:
        # verificando se o jogador tem o bastao
        if bastao[0] and nova_ordem.count(minha_pos) == 0:
            # Jogar
            if(tipo_prox[0] == rede_anel.tipo_jogar[0]):
                tipo_prox = rede_anel.jogar(meu_socket, meu_ip, meu_baralho, monte_descarte, ip_porta_saida, minha_pos, jogadores)
                
                # caso a mao do jogador tenha acabado
                if(rede_anel.baralho_vazio(meu_baralho)):
                    tipo_prox = rede_anel.tipo_acabou_baralho
                else:
                    rede_anel.passa_bastao(meu_socket, meu_ip, tipo_prox, ip_porta_saida, rede_anel.get_prox_jogador(minha_pos, jogadores, nova_ordem) ,  jogadores, minha_pos, bastao)
            # Escolha
            elif(tipo_prox[0] == rede_anel.tipo_escolha[0]):
                tipo_prox = rede_anel.escolha(meu_socket, meu_ip, meu_baralho, monte_descarte, ip_porta_saida, minha_pos, jogadores)
            # Passar
            elif(tipo_prox[0] == rede_anel.tipo_passar[0]):
                prox_player = []
                rede_anel.imprime_espere_sua_vez(meu_baralho, monte_descarte)
                tipo_prox = rede_anel.passar(meu_socket, meu_ip, ip_porta_saida, minha_pos, jogadores, prox_player)
                
                # Todos passaram, pegando o jogador anterior
                if prox_player[0] == minha_pos:
                    prox_player[0] = rede_anel.get_prox_jogador(minha_pos, jogadores, nova_ordem, reverso=True)
                # Todos passaram, limpando monte descarte
                if tipo_prox[0] == rede_anel.tipo_clear_descarte[0]:
                    rede_anel.clear_descarte(meu_socket, meu_ip, monte_descarte, ip_porta_saida, minha_pos, jogadores)
                # passando bastao para o proximo player
                rede_anel.passa_bastao(meu_socket, meu_ip, rede_anel.tipo_jogar, ip_porta_saida, prox_player[0],  jogadores, minha_pos, bastao)
            
            # Descartou toda mao
            elif(tipo_prox[0] == rede_anel.tipo_acabou_baralho[0]):
                rede_anel.acabou_baralho(meu_socket, meu_ip, ip_porta_saida, jogadores, minha_pos)
                player_temp = rede_anel.get_prox_jogador(minha_pos, jogadores, nova_ordem)

                # adicionando a lista de pessoas que descartaeam toda a mao
                nova_ordem.append(minha_pos)

                # caso ainda exista jogadores com cartas na mao
                if len(nova_ordem) < jogadores - 1:
                    rede_anel.passa_bastao(meu_socket, meu_ip, rede_anel.tipo_escolha, ip_porta_saida, player_temp,
                                            jogadores, minha_pos, bastao)
                # todo mundo descartou a mao
                else:
                    rede_anel.passa_bastao(meu_socket, meu_ip, rede_anel.tipo_fim_baralho, ip_porta_saida, player_temp,
                                            jogadores, minha_pos, bastao)
                os.system('clear')
                print("Acabou seu baralho, voce ficou em %d lugar, esperando os outros jogadores..." % len(nova_ordem))
            # Todos descartaram suas maos
            elif(tipo_prox[0] == rede_anel.tipo_fim_baralho[0]):
                nova_lista = rede_anel.gerar_cfg(lista_jogadores, nova_ordem, jogadores)
                rede_anel.fim_baralho(meu_socket, meu_ip, nova_lista, ip_porta_saida, minha_pos, jogadores)
                print("Acabou seu baralho, voce ficou em %d lugar." % len(nova_ordem))
                flag = False
            else:
                raise Exception()
            
            #voltando ao modo de operacao padrao dos sockets
            meu_socket.setblocking(True)

        # Socket fica escutando novas mensagens
        else:
            data = meu_socket.recv(9)
            # transformando mensagem recebida em bytearray para poder altera-la
            mensagem = bytearray(data)
            # decodificando mensagem
            eh_minha, tipo, jogada = rede_anel.decodifica_mensagem(meu_ip, mensagem, minha_pos)
            # fazendo o tratamento da mensagem
            tipo_prox = rede_anel.mensagem_handler(meu_socket, mensagem, tipo, jogada, lista_jogadores, monte_descarte,
                                                meu_baralho, nova_ordem, ip_porta_saida, minha_pos, bastao, jogadores)

    print("Fim de jogo, novo setup salvo em cfg.txt\nTerminando execucao.")
    sleep(1.5)


if __name__ == '__main__':
    main()